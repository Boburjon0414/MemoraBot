"""Business logic for user registration and lookup."""

from __future__ import annotations

import logging

from app.database.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository

logger = logging.getLogger(__name__)


class UserService:
    """Registers new users and answers "is this Telegram user registered?" queries."""

    def __init__(self, user_repo: UserRepository, settings_repo: UserSettingsRepository) -> None:
        self._user_repo = user_repo
        self._settings_repo = settings_repo

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self._user_repo.get_by_telegram_id(telegram_id)

    async def is_registered(self, telegram_id: int) -> bool:
        return (await self.get_by_telegram_id(telegram_id)) is not None

    async def register_user(
        self,
        *,
        telegram_id: int,
        full_name: str,
        phone_number: str,
        username: str | None,
    ) -> User:
        """Register a new user and create their default settings row.

        Idempotent: if the Telegram user is already registered, the existing
        `User` is returned unchanged instead of raising or duplicating rows.
        """
        existing = await self._user_repo.get_by_telegram_id(telegram_id)
        if existing is not None:
            return existing

        user = await self._user_repo.create(
            telegram_id=telegram_id,
            full_name=full_name,
            phone_number=phone_number,
            username=username,
        )
        await self._settings_repo.create_default(user.id)
        logger.info("Registered new user telegram_id=%s", telegram_id)
        return user
