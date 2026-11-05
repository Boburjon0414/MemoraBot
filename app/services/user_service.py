"""Business logic for user registration and lookup."""

from __future__ import annotations

import logging

from app.database.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository

logger = logging.getLogger(__name__)


class UserService:
    """Registers new users and answers "is this Telegram user registered?" queries."""

    def __init__(
        self,
        user_repo: UserRepository,
        settings_repo: UserSettingsRepository,
        memory_repo=None,  # UserMemoryRepository — injected in Step 8, optional for backward compat
    ) -> None:
        self._user_repo = user_repo
        self._settings_repo = settings_repo
        self._memory_repo = memory_repo  # Step 8

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
        """Register a new user and create their default settings and memory rows.

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

        # Step 8: create blank memory row at registration so every new user
        # has a profile from day one.  If memory_repo is not injected (legacy
        # or test environments), skip silently — get_or_create() handles it.
        if self._memory_repo is not None:
            try:
                await self._memory_repo.create_default(user.id)
            except Exception:
                logger.warning(
                    "UserService.register_user: failed to create memory row for "
                    "user_id=%s — will be created lazily on first access", user.id,
                    exc_info=True,
                )

        logger.info("Registered new user telegram_id=%s", telegram_id)
        return user
