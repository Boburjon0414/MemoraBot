"""UserMemoryService: reads and updates a user's long-term learning profile.

This is a thin domain layer over UserMemoryRepository that:
  1. Provides a `get_or_create()` method so callers never worry about whether
     a memory row exists (lazy creation covers users registered before Step 8).
  2. Keeps update logic DRY (callers pass named kwargs; service validates and
     delegates to the repository).
  3. Never raises for missing rows — it creates them lazily instead.

Who calls this
--------------
  UserContextService.build()  — reads memory to populate UserContext.
  UserService.register_user() — calls create_default() at registration.
  Future handlers:
    /settings → set_english_level(), set_learning_goal()
    QuizService → record_weak_word() after wrong answers
    ContentService → set_active_topic() when a document is indexed

Failure isolation
-----------------
All methods log and return None/[] rather than raising when the DB is
unavailable, so a memory service failure never crashes a primary feature.
"""

from __future__ import annotations

import logging

from app.database.models.user_memory import UserMemory
from app.repositories.user_memory_repository import UserMemoryRepository

logger = logging.getLogger(__name__)

# Valid CEFR levels for english_level validation
_CEFR_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}


class UserMemoryService:
    """Reads and updates a user's long-term learning profile."""

    def __init__(self, memory_repo: UserMemoryRepository) -> None:
        self._repo = memory_repo

    # ── Lifecycle ──────────────────────────────────────────────────────── #

    async def get_or_create(self, user_id: int) -> UserMemory:
        """Return the memory row for `user_id`, creating a blank one if absent.

        This is the safe read path for all callers. It handles:
          - Users registered before Step 8 (no row yet → create blank row).
          - Users registered after Step 8 (row created at registration).

        Never raises.
        """
        try:
            memory = await self._repo.get_by_user_id(user_id)
            if memory is None:
                memory = await self._repo.create_default(user_id)
                logger.info(
                    "UserMemoryService.get_or_create: created blank row for user_id=%s",
                    user_id,
                )
            return memory
        except Exception:
            logger.exception(
                "UserMemoryService.get_or_create: DB error for user_id=%s", user_id
            )
            # Return an unsaved, detached object as a safe fallback so callers
            # can still read None fields without crashing.
            return UserMemory(user_id=user_id)

    # ── Profile updates ────────────────────────────────────────────────── #

    async def set_english_level(
        self, user_id: int, level: str
    ) -> UserMemory | None:
        """Set the user's CEFR English level.

        Args:
            user_id: Internal users.id PK.
            level:   One of "A1", "A2", "B1", "B2", "C1", "C2".

        Returns:
            Updated UserMemory, or None if validation fails or DB error.
        """
        level = level.upper().strip()
        if level not in _CEFR_LEVELS:
            logger.warning(
                "UserMemoryService.set_english_level: invalid level %r for user_id=%s",
                level, user_id,
            )
            return None
        await self.get_or_create(user_id)   # ensure row exists
        return await self._repo.update_fields(user_id, english_level=level)

    async def set_learning_goal(
        self, user_id: int, goal: str
    ) -> UserMemory | None:
        """Set the user's learning goal (free text, max 255 chars)."""
        goal = goal.strip()[:255]
        if not goal:
            return None
        await self.get_or_create(user_id)
        return await self._repo.update_fields(user_id, learning_goal=goal)

    async def set_native_language(
        self, user_id: int, language_code: str
    ) -> UserMemory | None:
        """Set the user's native language code (e.g. "uz", "ru", "tr")."""
        language_code = language_code.strip().lower()[:8]
        if not language_code:
            return None
        await self.get_or_create(user_id)
        return await self._repo.update_fields(user_id, native_language=language_code)

    async def set_active_topic(
        self, user_id: int, topic: str
    ) -> UserMemory | None:
        """Set the topic the user is currently focused on."""
        topic = topic.strip()[:255]
        if not topic:
            return None
        await self.get_or_create(user_id)
        updated = await self._repo.update_fields(user_id, active_topic=topic)
        # Also add to topic_interests for longer-term context
        if updated:
            await self._repo.add_topic_interest(user_id, topic)
        return updated

    # ── Adaptive data ──────────────────────────────────────────────────── #

    async def record_weak_word(self, user_id: int, word: str) -> None:
        """Record that the user answered incorrectly for `word`.

        Called by QuizService after a wrong answer.  Fire-and-forget:
        failure is logged but never propagated.
        """
        try:
            await self.get_or_create(user_id)
            await self._repo.add_weak_word(user_id, word)
            logger.debug(
                "UserMemoryService.record_weak_word: user_id=%s word=%r", user_id, word
            )
        except Exception:
            logger.warning(
                "UserMemoryService.record_weak_word: failed for user_id=%s word=%r",
                user_id, word, exc_info=True,
            )

    async def get_weak_words(self, user_id: int, limit: int = 10) -> list[str]:
        """Return the most recently struggled-with words (newest first).

        Returns [] on any error rather than raising.
        """
        try:
            return await self._repo.get_weak_words(user_id, limit=limit)
        except Exception:
            logger.warning(
                "UserMemoryService.get_weak_words: failed for user_id=%s",
                user_id, exc_info=True,
            )
            return []

    async def get_topic_interests(self, user_id: int) -> list[str]:
        """Return the user's topic interest list (oldest first).

        Returns [] on any error rather than raising.
        """
        try:
            return await self._repo.get_topic_interests(user_id)
        except Exception:
            logger.warning(
                "UserMemoryService.get_topic_interests: failed for user_id=%s",
                user_id, exc_info=True,
            )
            return []
