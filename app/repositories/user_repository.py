"""Data-access layer for the `User` entity."""

from __future__ import annotations

from sqlalchemy import select

from app.database.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for reading and creating `User` rows."""

    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Fetch a user by their Telegram user id, or None if not registered."""
        result = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Fetch a user by their Telegram username (case-insensitive, without @)."""
        result = await self._session.execute(
            select(User).where(User.username.ilike(username))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Fetch a user by their internal primary-key id."""
        return await self._session.get(User, user_id)

    async def get_all_telegram_ids(self) -> list[int]:
        """Return the Telegram user ID of every registered user.

        Used by ``BroadcastService`` to fan out a message to the full
        user base.  Only the IDs are fetched — not full rows — to keep
        the payload small regardless of table size.
        """
        result = await self._session.execute(select(User.telegram_id))
        return list(result.scalars().all())

    async def create(
        self,
        *,
        telegram_id: int,
        full_name: str,
        phone_number: str,
        username: str | None = None,
    ) -> User:
        """Insert a new user row."""
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            phone_number=phone_number,
            username=username,
        )
        return await self.add(user)
