"""Feature output tools — read previous AI-generated artifacts."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.database.models.feature_output import OutputType
from app.services.tools.base import (
    PlatformTool, ToolContext, ToolDefinition, ToolParameter, ToolResult,
)

logger = logging.getLogger(__name__)


def _titles_from_rows(rows: list, n: int = 5) -> list[str]:
    """Extract display titles from FeatureOutput rows."""
    titles = []
    for row in rows[:n]:
        t = row.title
        if not t:
            try:
                data = json.loads(row.payload_json)
                t = data.get("topic") or data.get("title") or f"Output #{row.id}"
            except Exception:
                t = f"Output #{row.id}"
        titles.append(t)
    return titles


class GetRecentQuizzesTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_quizzes",
            description="Return the titles/topics of the user's most recent generated quizzes.",
            parameters=[
                ToolParameter("limit", "int", "Max quizzes to return.", required=False, default=5),
            ],
            return_description="Dict with key: quizzes (list[str] — topic/title of each quiz).",
            features=["chat", "quiz"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            limit = int(kwargs.get("limit", 5))
            rows = await context.feature_output_repo.get_recent_by_type(
                context.user_id, OutputType.QUIZ.value, limit=limit
            )
            return ToolResult.ok("get_recent_quizzes", quizzes=_titles_from_rows(rows, limit))
        except Exception as exc:
            logger.warning("get_recent_quizzes failed: %s", exc)
            return ToolResult.fail("get_recent_quizzes", str(exc))


class GetRecentFlashcardsTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_flashcards",
            description="Return the topics of the user's most recently generated flashcard sets.",
            parameters=[
                ToolParameter("limit", "int", "Max sets to return.", required=False, default=5),
            ],
            return_description="Dict with key: flashcard_sets (list[str]).",
            features=["chat", "flashcards"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            limit = int(kwargs.get("limit", 5))
            rows = await context.feature_output_repo.get_recent_by_type(
                context.user_id, OutputType.FLASHCARD_SET.value, limit=limit
            )
            return ToolResult.ok("get_recent_flashcards", flashcard_sets=_titles_from_rows(rows, limit))
        except Exception as exc:
            logger.warning("get_recent_flashcards failed: %s", exc)
            return ToolResult.fail("get_recent_flashcards", str(exc))


class GetRecentSummariesTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_summaries",
            description="Return the titles of the user's most recently generated summaries.",
            parameters=[
                ToolParameter("limit", "int", "Max summaries to return.", required=False, default=5),
            ],
            return_description="Dict with key: summaries (list[str]).",
            features=["chat", "summary"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            limit = int(kwargs.get("limit", 5))
            rows = await context.feature_output_repo.get_recent_by_type(
                context.user_id, OutputType.SUMMARY.value, limit=limit
            )
            return ToolResult.ok("get_recent_summaries", summaries=_titles_from_rows(rows, limit))
        except Exception as exc:
            logger.warning("get_recent_summaries failed: %s", exc)
            return ToolResult.fail("get_recent_summaries", str(exc))


class GetRecentPresentationsTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_presentations",
            description="Return the titles of the user's most recently generated presentation outlines.",
            parameters=[
                ToolParameter("limit", "int", "Max presentations to return.", required=False, default=5),
            ],
            return_description="Dict with key: presentations (list[str]).",
            features=["chat", "presentation"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            limit = int(kwargs.get("limit", 5))
            rows = await context.feature_output_repo.get_recent_by_type(
                context.user_id, OutputType.PRESENTATION_OUTLINE.value, limit=limit
            )
            return ToolResult.ok("get_recent_presentations", presentations=_titles_from_rows(rows, limit))
        except Exception as exc:
            logger.warning("get_recent_presentations failed: %s", exc)
            return ToolResult.fail("get_recent_presentations", str(exc))


class GetRecentChatSessionsTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_chat_sessions",
            description="Return the titles of the user's recent AI chat sessions.",
            parameters=[
                ToolParameter("limit", "int", "Max sessions to return.", required=False, default=5),
            ],
            return_description="Dict with key: chat_sessions (list[str]).",
            features=["chat"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            limit = int(kwargs.get("limit", 5))
            rows = await context.feature_output_repo.get_recent_by_type(
                context.user_id, OutputType.CHAT_SESSION.value, limit=limit
            )
            return ToolResult.ok("get_recent_chat_sessions", chat_sessions=_titles_from_rows(rows, limit))
        except Exception as exc:
            logger.warning("get_recent_chat_sessions failed: %s", exc)
            return ToolResult.fail("get_recent_chat_sessions", str(exc))
