"""GrammarService: the single entry point for all Grammar Learning business logic.

Responsibilities
----------------
1. List active grammar topics (for the topic selection keyboard).
2. Retrieve a specific topic by ID or slug.
3. Record lesson opens and quiz results against UserGrammarProgress.
4. Calculate mastery scores deterministically (no AI involved).
5. Return studied-topic lists for AI context and for future Grammar Quiz Auto mode.

Mastery algorithm (deterministic, no AI)
-----------------------------------------
mastery = 0.4 × recent_accuracy + 0.4 × overall_accuracy + 0.2 × attempt_factor

where:
  recent_accuracy  = last_score (most recent quiz accuracy)
  overall_accuracy = questions_correct / questions_answered (lifetime)
  attempt_factor   = min(1.0, questions_answered / MIN_ATTEMPTS_FOR_FULL_SCORE)

The topic is marked COMPLETED when mastery_score >= MASTERY_COMPLETED_THRESHOLD
AND questions_answered >= MIN_QUESTIONS_TO_COMPLETE.

This means:
  - A user needs at least MIN_QUESTIONS_TO_COMPLETE answers.
  - A single perfect quiz is not enough for COMPLETED status.
  - Consistent accuracy across multiple sessions is rewarded.
  - Attempt factor prevents gaming with a single easy question.

All thresholds are constants here (not in config) because they represent a
pedagogical design decision, not an operational parameter.  Operators should
not need to tune them to deploy the feature.
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC

from app.database.models.grammar_topic import GrammarTopic
from app.database.models.learning_activity import ActivityType
from app.database.models.user_grammar_progress import (
    GrammarProgressStatus,
    UserGrammarProgress,
)
from app.repositories.grammar_topic_repository import GrammarTopicRepository
from app.repositories.user_grammar_progress_repository import (
    UserGrammarProgressRepository,
)
from app.services.activity_service import ActivityService

logger = logging.getLogger(__name__)

# ── Mastery thresholds ─────────────────────────────────────────────────── #

MASTERY_COMPLETED_THRESHOLD = 0.80   # mastery_score must reach this for COMPLETED
MIN_QUESTIONS_TO_COMPLETE   = 5      # user must answer at least this many questions
MIN_ATTEMPTS_FOR_FULL_SCORE = 10     # attempt_factor saturates at this many questions


class GrammarService:
    """Business logic for Grammar Learning (Learn → Grammar)."""

    def __init__(
        self,
        grammar_topic_repo: GrammarTopicRepository,
        grammar_progress_repo: UserGrammarProgressRepository,
        activity_service: ActivityService,
    ) -> None:
        self._topics = grammar_topic_repo
        self._progress = grammar_progress_repo
        self._activity = activity_service

    # ── Topic catalogue ────────────────────────────────────────────────── #

    async def list_active_topics(self) -> list[GrammarTopic]:
        """Return active grammar topics ordered for the UI keyboard."""
        return await self._topics.list_active()

    async def get_topic(self, topic_id: int) -> GrammarTopic | None:
        """Fetch a single topic by PK, or None."""
        return await self._topics.get_by_id(topic_id)

    async def get_topic_by_slug(self, slug: str) -> GrammarTopic | None:
        """Fetch a topic by its URL-safe slug."""
        return await self._topics.get_by_slug(slug)

    # ── Progress tracking ──────────────────────────────────────────────── #

    async def start_topic(
        self, user_id: int, topic_id: int
    ) -> UserGrammarProgress:
        """Open a lesson: create/fetch progress row and record the open.

        Returns the updated UserGrammarProgress row.
        Does NOT record the lesson open if DB operations fail — logs instead.
        """
        # get_or_create never raises (errors propagate to caller)
        progress, created = await self._progress.get_or_create(user_id, topic_id)

        # Increment lessons_opened counter
        progress = await self._progress.increment_lesson_opened(user_id, topic_id) or progress

        # Record in activity log (fire-and-forget — failure does not interrupt)
        try:
            await self._activity.record(
                user_id,
                ActivityType.GRAMMAR_LESSON_OPENED,
                metadata={"grammar_topic_id": topic_id, "first_open": created},
            )
        except Exception:
            logger.warning(
                "GrammarService.start_topic: activity record failed uid=%s topic=%s",
                user_id, topic_id, exc_info=True,
            )

        return progress

    async def record_lesson_opened(
        self, user_id: int, topic_id: int
    ) -> UserGrammarProgress | None:
        """Explicit lesson-open record (used when re-opening an existing lesson)."""
        return await self._progress.increment_lesson_opened(user_id, topic_id)

    async def record_question_result(
        self,
        user_id: int,
        topic_id: int,
        *,
        correct: bool,
    ) -> UserGrammarProgress | None:
        """Record a single quiz question result and update counters."""
        progress = await self._progress.record_question_result(
            user_id, topic_id, correct=correct
        )
        if progress is None:
            return None

        activity_type = (
            ActivityType.GRAMMAR_QUESTION_CORRECT
            if correct
            else ActivityType.GRAMMAR_QUESTION_WRONG
        )
        try:
            await self._activity.record(
                user_id,
                activity_type,
                metadata={"grammar_topic_id": topic_id},
            )
        except Exception:
            logger.warning(
                "GrammarService.record_question_result: activity failed uid=%s",
                user_id, exc_info=True,
            )
        return progress

    async def complete_quiz(
        self,
        user_id: int,
        topic_id: int,
        *,
        correct: int,
        total: int,
    ) -> UserGrammarProgress | None:
        """Finalise a quiz session: update mastery and status.

        Called once per quiz completion after all questions are answered.
        """
        if total == 0:
            return None

        progress = await self._progress.get(user_id, topic_id)
        if progress is None:
            return None

        last_score = correct / total
        mastery = self.calculate_mastery(
            last_score=last_score,
            total_correct=progress.questions_correct,
            total_answered=progress.questions_answered,
        )
        status = (
            GrammarProgressStatus.COMPLETED
            if (
                mastery >= MASTERY_COMPLETED_THRESHOLD
                and progress.questions_answered >= MIN_QUESTIONS_TO_COMPLETE
            )
            else GrammarProgressStatus.IN_PROGRESS
        )

        progress = await self._progress.update_mastery(
            user_id, topic_id,
            last_score=last_score,
            mastery_score=mastery,
            status=status,
        )

        try:
            await self._activity.record(
                user_id,
                ActivityType.GRAMMAR_QUIZ_COMPLETED,
                score=last_score,
                metadata={
                    "grammar_topic_id": topic_id,
                    "correct": correct,
                    "total": total,
                    "mastery": mastery,
                    "status": status.value,
                },
            )
        except Exception:
            logger.warning(
                "GrammarService.complete_quiz: activity failed uid=%s", user_id, exc_info=True
            )

        return progress

    # ── Queries ────────────────────────────────────────────────────────── #

    async def get_user_progress(
        self, user_id: int, topic_id: int
    ) -> UserGrammarProgress | None:
        """Return the progress row for (user_id, topic_id), or None."""
        return await self._progress.get(user_id, topic_id)

    async def get_studied_topics(self, user_id: int) -> list[UserGrammarProgress]:
        """Return all topics the user has actually opened (has a progress row)."""
        return await self._progress.get_studied_topics(user_id)

    async def get_recent_topics(
        self, user_id: int, limit: int = 5
    ) -> list[UserGrammarProgress]:
        """Return the N most recently studied topics."""
        return await self._progress.get_recent_topics(user_id, limit=limit)

    async def get_mastery(
        self, user_id: int, topic_id: int
    ) -> float:
        """Return the current mastery score (0.0 if not started)."""
        progress = await self._progress.get(user_id, topic_id)
        return progress.mastery_score if progress else 0.0

    # ── Mastery calculation (deterministic, no AI) ─────────────────────── #

    @staticmethod
    def calculate_mastery(
        *,
        last_score: float,
        total_correct: int,
        total_answered: int,
    ) -> float:
        """Compute a composite mastery score in [0.0, 1.0].

        Formula
        -------
          mastery = 0.4 × recent_accuracy
                  + 0.4 × overall_accuracy
                  + 0.2 × attempt_factor

        recent_accuracy  = last_score (most recent quiz's accuracy)
        overall_accuracy = total_correct / total_answered (or 0 if none)
        attempt_factor   = min(1.0, total_answered / MIN_ATTEMPTS_FOR_FULL_SCORE)

        This rewards:
          - Consistently correct recent performance (recent_accuracy)
          - Historical accuracy (overall_accuracy)
          - Sufficient practice volume (attempt_factor)

        Result is clamped to [0.0, 1.0].
        """
        overall_accuracy = (
            total_correct / total_answered if total_answered > 0 else 0.0
        )
        attempt_factor = min(1.0, total_answered / MIN_ATTEMPTS_FOR_FULL_SCORE)

        mastery = (
            0.4 * last_score
            + 0.4 * overall_accuracy
            + 0.2 * attempt_factor
        )
        return max(0.0, min(1.0, mastery))
