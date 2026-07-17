"""Business logic for the free-plan AI generation quota.

Cached words are always free and never touch this — see
`MnemonicService.would_require_generation`. This only tracks genuinely new
words that require a fresh Gemini call, gated by
`settings.free_plan_generation_limit` (default 3, configurable).

Not yet distinguishing free vs. premium users (Premium is an explicitly
deferred, documented future feature — see docs/ROADMAP.md) — today this
quota applies uniformly. Wiring in a premium bypass later is a one-line
change to `has_quota_remaining`.
"""

from __future__ import annotations

from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository


class UsageService:
    """Tracks and enforces the free-plan AI-generation limit, keyed by Telegram id."""

    def __init__(
        self,
        user_repo: UserRepository,
        settings_repo: UserSettingsRepository,
        generation_limit: int,
    ) -> None:
        self._user_repo = user_repo
        self._settings_repo = settings_repo
        self._generation_limit = generation_limit

    @property
    def limit(self) -> int:
        """The configured free-plan generation limit (for display purposes)."""
        return self._generation_limit

    async def has_quota_remaining(self, telegram_id: int) -> bool:
        """True if this user can still trigger a fresh AI generation."""
        used = await self._get_used(telegram_id)
        return used < self._generation_limit

    async def remaining(self, telegram_id: int) -> int:
        """How many fresh generations this user has left (never negative)."""
        used = await self._get_used(telegram_id)
        return max(0, self._generation_limit - used)

    async def record_generation(self, telegram_id: int) -> None:
        """Count one fresh AI generation against this user's quota.

        Call this ONLY after confirming a generation actually happened (a
        cache miss that succeeded) — never for a cache hit.
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return
        await self._settings_repo.increment_generation_count(user.id)

    async def _get_used(self, telegram_id: int) -> int:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return 0
        settings_row = await self._settings_repo.get_by_user_id(user.id)
        return settings_row.ai_generations_used if settings_row else 0
