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
