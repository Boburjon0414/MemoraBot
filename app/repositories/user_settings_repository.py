"""Data-access layer for the `UserSettings` entity."""

from __future__ import annotations

from sqlalchemy import select

from app.database.models.user_settings import UserSettings
from app.repositories.base import BaseRepository


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
        """Create a settings row with defaults (uz, notifications on) for a new user."""
        settings_row = UserSettings(user_id=user_id)
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

    async def increment_generation_count(self, user_id: int) -> UserSettings | None:
        """Increment `ai_generations_used` by 1 — called only when a genuinely
        new AI generation happens (a cache miss), never for cached words.
        """
        settings_row = await self.get_by_user_id(user_id)
        if settings_row is None:
            return None
        settings_row.ai_generations_used += 1
        await self._session.flush()
        await self._session.refresh(settings_row)
        return settings_row
