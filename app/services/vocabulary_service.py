"""VocabularyService — business logic for the personal vocabulary library (V1.6).

Responsibilities
----------------
  • Auto-save every successfully generated mnemonic into the user's vocab.
  • Detect genuine system improvements (prompt_version upgrade) vs user
    manual regenerations (same prompt_version → ignored).
  • Coordinate the versioning state machine: create / set_pending /
    apply_pending / clear_pending / toggle_favorite / delete.
  • Provide paginated list and search results with total counts.
  • Remain the single authoritative place for vocab business rules; handlers
    stay thin.

Versioning rule ("system improvement" detection)
-------------------------------------------------
A mnemonic is a "genuine system improvement" if and only if:

    int(incoming.prompt_version.lstrip("v")) > int(active.prompt_version.lstrip("v"))

Manual user regenerations always share the same prompt_version as the
bot's current configuration, so they will match the user's active version
and NEVER set pending_mnemonic_id.

Extension points
----------------
  • _save_from_mnemonic has a marked comment for the SM-2 scheduling hook
    (V1.7 Spaced Repetition).
  • accept_pending_update accepts a `retention_days` parameter that the
    future configurable-retention feature can wire to UserSettings.
"""

from __future__ import annotations

import logging

from app.database.models.mnemonic_history import MnemonicHistory
from app.database.models.vocabulary import VocabularyEntry
from app.repositories.vocabulary_repository import (
    DEFAULT_ARCHIVE_RETENTION_DAYS,
    DEFAULT_PAGE_SIZE,
    VocabularyRepository,
)

logger = logging.getLogger(__name__)


def _prompt_version_int(version: str) -> int:
    """Convert a prompt version string (e.g. 'v1', 'v12') to a comparable int.

    Strips the leading 'v' (case-insensitive) and returns 0 for anything
    that doesn't parse cleanly — an unknown version is treated as the
    oldest, never as an upgrade.
    """
    try:
        return int(version.lstrip("vV") or "0")
    except ValueError:
        return 0


def _is_system_improvement(incoming_version: str, active_version: str) -> bool:
    """Return True only when the incoming mnemonic was produced by a strictly
    newer prompt version than the user's currently active one.

    Manual user regenerations always run against the same deployed prompt
    version and will always return False here — they never trigger a
    "new version available" notification.
    """
    return _prompt_version_int(incoming_version) > _prompt_version_int(active_version)


class VocabularyService:
    """Business logic for My Vocabulary.  Delegates all SQL to VocabularyRepository."""

    def __init__(self, vocab_repo: VocabularyRepository) -> None:
        self._repo = vocab_repo

    # ── Auto-save (called after every successful mnemonic generation) ──── #

    async def save_from_mnemonic(
        self,
        *,
        user_id: int,
        mnemonic: MnemonicHistory,
    ) -> VocabularyEntry:
        """Auto-save hook called after every successful get_or_generate / regenerate.

        Behaviour:
          • First time the user sees this word → create a new entry.
          • Word already in vocabulary, same prompt_version (cache hit or
            manual regeneration) → return existing entry untouched.
          • Word already in vocabulary, incoming prompt_version is strictly
            higher → set pending_mnemonic_id to signal "✨ update available".
            The user's active mnemonic is NOT replaced.

        This method is idempotent: calling it multiple times with the same
        mnemonic produces the same result.

        Extension point (V1.7 Spaced Repetition)
        -----------------------------------------
        After `create_from_mnemonic`, call:
            await self._repo.set_initial_review_schedule(entry.id)
        Once review_due_at / review_count / next_interval columns exist.
        """
        existing = await self._repo.get_by_user_and_word(user_id, mnemonic.word)

        if existing is None:
            # First time this user has seen this word — create their entry.
            entry = await self._repo.create_from_mnemonic(user_id, mnemonic)
            logger.info(
                "Auto-saved new vocabulary entry: user_id=%s word=%r entry_id=%s",
                user_id,
                mnemonic.word,
                entry.id,
            )
            # Extension point (V1.7): set_initial_review_schedule(entry.id)
            return entry

        # Word already in vocabulary — check for genuine system improvement.
        if _is_system_improvement(mnemonic.prompt_version, existing.active_prompt_version):
            # Only set pending if it's not already pointing at this mnemonic
            # (idempotent guard against duplicate calls).
            if existing.pending_mnemonic_id != mnemonic.id:
                await self._repo.set_pending(existing.id, mnemonic)
                logger.info(
                    "System improvement detected: user_id=%s word=%r "
                    "active_version=%s incoming_version=%s pending_mnemonic_id=%s",
                    user_id,
                    mnemonic.word,
                    existing.active_prompt_version,
                    mnemonic.prompt_version,
                    mnemonic.id,
                )
                await self._repo._session.refresh(existing)
        # else: same prompt_version → cache hit or manual regeneration → no-op.

        return existing

    # ── List & Search ──────────────────────────────────────────────────── #

    async def get_page(
        self,
        user_id: int,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
        search_query: str | None = None,
    ) -> tuple[list[VocabularyEntry], int]:
        """Return (entries, total_count) for one page of the user's vocabulary.

        Favorites appear first, then alphabetical.  If `search_query` is
        given, the list is filtered by word and meaning substring.
        """
        entries = await self._repo.get_page(
            user_id=user_id,
            page=page,
            page_size=page_size,
            search_query=search_query,
        )
        total = await self._repo.count(user_id=user_id, search_query=search_query)
        return entries, total

    async def get_detail(self, user_id: int, entry_id: int) -> VocabularyEntry | None:
        """Fetch a vocabulary entry only when it belongs to the user."""
        return await self._repo.get_by_user_and_id(user_id, entry_id)

    async def get_adjacent_ids(
        self,
        user_id: int,
        current_word: str,
        search_query: str | None = None,
    ) -> tuple[int | None, int | None]:
        """Return (prev_entry_id, next_entry_id) for in-detail navigation."""
        return await self._repo.get_adjacent_ids(
            user_id=user_id,
            current_word=current_word,
            search_query=search_query,
        )

    # ── Versioning ─────────────────────────────────────────────────────── #

    async def accept_pending_update(
        self,
        user_id: int,
        entry_id: int,
        retention_days: int = DEFAULT_ARCHIVE_RETENTION_DAYS,
    ) -> VocabularyEntry:
        """User chose '✨ Update Mnemonic'.

        Promotes the pending mnemonic to active and archives the old one.
        The archived version is retained for `retention_days` to allow a
        future rollback UI (not implemented in V1.6).

        Raises:
            ValueError: propagated from repository if no pending mnemonic exists.
        """
        return await self._repo.apply_pending_update(user_id, entry_id, retention_days)

    async def reject_pending_update(self, user_id: int, entry_id: int) -> None:
        """User chose 'Keep Current'.

        Clears pending_mnemonic_id.  Active mnemonic is untouched.
        """
        entry = await self._repo.get_by_user_and_id(user_id, entry_id)
        if entry is None:
            raise ValueError(f"VocabularyEntry id={entry_id} not found.")
        await self._repo.clear_pending(entry_id)

    # ── Personal state mutations ───────────────────────────────────────── #

    async def toggle_favorite(self, user_id: int, entry_id: int) -> bool:
        """Toggle is_favorite on the entry; return the new value."""
        return await self._repo.toggle_favorite(user_id, entry_id)

    async def delete(self, user_id: int, entry_id: int) -> None:
        """Hard-delete the user's vocabulary entry.

        Does NOT touch mnemonic_history.  The shared library and any
        future Statistics / Review data are unaffected.
        """
        await self._repo.delete_entry(user_id, entry_id)
        logger.info("Vocabulary entry deleted: entry_id=%s", entry_id)
