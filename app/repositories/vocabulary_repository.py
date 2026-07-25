"""VocabularyRepository — data-access layer for `vocabulary_entries`.

Responsibilities
----------------
  • All SQL for the personal vocabulary table lives here.
  • Zero business logic — that belongs in VocabularyService.
  • Pagination is implemented once here; future modules (QuizRepository,
    ReviewRepository) copy the same (items, total_count) pattern.

Extension points
----------------
  • get_due_for_review() stub is intentionally absent; it goes in V1.7
    once `review_due_at` column is added in migration 0007.
  • get_page() accepts a `sort_by` parameter (defaulting to the current
    favorites-first/alphabetical order) so the Review System can sort by
    `review_due_at` without touching the method signature.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.mnemonic_history import MnemonicHistory
from app.database.models.vocabulary import VocabularyEntry
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

# Default number of entries per vocabulary list page.
DEFAULT_PAGE_SIZE = 8

# Default number of days to retain an archived mnemonic after the user
# accepts a pending update.  A future cleanup job uses `archive_expires_at`.
DEFAULT_ARCHIVE_RETENTION_DAYS = 30

SortBy = Literal["default", "alpha", "added_desc", "added_asc"]


class VocabularyRepository(BaseRepository[VocabularyEntry]):
    """Async repository for personal vocabulary entries."""

    model = VocabularyEntry

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ── Read ──────────────────────────────────────────────────────────── #

    async def get_by_user_and_word(
        self, user_id: int, word: str
    ) -> VocabularyEntry | None:
        """Fetch the user's entry for `word`, or None if they don't have it."""
        result = await self._session.execute(
            select(VocabularyEntry).where(
                VocabularyEntry.user_id == user_id,
                VocabularyEntry.word == word.lower(),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_id(
        self, user_id: int, entry_id: int
    ) -> VocabularyEntry | None:
        """Fetch an entry only when it belongs to the given user."""
        result = await self._session.execute(
            select(VocabularyEntry).where(
                VocabularyEntry.id == entry_id,
                VocabularyEntry.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def count(self, user_id: int, search_query: str | None = None) -> int:
        """Total number of vocabulary entries for a user (optionally filtered)."""
        stmt = select(func.count()).select_from(VocabularyEntry).where(
            VocabularyEntry.user_id == user_id
        )
        if search_query:
            q = f"%{search_query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(VocabularyEntry.word).like(q),
                    func.lower(VocabularyEntry.meaning).like(q),
                )
            )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_page(
        self,
        user_id: int,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
        search_query: str | None = None,
        sort_by: SortBy = "default",
    ) -> list[VocabularyEntry]:
        """Return one page of a user's vocabulary entries.

        Default sort: favorites first, then alphabetical by word.
        The `sort_by` parameter is a forward-compatibility hook for the
        Review System (V1.7) which will need `sort_by="review_due_asc"`.

        Args:
            page:         0-based page index.
            page_size:    Entries per page (default DEFAULT_PAGE_SIZE).
            search_query: Optional substring filter on word and meaning.
            sort_by:      Ordering strategy (extensible for future sorts).
        """
        stmt = select(VocabularyEntry).where(VocabularyEntry.user_id == user_id)

        if search_query:
            q = f"%{search_query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(VocabularyEntry.word).like(q),
                    func.lower(VocabularyEntry.meaning).like(q),
                )
            )

        if sort_by == "alpha":
            stmt = stmt.order_by(VocabularyEntry.word.asc())
        elif sort_by == "added_desc":
            stmt = stmt.order_by(VocabularyEntry.added_at.desc())
        elif sort_by == "added_asc":
            stmt = stmt.order_by(VocabularyEntry.added_at.asc())
        else:
            # Default: favorites first, then alphabetical.
            stmt = stmt.order_by(
                VocabularyEntry.is_favorite.desc(),
                VocabularyEntry.word.asc(),
            )

        stmt = stmt.offset(page * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_adjacent_ids(
        self,
        user_id: int,
        current_word: str,
        search_query: str | None = None,
    ) -> tuple[int | None, int | None]:
        """Return (prev_entry_id, next_entry_id) in the sorted list order.

        Uses the same favorites-first/alpha ordering as get_page() so that
        prev/next navigation in the detail screen is consistent with the list.
        """
        stmt = (
            select(VocabularyEntry.id, VocabularyEntry.word, VocabularyEntry.is_favorite)
            .where(VocabularyEntry.user_id == user_id)
        )
        if search_query:
            q = f"%{search_query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(VocabularyEntry.word).like(q),
                    func.lower(VocabularyEntry.meaning).like(q),
                )
            )
        stmt = stmt.order_by(
            VocabularyEntry.is_favorite.desc(),
            VocabularyEntry.word.asc(),
        )

        result = await self._session.execute(stmt)
        rows = result.all()  # list of (id, word, is_favorite)

        # Find the position of the current word in the ordered list.
        current_idx: int | None = None
        for i, row in enumerate(rows):
            if row.word == current_word:
                current_idx = i
                break

        if current_idx is None:
            return None, None

        prev_id = rows[current_idx - 1].id if current_idx > 0 else None
        next_id = rows[current_idx + 1].id if current_idx < len(rows) - 1 else None
        return prev_id, next_id

    # ── Write ─────────────────────────────────────────────────────────── #

    async def create_from_mnemonic(
        self,
        user_id: int,
        mnemonic: MnemonicHistory,
    ) -> VocabularyEntry:
        """Create the user's first vocabulary entry for a word.

        Called only when `get_by_user_and_word` returned None (new word).
        """
        entry = VocabularyEntry(
            user_id=user_id,
            active_mnemonic_id=mnemonic.id,
            active_prompt_version=mnemonic.prompt_version,
            word=mnemonic.word.lower(),
            meaning=mnemonic.meaning,
            uzbek_pronunciation=mnemonic.uzbek_pronunciation,
            mnemonic_story=mnemonic.mnemonic_story,
            example_sentence=mnemonic.example_sentence,
            difficulty=mnemonic.difficulty,
        )
        return await self.add(entry)

    async def set_pending(
        self,
        entry_id: int,
        pending_mnemonic: MnemonicHistory,
    ) -> None:
        """Mark a system-improvement mnemonic as pending for the user's entry.

        The user's active mnemonic is NOT changed.  The ✨ indicator on the
        list screen reads `pending_mnemonic_id IS NOT NULL`.
        """
        await self._session.execute(
            update(VocabularyEntry)
            .where(VocabularyEntry.id == entry_id)
            .values(pending_mnemonic_id=pending_mnemonic.id)
        )
        await self._session.flush()

    async def clear_pending(self, entry_id: int) -> None:
        """Dismiss the pending update (user chose 'Keep Current').

        Active mnemonic is untouched.  pending_mnemonic_id → NULL.
        """
        await self._session.execute(
            update(VocabularyEntry)
            .where(VocabularyEntry.id == entry_id)
            .values(pending_mnemonic_id=None)
        )
        await self._session.flush()

    async def apply_pending_update(
        self,
        user_id: int,
        entry_id: int,
        retention_days: int = DEFAULT_ARCHIVE_RETENTION_DAYS,
    ) -> VocabularyEntry:
        """Accept the pending update: promote pending → active, old active → archived.

        Workflow:
          1. Load the entry (validates it exists and has a pending mnemonic).
          2. Move current active_mnemonic_id → archived_mnemonic_id.
          3. Move pending_mnemonic_id → active_mnemonic_id.
          4. Update denormalized content from the new active mnemonic.
          5. Set archived_at and archive_expires_at.
          6. Clear pending_mnemonic_id.

        Raises:
            ValueError: if the entry has no pending mnemonic (caller should
                        have validated this before calling).
        """
        entry = await self.get_by_user_and_id(user_id, entry_id)
        if entry is None or entry.pending_mnemonic_id is None:
            raise ValueError(
                f"VocabularyEntry id={entry_id} has no pending mnemonic to apply."
            )

        # Load the new (pending) mnemonic to pull denormalized content.
        new_mnemonic = await self._session.get(MnemonicHistory, entry.pending_mnemonic_id)
        if new_mnemonic is None:
            # Pending mnemonic was deleted from the library — just clear it.
            await self.clear_pending(entry_id)
            return entry

        now = datetime.utcnow()

        await self._session.execute(
            update(VocabularyEntry)
            .where(VocabularyEntry.id == entry_id)
            .values(
                # Archive current active version
                archived_mnemonic_id=entry.active_mnemonic_id,
                archived_at=now,
                archive_expires_at=now + timedelta(days=retention_days),
                # Promote pending to active
                active_mnemonic_id=new_mnemonic.id,
                active_prompt_version=new_mnemonic.prompt_version,
                # Sync denormalized content
                meaning=new_mnemonic.meaning,
                uzbek_pronunciation=new_mnemonic.uzbek_pronunciation,
                mnemonic_story=new_mnemonic.mnemonic_story,
                example_sentence=new_mnemonic.example_sentence,
                difficulty=new_mnemonic.difficulty,
                # Clear pending slot
                pending_mnemonic_id=None,
            )
        )
        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def toggle_favorite(self, user_id: int, entry_id: int) -> bool:
        """Flip is_favorite on the given entry; return the new value."""
        entry = await self.get_by_user_and_id(user_id, entry_id)
        if entry is None:
            raise ValueError(f"VocabularyEntry id={entry_id} not found.")
        new_value = not entry.is_favorite
        await self._session.execute(
            update(VocabularyEntry)
            .where(
                VocabularyEntry.id == entry_id,
                VocabularyEntry.user_id == user_id,
            )
            .values(is_favorite=new_value)
        )
        await self._session.flush()
        return new_value

    async def delete_entry(self, user_id: int, entry_id: int) -> None:
        """Hard-delete the vocabulary entry.

        IMPORTANT: this only deletes vocabulary_entries.  mnemonic_history
        is NOT touched — the shared library survives user deletions.  This
        is intentional: Statistics and future Review modules must not lose
        data because one user deleted their personal record.
        """
        await self._session.execute(
            delete(VocabularyEntry).where(
                VocabularyEntry.id == entry_id,
                VocabularyEntry.user_id == user_id,
            )
        )
        await self._session.flush()

    async def refresh(self, entry: VocabularyEntry) -> VocabularyEntry:
        """Refresh an entry after a repository update."""
        await self._session.refresh(entry)
        return entry
