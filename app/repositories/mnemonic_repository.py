"""Data-access layer for the `MnemonicHistory` entity.

V1.2 turns this into a self-improving library's data layer: alongside the
original create/lookup methods, it now tracks usage, keeps denormalized
rating counters in sync, and can retire (never delete) poor versions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select

from app.database.models.mnemonic_history import MnemonicHistory
from app.repositories.base import BaseRepository


class MnemonicRepository(BaseRepository[MnemonicHistory]):
    """Repository for creating, serving, and rating a self-improving mnemonic library."""

    model = MnemonicHistory

    async def create(
        self,
        *,
        user_id: int,
        word: str,
        meaning: str,
        uzbek_pronunciation: str,
        mnemonic_story: str,
        example_sentence: str,
        difficulty: str,
        ai_provider: str,
        prompt_version: str = "v1",
        response_time_ms: int | None = None,
    ) -> MnemonicHistory:
        """Insert a new mnemonic version.

        `uses` starts at 1 and `last_used_at` is set to now — creating a
        version and serving it to its first viewer happen in the same
        moment (see `MnemonicService`).
        """
        entry = MnemonicHistory(
            user_id=user_id,
            word=word,
            meaning=meaning,
            uzbek_pronunciation=uzbek_pronunciation,
            mnemonic_story=mnemonic_story,
            example_sentence=example_sentence,
            difficulty=difficulty,
            ai_provider=ai_provider,
            prompt_version=prompt_version,
            response_time_ms=response_time_ms,
            uses=1,
            last_used_at=datetime.now(timezone.utc),
        )
        return await self.add(entry)

    async def get_recent_for_user(self, user_id: int, limit: int = 10) -> Sequence[MnemonicHistory]:
        """Return a user's most recently generated mnemonics, newest first.

        Not yet wired into a handler, but ready for a future history-review
        feature (see docs).
        """
        result = await self._session.execute(
            select(MnemonicHistory)
            .where(MnemonicHistory.user_id == user_id)
            .order_by(MnemonicHistory.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_best_active_by_word(self, word: str) -> MnemonicHistory | None:
        """Return the highest-rated ACTIVE version for `word`, or None.

        This is the mnemonic library's serving rule (V1.2): prefer the
        best-performing version, not just the most recent one. Ties (most
        commonly "no feedback yet on either", both at 0.0) fall back to
        newest-first, which favors trying fresh unrated content over old
        neutral content when there's no strong signal either way.

        Returning None here is what `MnemonicService.get_or_generate`
        interprets as a cache miss — this happens both for a genuinely new
        word AND for a word whose every version has been deactivated for
        poor quality, so the system naturally regenerates fresh content
        instead of ever serving a demoted version.

        Callers must pass an already-normalized (`.strip().lower()`) word.
        """
        result = await self._session.execute(
            select(MnemonicHistory)
            .where(MnemonicHistory.word == word, MnemonicHistory.is_active.is_(True))
            .order_by(MnemonicHistory.average_rating.desc(), MnemonicHistory.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all_by_word(self, word: str) -> Sequence[MnemonicHistory]:
        """Return every version ever generated for `word` (active or not), newest first.

        Used by the regenerate flow to know what to tell the AI to avoid repeating.
        """
        result = await self._session.execute(
            select(MnemonicHistory)
            .where(MnemonicHistory.word == word)
            .order_by(MnemonicHistory.created_at.desc())
        )
        return result.scalars().all()

    async def record_use(self, mnemonic_history_id: int) -> None:
        """Increment `uses` and stamp `last_used_at` — called every time a
        version (cached or freshly generated) is actually served to someone.

        Uses fetch-then-mutate (like `apply_feedback_delta`) rather than a
        bulk `UPDATE`, so an already-loaded `MnemonicHistory` object for this
        id elsewhere in the same session can be refreshed rather than left
        silently stale.
        """
        entry = await self.get_by_id(mnemonic_history_id)
        if entry is None:
            return
        entry.uses += 1
        entry.last_used_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(entry)

    async def increment_regenerated_count(self, mnemonic_history_id: int) -> None:
        """Mark that a learner regenerated away from this specific version —
        an implicit "this wasn't good enough" signal distinct from an
        explicit 👎.
        """
        entry = await self.get_by_id(mnemonic_history_id)
        if entry is None:
            return
        entry.regenerated_count += 1
        await self._session.flush()
        await self._session.refresh(entry)

    async def apply_feedback_delta(
        self, mnemonic_history_id: int, *, like_delta: int, dislike_delta: int
    ) -> MnemonicHistory | None:
        """Adjust `likes`/`dislikes` by the given deltas and recompute `average_rating`.

        Deltas (rather than absolute values) let the caller express "a user
        changed their vote from 👎 to 👍" as `like_delta=+1, dislike_delta=-1`
        in one call. Returns the updated row, or None if it doesn't exist.
        """
        entry = await self.get_by_id(mnemonic_history_id)
        if entry is None:
            return None

        entry.likes = max(0, entry.likes + like_delta)
        entry.dislikes = max(0, entry.dislikes + dislike_delta)
        entry.average_rating = (entry.likes - entry.dislikes) / max(1, entry.likes + entry.dislikes)

        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def deactivate(self, mnemonic_history_id: int) -> None:
        """Soft-delete: mark a version inactive so it's never served again,
        without ever deleting the row (historical data is always preserved).
        """
        entry = await self.get_by_id(mnemonic_history_id)
        if entry is None:
            return
        entry.is_active = False
        await self._session.flush()
