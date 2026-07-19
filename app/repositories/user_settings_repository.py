"""Data-access layer for the `UserSettings` entity."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database.models.user_settings import UserSettings
from app.repositories.base import BaseRepository

_DAILY_RESET_WINDOW = timedelta(hours=24)


class UserSettingsRepository(BaseRepository[UserSettings]):
    """Repository for reading and updating a user's preferences.

    All methods here key off the internal `user_id` (the `users.id` FK), not
    the Telegram id — resolving Telegram id -> internal user is the
    responsibility of the service layer (see `SettingsService`), keeping this
    repository focused purely on the `user_settings` table itself.
    """

    model = UserSettings

    async def get_by_user_id(self, user_id: int) -> UserSettings | None:
        result = await self._session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_default(self, user_id: int) -> UserSettings:
        """Create a settings row with defaults (uz, notifications on) for a new user.

        `last_daily_reset` is seeded to the current UTC time so the user's
        first 24-hour quota window begins at registration, not at epoch 0.
        """
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC, matches DB storage
        settings_row = UserSettings(user_id=user_id, last_daily_reset=now_utc)
        return await self.add(settings_row)

    async def update_language(self, user_id: int, language: str) -> UserSettings | None:
        settings_row = await self.get_by_user_id(user_id)
        if settings_row is None:
            return None
        settings_row.preferred_language = language
        await self._session.flush()
        await self._session.refresh(settings_row)
        return settings_row

    async def toggle_notifications(self, user_id: int) -> UserSettings | None:
        settings_row = await self.get_by_user_id(user_id)
        if settings_row is None:
            return None
        settings_row.notifications_enabled = not settings_row.notifications_enabled
        await self._session.flush()
        await self._session.refresh(settings_row)
        return settings_row

    async def reset_daily_quota_if_needed(self, user_id: int) -> UserSettings | None:
        """Reset `daily_generation_count` to 0 and stamp `last_daily_reset` to
        the current UTC time if 24 hours have passed since the last reset.

        This is called at the start of every quota check so the daily window
        resets automatically during normal user requests — no cron job needed.

        The comparison is done entirely in naive UTC (as stored in SQLite's
        DateTime column) to avoid aware/naive mixing errors.

        Returns the (potentially updated) settings row, or None if the user
        has no settings row yet.
        """
        settings_row = await self.get_by_user_id(user_id)
        if settings_row is None:
            return None

        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC

        # Treat NULL last_daily_reset as epoch 0 — always triggers a reset,
        # which seeds the column for users created before V1.3.
        last_reset = settings_row.last_daily_reset or datetime.min

        if now_utc - last_reset >= _DAILY_RESET_WINDOW:
            settings_row.daily_generation_count = 0
            settings_row.last_daily_reset = now_utc
            await self._session.flush()
            await self._session.refresh(settings_row)

        return settings_row

    async def increment_generation_count(self, user_id: int) -> UserSettings | None:
        """Increment both `daily_generation_count` and the legacy `ai_generations_used`
        by 1. Called only when a genuinely new AI generation happens (a cache miss).

        `daily_generation_count` drives the 24-hour quota enforced by `UsageService`.
        `ai_generations_used` is retained as a lifetime audit counter.
        """
        settings_row = await self.get_by_user_id(user_id)
        if settings_row is None:
            return None
        settings_row.daily_generation_count += 1
        settings_row.ai_generations_used += 1  # legacy lifetime counter — keep in sync
        await self._session.flush()
        await self._session.refresh(settings_row)
        return settings_row
