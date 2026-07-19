"""Business logic for the free-plan daily AI generation quota.

Cached words are always free and never touch this — see
`MnemonicService.would_require_generation`. This only tracks genuinely new
words that require a fresh AI call.

Daily reset (V1.3):
- Free users receive `daily_limit` new AI generations every 24 hours.
- The 24-hour window is evaluated lazily on every request: if 24 hours
  have elapsed since the stored `last_daily_reset`, the counter is reset
  to 0 before the quota check. No cron job is required.
- Premium users bypass the daily quota entirely.
- Coins, referrals, and premium status are never touched here.
"""

from __future__ import annotations

import logging

from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository

logger = logging.getLogger(__name__)


class UsageService:
    """Tracks and enforces the free-plan daily AI-generation limit, keyed by Telegram id.

    Constructor args:
        user_repo: repository for resolving Telegram id -> internal User.
        settings_repo: repository for `user_settings` reads/writes.
        daily_limit: maximum new AI generations allowed per 24-hour window
                     for free users (comes from `Settings.free_plan_daily_generations`).
    """

    def __init__(
        self,
        user_repo: UserRepository,
        settings_repo: UserSettingsRepository,
        daily_limit: int,
    ) -> None:
        self._user_repo = user_repo
        self._settings_repo = settings_repo
        self._daily_limit = daily_limit

    @property
    def limit(self) -> int:
        """The configured free-plan daily generation limit (for display purposes)."""
        return self._daily_limit

    async def has_quota_remaining(self, telegram_id: int) -> bool:
        """True if this user may trigger a fresh AI generation right now.

        For premium users this always returns True.
        For free users, the 24-hour window is automatically reset here if
        it has expired before the count is evaluated — so the first call
        after midnight (UTC-relative) transparently starts a fresh window.
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            # Unknown user: block by default (safe fallback).
            return False

        # Reset window first so an expired window is never counted against.
        settings_row = await self._settings_repo.reset_daily_quota_if_needed(user.id)
        if settings_row is None:
            return False

        if settings_row.is_premium:
            return True

        remaining = self._daily_limit - settings_row.daily_generation_count
        logger.debug(
            "Quota check telegram_id=%s: daily_count=%d limit=%d remaining=%d",
            telegram_id,
            settings_row.daily_generation_count,
            self._daily_limit,
            max(0, remaining),
        )
        return remaining > 0

    async def remaining(self, telegram_id: int) -> int:
        """How many fresh generations this user has left today (never negative).

        Returns `daily_limit` for premium users (effectively unlimited display).
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return 0

        settings_row = await self._settings_repo.reset_daily_quota_if_needed(user.id)
        if settings_row is None:
            return 0

        if settings_row.is_premium:
            return self._daily_limit  # display value only; not a real cap

        return max(0, self._daily_limit - settings_row.daily_generation_count)

    async def record_generation(self, telegram_id: int) -> None:
        """Count one fresh AI generation against this user's daily quota.

        MUST be called ONLY after a successful AI generation (cache miss that
        produced a result) — never for cache hits and never for failed requests.
        Premium users are silently skipped (their quota is unlimited).
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return

        # Read the current settings to check premium status before writing.
        settings_row = await self._settings_repo.get_by_user_id(user.id)
        if settings_row is None:
            return

        if settings_row.is_premium:
            # Premium users have unlimited generations — never count against them.
            return

        await self._settings_repo.increment_generation_count(user.id)
        logger.debug(
            "Recorded generation for telegram_id=%s (new daily_count=%d)",
            telegram_id,
            settings_row.daily_generation_count + 1,
        )
