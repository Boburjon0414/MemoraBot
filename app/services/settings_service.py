"""Business logic for reading and updating user preferences.

Every public method here takes a Telegram user id, so handlers never need to
reason about internal database primary keys — this service resolves
Telegram id -> internal user internally.
"""

from __future__ import annotations

from app.database.models.user_settings import UserSettings
from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository

_DEFAULT_LANGUAGE = "uz"


class SettingsService:
    """Reads and updates a user's language/notification preferences."""

    def __init__(self, user_repo: UserRepository, settings_repo: UserSettingsRepository) -> None:
        self._user_repo = user_repo
        self._settings_repo = settings_repo

    async def get_settings(self, telegram_id: int) -> UserSettings | None:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        return await self._settings_repo.get_by_user_id(user.id)

    async def get_language(self, telegram_id: int) -> str:
        """Return the user's preferred UI language, defaulting to Uzbek.

        Safe to call for unregistered users too (e.g. before /start finishes),
        in which case it simply returns the default language.
        """
        settings_row = await self.get_settings(telegram_id)
        return settings_row.preferred_language if settings_row else _DEFAULT_LANGUAGE

    async def set_language(self, telegram_id: int, language: str) -> UserSettings | None:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        return await self._settings_repo.update_language(user.id, language)

    async def toggle_notifications(self, telegram_id: int) -> UserSettings | None:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        return await self._settings_repo.toggle_notifications(user.id)
