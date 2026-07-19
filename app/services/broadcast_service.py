"""Business logic for the admin broadcast feature.

All delivery work runs inside a background ``asyncio.Task`` so the
Telegram handler returns immediately after the admin confirms.  When the
loop finishes the statistics summary is sent back to the originating
admin's chat as a regular message.

Errors are absorbed per-user: the loop never aborts because one recipient
blocked the bot or was deactivated.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter

from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# Sentinel return values from _send_one
_SENT = True
_BLOCKED: bool | None = None
_FAILED = False


@dataclass(frozen=True)
class BroadcastResult:
    """Immutable snapshot of a completed broadcast run."""

    total: int
    sent: int
    failed: int
    blocked: int
    elapsed_seconds: float


class BroadcastService:
    """Orchestrates sending a text message to all registered users.

    Constructor args:
        user_repo:  repository used to collect Telegram IDs (DB session
                    must still be open at call time).
        delay_ms:   inter-message pause in milliseconds (avoids Telegram
                    flood limits).  Comes from ``Settings.broadcast_delay_ms``.
    """

    def __init__(self, user_repo: UserRepository, delay_ms: int = 50) -> None:
        self._user_repo = user_repo
        self._delay_ms = delay_ms

    async def start_broadcast(self, bot: Bot, text: str, admin_id: int) -> int:
        """Collect all IDs and schedule the delivery loop as a background task.

        The DB session is still open when this coroutine runs, so the
        repository query is safe.  The background task only calls the
        Telegram API — it does not touch the DB — so session lifetime is
        not a concern after this method returns.

        Returns:
            The total number of registered users the broadcast targets.
        """
        telegram_ids = await self._user_repo.get_all_telegram_ids()
        count = len(telegram_ids)
        asyncio.create_task(
            self._run(bot, text, telegram_ids, admin_id),
            name=f"broadcast:{admin_id}",
        )
        logger.info(
            "Broadcast scheduled: admin=%s target_users=%d delay_ms=%d",
            admin_id,
            count,
            self._delay_ms,
        )
        return count

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _run(
        self,
        bot: Bot,
        text: str,
        telegram_ids: list[int],
        admin_id: int,
    ) -> None:
        """Inner delivery loop — absorbs all per-user errors."""
        total = len(telegram_ids)
        sent = 0
        failed = 0
        blocked = 0
        start = time.monotonic()

        for tg_id in telegram_ids:
            outcome = await self._send_one(bot, tg_id, text)
            if outcome is _SENT:
                sent += 1
            elif outcome is _BLOCKED:
                blocked += 1
            else:
                failed += 1

            if self._delay_ms > 0:
                await asyncio.sleep(self._delay_ms / 1000.0)

        elapsed = time.monotonic() - start
        result = BroadcastResult(
            total=total,
            sent=sent,
            failed=failed,
            blocked=blocked,
            elapsed_seconds=elapsed,
        )
        logger.info(
            "Broadcast finished: sent=%d failed=%d blocked=%d elapsed=%.1fs",
            sent,
            failed,
            blocked,
            elapsed,
        )
        await self._send_stats(bot, admin_id, result)

    async def _send_one(self, bot: Bot, tg_id: int, text: str) -> bool | None:
        """Attempt to deliver to a single user.

        Returns:
            ``True``  — delivered.
            ``None``  — user blocked the bot (Forbidden / 403).
            ``False`` — any other failure (deactivated, not found, unexpected).
        """
        try:
            await bot.send_message(tg_id, text)
            return _SENT
        except TelegramForbiddenError:
            # 403: user blocked the bot or deactivated account (Forbidden)
            logger.debug("Broadcast: blocked by user %s", tg_id)
            return _BLOCKED
        except TelegramRetryAfter as exc:
            # 429: flood-wait — sleep for the required delay, then retry once.
            logger.warning(
                "Broadcast: flood-wait %ss for user %s — retrying",
                exc.retry_after,
                tg_id,
            )
            await asyncio.sleep(float(exc.retry_after))
            try:
                await bot.send_message(tg_id, text)
                return _SENT
            except Exception as retry_exc:
                logger.error(
                    "Broadcast: retry failed for user %s: %s",
                    tg_id,
                    retry_exc,
                )
                return _FAILED
        except TelegramAPIError as exc:
            # Covers 400 Bad Request (deactivated user, chat not found, etc.)
            # and any other Telegram API-level error.
            logger.debug("Broadcast: API error for user %s: %s", tg_id, exc)
            return _FAILED
        except Exception as exc:
            logger.error(
                "Broadcast: unexpected runtime error for user %s: %s",
                tg_id,
                exc,
            )
            return _FAILED

    async def _send_stats(
        self,
        bot: Bot,
        admin_id: int,
        result: BroadcastResult,
    ) -> None:
        """Deliver the completion statistics to the admin."""
        minutes, seconds = divmod(int(result.elapsed_seconds), 60)
        elapsed_str = f"{minutes}d {seconds}s" if minutes else f"{seconds}s"

        stats_text = (
            "📊 <b>Broadcast yakunlandi!</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{result.total}</b>\n"
            f"✅ Muvaffaqiyatli yuborildi: <b>{result.sent}</b>\n"
            f"❌ Yuborilmadi (xato): <b>{result.failed}</b>\n"
            f"🚫 Bot bloklangan: <b>{result.blocked}</b>\n"
            f"⏱ Umumiy vaqt: <b>{elapsed_str}</b>"
        )
        try:
            await bot.send_message(admin_id, stats_text)
        except Exception as exc:
            logger.error(
                "Broadcast: failed to deliver stats to admin %s: %s",
                admin_id,
                exc,
            )
