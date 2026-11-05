"""Data-access layer for the `user_memory` table."""

from __future__ import annotations

import json
import logging
from datetime import datetime, UTC

from sqlalchemy import select

from app.database.models.user_memory import MAX_WEAK_WORDS, MAX_TOPIC_INTERESTS, UserMemory
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserMemoryRepository(BaseRepository[UserMemory]):
    """Repository for reading and updating a user's learning profile."""

    model = UserMemory

    async def get_by_user_id(self, user_id: int) -> UserMemory | None:
        """Fetch the memory row for `user_id`, or None if it doesn't exist."""
        result = await self._session.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_default(self, user_id: int) -> UserMemory:
        """Insert a blank UserMemory row for `user_id` and return it.

        Called by UserService.register_user() for new users.
        All nullable fields default to None — the profile fills in over time.
        """
        memory = UserMemory(user_id=user_id)
        return await self.add(memory)

    async def update_fields(
        self,
        user_id: int,
        **fields: str | None,
    ) -> UserMemory | None:
        """Update one or more scalar fields on the memory row.

        Accepted field names: english_level, learning_goal, native_language,
        active_topic.  Unknown fields are silently ignored.

        Returns the updated row, or None if no row exists for user_id.
        """
        memory = await self.get_by_user_id(user_id)
        if memory is None:
            logger.warning(
                "UserMemoryRepository.update_fields: no row for user_id=%s", user_id
            )
            return None

        allowed = {"english_level", "learning_goal", "native_language", "active_topic"}
        changed = False
        for key, value in fields.items():
            if key in allowed:
                setattr(memory, key, value)
                changed = True
            else:
                logger.warning(
                    "UserMemoryRepository.update_fields: unknown field %r — skipped", key
                )

        if changed:
            memory.updated_at = datetime.now(UTC).replace(tzinfo=None)
            await self._session.flush()
            await self._session.refresh(memory)

        return memory

    async def add_weak_word(self, user_id: int, word: str) -> UserMemory | None:
        """Append `word` to the weak_words list (deduplicating and capping at MAX).

        If the word is already present, it is moved to the end (most recent).
        When the list exceeds MAX_WEAK_WORDS, the oldest entry is dropped (FIFO).

        Returns the updated row, or None if no row exists.
        """
        memory = await self.get_by_user_id(user_id)
        if memory is None:
            return None

        words: list[str] = _load_json_list(memory.weak_words_json)
        word = word.strip().lower()

        # Deduplicate: remove existing occurrence, append at end
        words = [w for w in words if w != word]
        words.append(word)

        # FIFO eviction
        if len(words) > MAX_WEAK_WORDS:
            words = words[-MAX_WEAK_WORDS:]

        memory.weak_words_json = json.dumps(words, ensure_ascii=False)
        memory.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        await self._session.refresh(memory)
        return memory

    async def get_weak_words(self, user_id: int, limit: int = 10) -> list[str]:
        """Return the most recent `limit` weak words for `user_id`.

        Returns [] if no row exists or the list is empty.
        """
        memory = await self.get_by_user_id(user_id)
        if memory is None or not memory.weak_words_json:
            return []
        words = _load_json_list(memory.weak_words_json)
        # Most recent = end of list; return last `limit` in reverse order
        return list(reversed(words[-limit:]))

    async def add_topic_interest(self, user_id: int, topic: str) -> UserMemory | None:
        """Append `topic` to topic_interests (deduplicating, capping at MAX)."""
        memory = await self.get_by_user_id(user_id)
        if memory is None:
            return None

        topics: list[str] = _load_json_list(memory.topic_interests_json)
        topic = topic.strip()
        topics = [t for t in topics if t.lower() != topic.lower()]
        topics.append(topic)
        if len(topics) > MAX_TOPIC_INTERESTS:
            topics = topics[-MAX_TOPIC_INTERESTS:]

        memory.topic_interests_json = json.dumps(topics, ensure_ascii=False)
        memory.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        await self._session.refresh(memory)
        return memory

    async def get_topic_interests(self, user_id: int) -> list[str]:
        """Return all topic interests for `user_id`, most recent last."""
        memory = await self.get_by_user_id(user_id)
        if memory is None or not memory.topic_interests_json:
            return []
        return _load_json_list(memory.topic_interests_json)


def _load_json_list(value: str | None) -> list[str]:
    """Safely parse a JSON-encoded list of strings, returning [] on error."""
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
