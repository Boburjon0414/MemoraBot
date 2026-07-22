"""Business logic for the admin broadcast feature.

All delivery work runs inside a background ``asyncio.Task`` so the
Telegram handler returns immediately after the admin confirms.  When the
loop finishes the statistics summary is sent back to the originating
admin's chat as a regular message.

Errors are absorbed per-user: the loop never aborts because one recipient
blocked the bot or was deactivated.

V1.5: `start_broadcast` accepts `lang` so stats are sent in the admin's language.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter

from app.repositories.user_repository import UserRepository
from app.texts.messages import t

logger = logging.getLogger(__name__)

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
    """Orchestrates sending a text message to all registered users."""

    def __init__(self, user_repo: UserRepository, delay_ms: int = 50) -> None:
        self._user_repo = user_repo
        self._delay_ms = delay_ms

    async def start_broadcast(
        self,
        bot: Bot,
        text: str,
        admin_id: int,
        lang: str = "uz",
    ) -> int:
        """Collect all IDs and schedule the delivery loop as a background task.

        Args:
            lang: The admin's UI language — used when sending the stats summary.

        Returns:
            The total number of registered users the broadcast targets.
        """
        telegram_ids = await self._user_repo.get_all_telegram_ids()
        count = len(telegram_ids)
        asyncio.create_task(
            self._run(bot, text, telegram_ids, admin_id, lang),
            name=f"broadcast:{admin_id}",
        )
        logger.info(
            "Broadcast scheduled: admin=%s target_users=%d delay_ms=%d",
            admin_id, count, self._delay_ms,
        )
        return count

    # ── Private helpers ────────────────────────────────────────────────

    async def _run(
        self,
        bot: Bot,
        text: str,
        telegram_ids: list[int],
        admin_id: int,
        lang: str,
    ) -> None:
        """Inner delivery loop — absorbs all per-user errors."""
        total = len(telegram_ids)
        sent = failed = blocked = 0
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
            total=total, sent=sent, failed=failed,
            blocked=blocked, elapsed_seconds=elapsed,
        )
        logger.info(
            "Broadcast finished: sent=%d failed=%d blocked=%d elapsed=%.1fs",
            sent, failed, blocked, elapsed,
        )
        await self._send_stats(bot, admin_id, result, lang)

    async def _send_one(self, bot: Bot, tg_id: int, text: str) -> bool | None:
        try:
            await bot.send_message(tg_id, text)
            return _SENT
        except TelegramForbiddenError:
            logger.debug("Broadcast: blocked by user %s", tg_id)
            return _BLOCKED
        except TelegramRetryAfter as exc:
            logger.warning("Broadcast: flood-wait %ss for user %s — retrying", exc.retry_after, tg_id)
            await asyncio.sleep(float(exc.retry_after))
            try:
                await bot.send_message(tg_id, text)
                return _SENT
            except Exception as retry_exc:
                logger.error("Broadcast: retry failed for user %s: %s", tg_id, retry_exc)
                return _FAILED
        except TelegramAPIError as exc:
            logger.debug("Broadcast: API error for user %s: %s", tg_id, exc)
            return _FAILED
        except Exception as exc:
            logger.error("Broadcast: unexpected error for user %s: %s", tg_id, exc)
            return _FAILED

    async def _send_stats(
        self,
        bot: Bot,
        admin_id: int,
        result: BroadcastResult,
        lang: str = "uz",
    ) -> None:
        """Deliver the completion statistics to the admin in their language."""
        minutes, seconds = divmod(int(result.elapsed_seconds), 60)
        elapsed_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

        stats_text = "\n".join([
            t("admin.broadcast.stats.title", lang),
            "",
            t("admin.broadcast.stats.total",   lang, value=str(result.total)),
            t("admin.broadcast.stats.sent",     lang, value=str(result.sent)),
            t("admin.broadcast.stats.failed",   lang, value=str(result.failed)),
            t("admin.broadcast.stats.blocked",  lang, value=str(result.blocked)),
            t("admin.broadcast.stats.elapsed",  lang, value=elapsed_str),
        ])
        try:
            await bot.send_message(admin_id, stats_text)
        except Exception as exc:
            logger.error("Broadcast: failed to deliver stats to admin %s: %s", admin_id, exc)
