"""Data-access layer for the `MnemonicFeedback` entity (Task 5 ratings)."""

from __future__ import annotations

from sqlalchemy import select

from app.database.models.mnemonic_feedback import MnemonicFeedback
from app.repositories.base import BaseRepository


class MnemonicFeedbackRepository(BaseRepository[MnemonicFeedback]):
    """Repository for recording and reading per-user mnemonic ratings."""

    model = MnemonicFeedback

    async def get_by_mnemonic_and_user(
        self, mnemonic_history_id: int, user_id: int
    ) -> MnemonicFeedback | None:
        result = await self._session.execute(
            select(MnemonicFeedback).where(
                MnemonicFeedback.mnemonic_history_id == mnemonic_history_id,
                MnemonicFeedback.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, *, mnemonic_history_id: int, user_id: int, is_helpful: bool
    ) -> MnemonicFeedback:
        """Create a rating, or update it in place if this user already rated this mnemonic.

        This is what keeps the (mnemonic_history_id, user_id) pair unique:
        tapping 👍 then later 👎 flips the existing row rather than adding a
        second one.
        """
        existing = await self.get_by_mnemonic_and_user(mnemonic_history_id, user_id)
        if existing is not None:
            existing.is_helpful = is_helpful
            await self._session.flush()
            await self._session.refresh(existing)
            return existing

        feedback = MnemonicFeedback(
            mnemonic_history_id=mnemonic_history_id,
            user_id=user_id,
            is_helpful=is_helpful,
        )
        return await self.add(feedback)
