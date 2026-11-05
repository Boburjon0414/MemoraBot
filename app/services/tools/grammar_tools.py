"""Grammar-specific tools for the ToolRegistry.

These tools let the AIPlanner inject real grammar progress data into
AIContext before any grammar-related AI call.  They follow the same
read-only, never-raise contract as all other PlatformTools.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from app.services.tools.base import (
    PlatformTool, ToolContext, ToolDefinition, ToolParameter, ToolResult,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_GRAMMAR_FEATURES = ["grammar", "quiz", "chat"]


class GetStudiedGrammarTopicsTool(PlatformTool):
    """Return grammar topics the user has actually studied (opened a lesson for).

    Used by the AIPlanner for grammar Q&A and grammar quiz generation to give
    the AI accurate context about what grammar the user knows.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_studied_grammar_topics",
            description=(
                "Return grammar topics the user has actually studied (opened a lesson). "
                "Use for grammar Q&A or grammar quiz generation to avoid testing "
                "grammar the user has never encountered."
            ),
            parameters=[
                ToolParameter("limit", "int", "Maximum topics to return.", required=False, default=10),
            ],
            return_description=(
                "Dict with keys: "
                "studied_topics (list[dict] — each has topic_id, slug, title, "
                "status, mastery_score, last_studied_at, questions_answered, "
                "questions_correct, questions_wrong)."
            ),
            features=_GRAMMAR_FEATURES,
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            grammar_progress_repo = getattr(context, "grammar_progress_repo", None)
            grammar_topic_repo    = getattr(context, "grammar_topic_repo", None)
            if grammar_progress_repo is None or grammar_topic_repo is None:
                return ToolResult.empty("get_studied_grammar_topics")

            limit = int(kwargs.get("limit", 10))
            rows = await grammar_progress_repo.get_recent_topics(context.user_id, limit=limit)
            if not rows:
                return ToolResult.empty("get_studied_grammar_topics")

            # Fetch topic metadata for each progress row
            topic_ids = [r.grammar_topic_id for r in rows]
            from sqlalchemy import select
            from app.database.models.grammar_topic import GrammarTopic
            result = await grammar_topic_repo._session.execute(
                select(GrammarTopic).where(GrammarTopic.id.in_(topic_ids))
            )
            topics_by_id = {t.id: t for t in result.scalars().all()}

            studied = []
            for row in rows:
                topic = topics_by_id.get(row.grammar_topic_id)
                studied.append({
                    "topic_id": row.grammar_topic_id,
                    "slug": topic.slug if topic else "",
                    "title": topic.title if topic else f"topic_{row.grammar_topic_id}",
                    "description": topic.description if topic else None,
                    "status": row.status,
                    "mastery_score": round(row.mastery_score, 2),
                    "last_studied_at": row.last_studied_at.isoformat() if row.last_studied_at else None,
                    "questions_answered": row.questions_answered,
                    "questions_correct": row.questions_correct,
                    "questions_wrong": row.questions_wrong,
                })

            return ToolResult.ok("get_studied_grammar_topics", studied_topics=studied)
        except Exception as exc:
            logger.warning("get_studied_grammar_topics failed: %s", exc)
            return ToolResult.fail("get_studied_grammar_topics", str(exc))


class GetGrammarProgressTool(PlatformTool):
    """Return progress for a specific grammar topic."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_grammar_progress",
            description=(
                "Return detailed progress for a specific grammar topic by its ID. "
                "Returns None if the user has not studied this topic yet."
            ),
            parameters=[
                ToolParameter("topic_id", "int", "GrammarTopic.id to look up."),
            ],
            return_description=(
                "Dict with keys: topic_id, status, mastery_score, "
                "lessons_opened, questions_answered, questions_correct, "
                "questions_wrong, last_score, last_studied_at. "
                "Returns empty result if not started."
            ),
            features=_GRAMMAR_FEATURES,
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            grammar_progress_repo = getattr(context, "grammar_progress_repo", None)
            if grammar_progress_repo is None:
                return ToolResult.empty("get_grammar_progress")

            topic_id = int(kwargs.get("topic_id", 0))
            if not topic_id:
                return ToolResult.fail("get_grammar_progress", "topic_id is required")

            row = await grammar_progress_repo.get(context.user_id, topic_id)
            if row is None:
                return ToolResult.empty("get_grammar_progress")

            return ToolResult.ok(
                "get_grammar_progress",
                topic_id=row.grammar_topic_id,
                status=row.status,
                mastery_score=round(row.mastery_score, 2),
                lessons_opened=row.lessons_opened,
                questions_answered=row.questions_answered,
                questions_correct=row.questions_correct,
                questions_wrong=row.questions_wrong,
                last_score=round(row.last_score, 2) if row.last_score is not None else None,
                last_studied_at=row.last_studied_at.isoformat() if row.last_studied_at else None,
            )
        except Exception as exc:
            logger.warning("get_grammar_progress failed: %s", exc)
            return ToolResult.fail("get_grammar_progress", str(exc))


class GetActiveGrammarTopicsTool(PlatformTool):
    """Return all active grammar topics from the catalogue.

    Used by the planner when it needs to give the AI the full topic list
    (e.g. for recommending what to study next).
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_active_grammar_topics",
            description=(
                "Return all active grammar topics from the lesson catalogue. "
                "Includes topic ID, slug, title, difficulty, and order."
            ),
            parameters=[],
            return_description=(
                "Dict with key: topics (list[dict] — id, slug, title, "
                "difficulty, order_index, description)."
            ),
            features=_GRAMMAR_FEATURES,
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            grammar_topic_repo = getattr(context, "grammar_topic_repo", None)
            if grammar_topic_repo is None:
                return ToolResult.empty("get_active_grammar_topics")

            topics = await grammar_topic_repo.list_active()
            return ToolResult.ok(
                "get_active_grammar_topics",
                topics=[
                    {
                        "id": t.id,
                        "slug": t.slug,
                        "title": t.title,
                        "description": t.description,
                        "difficulty": t.difficulty,
                        "order_index": t.order_index,
                    }
                    for t in topics
                ],
            )
        except Exception as exc:
            logger.warning("get_active_grammar_topics failed: %s", exc)
            return ToolResult.fail("get_active_grammar_topics", str(exc))
