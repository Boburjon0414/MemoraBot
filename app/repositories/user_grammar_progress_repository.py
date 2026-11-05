"""Repository for UserGrammarProgress — per-user grammar study history."""

from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user_grammar_progress import (
    GrammarProgressStatus,
    UserGrammarProgress,
)
from app.repositories.base import BaseRepository


class UserGrammarProgressRepository(BaseRepository[UserGrammarProgress]):
    """CRUD + domain queries for user_grammar_progress."""

    model = UserGrammarProgress

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ── Read ───────────────────────────────────────────────────────────── #

    async def get(
        self, user_id: int, grammar_topic_id: int
    ) -> UserGrammarProgress | None:
        """Fetch progress for (user_id, topic_id), or None if not started."""
        result = await self._session.execute(
            select(UserGrammarProgress)
            .where(UserGrammarProgress.user_id == user_id)
            .where(UserGrammarProgress.grammar_topic_id == grammar_topic_id)
        )
        return result.scalar_one_or_none()

    async def get_studied_topics(
        self, user_id: int
    ) -> list[UserGrammarProgress]:
        """Return all progress rows for topics the user has actually opened.

        'Studied' means a progress row exists — i.e. the lesson was opened
        at least once.  Order: most recently studied first.
        """
        result = await self._session.execute(
            select(UserGrammarProgress)
            .where(UserGrammarProgress.user_id == user_id)
            .order_by(UserGrammarProgress.last_studied_at.desc())
        )
        return list(result.scalars().all())

    async def get_recent_topics(
        self, user_id: int, limit: int = 5
    ) -> list[UserGrammarProgress]:
        """Return the N most recently studied topics."""
        result = await self._session.execute(
            select(UserGrammarProgress)
            .where(UserGrammarProgress.user_id == user_id)
            .order_by(UserGrammarProgress.last_studied_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_in_progress(
        self, user_id: int
    ) -> list[UserGrammarProgress]:
        """Return topics the user started but has not yet completed."""
        result = await self._session.execute(
            select(UserGrammarProgress)
            .where(UserGrammarProgress.user_id == user_id)
            .where(UserGrammarProgress.status == GrammarProgressStatus.IN_PROGRESS.value)
            .order_by(UserGrammarProgress.last_studied_at.desc())
        )
        return list(result.scalars().all())

    # ── Write ──────────────────────────────────────────────────────────── #

    async def get_or_create(
        self, user_id: int, grammar_topic_id: int
    ) -> tuple[UserGrammarProgress, bool]:
        """Return (progress, created).

        Creates a new IN_PROGRESS row if one does not exist yet.
        """
        row = await self.get(user_id, grammar_topic_id)
        if row is not None:
            return row, False

        row = UserGrammarProgress(
            user_id=user_id,
            grammar_topic_id=grammar_topic_id,
            status=GrammarProgressStatus.IN_PROGRESS.value,
            lessons_opened=0,
            questions_answered=0,
            questions_correct=0,
            questions_wrong=0,
            mastery_score=0.0,
        )
        row = await self.add(row)
        return row, True

    async def increment_lesson_opened(
        self, user_id: int, grammar_topic_id: int
    ) -> UserGrammarProgress | None:
        """Increment lessons_opened and update last_studied_at."""
        row = await self.get(user_id, grammar_topic_id)
        if row is None:
            return None
        row.lessons_opened += 1
        row.last_studied_at = datetime.now(UTC).replace(tzinfo=None)
        row.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        return row

    async def record_question_result(
        self,
        user_id: int,
        grammar_topic_id: int,
        *,
        correct: bool,
    ) -> UserGrammarProgress | None:
        """Record one quiz question result (correct or wrong)."""
        row = await self.get(user_id, grammar_topic_id)
        if row is None:
            return None
        row.questions_answered += 1
        if correct:
            row.questions_correct += 1
        else:
            row.questions_wrong += 1
        row.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        return row

    async def update_mastery(
        self,
        user_id: int,
        grammar_topic_id: int,
        *,
        last_score: float,
        mastery_score: float,
        status: GrammarProgressStatus,
    ) -> UserGrammarProgress | None:
        """Update mastery_score, last_score, status after a quiz completion."""
        row = await self.get(user_id, grammar_topic_id)
        if row is None:
            return None
        row.last_score = last_score
        row.mastery_score = mastery_score
        row.status = status.value
        row.last_studied_at = datetime.now(UTC).replace(tzinfo=None)
        row.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()
        return row
