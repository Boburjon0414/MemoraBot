"""Activity and statistics tools — read learning timeline and progress."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from typing import Any

from app.database.models.learning_activity import ActivityType
from app.services.tools.base import (
    PlatformTool, ToolContext, ToolDefinition, ToolParameter, ToolResult,
)

logger = logging.getLogger(__name__)


class GetRecentActivityTool(PlatformTool):
    """High-level activity summary for the last N days."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_activity",
            description="Return a count summary of learning activities in the last N days (vocabulary lookups, quizzes, chat messages, etc.).",
            parameters=[
                ToolParameter("days", "int", "Days to look back.", required=False, default=7),
            ],
            return_description="Dict with key: activity (dict[str, int] — activity_type → count).",
            features=["chat", "summary"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            days = int(kwargs.get("days", 7))
            since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
            summary = await context.activity_repo.get_summary(context.user_id, since=since)
            return ToolResult.ok("get_recent_activity", activity=summary, days=days)
        except Exception as exc:
            logger.warning("get_recent_activity failed: %s", exc)
            return ToolResult.fail("get_recent_activity", str(exc))


class GetActivityByTypeTool(PlatformTool):
    """Count of a specific activity type over a period."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_activity_by_type",
            description="Return the count of a specific activity type (e.g. 'mnemonic_generated', 'quiz_answered') for the last N days.",
            parameters=[
                ToolParameter("activity_type", "str", "One of: mnemonic_generated, vocabulary_saved, quiz_answered, ai_chat_message, flashcard_reviewed, document_uploaded."),
                ToolParameter("days", "int", "Days to look back.", required=False, default=7),
            ],
            return_description="Dict with keys: activity_type (str), count (int), days (int).",
            features=["chat", "summary"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            activity_type_str = str(kwargs.get("activity_type", ""))
            days = int(kwargs.get("days", 7))
            # Validate
            valid_types = {e.value for e in ActivityType}
            if activity_type_str not in valid_types:
                return ToolResult.fail(
                    "get_activity_by_type",
                    f"Unknown activity_type {activity_type_str!r}. Valid: {sorted(valid_types)}"
                )
            activity_type = ActivityType(activity_type_str)
            since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
            count = await context.activity_repo.count_by_type(
                context.user_id, activity_type, since=since
            )
            return ToolResult.ok(
                "get_activity_by_type",
                activity_type=activity_type_str,
                count=count,
                days=days,
            )
        except Exception as exc:
            logger.warning("get_activity_by_type failed: %s", exc)
            return ToolResult.fail("get_activity_by_type", str(exc))


class GetStreakTool(PlatformTool):
    """Current and best study streak."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_streak",
            description="Return the user's current study streak (consecutive days with any activity) and their all-time best streak.",
            parameters=[],
            return_description="Dict with keys: current_streak (int), best_streak (int).",
            features=["chat", "summary"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            current, best = await context.activity_service.get_streak(context.user_id)
            return ToolResult.ok("get_streak", current_streak=current, best_streak=best)
        except Exception as exc:
            logger.warning("get_streak failed: %s", exc)
            return ToolResult.fail("get_streak", str(exc))


class GetLearningStatisticsTool(PlatformTool):
    """Comprehensive learning statistics."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_learning_statistics",
            description="Return a comprehensive learning statistics summary: total words, streak, weekly/monthly activity counts, and vocabulary size.",
            parameters=[],
            return_description="Dict with keys: vocabulary_size, current_streak, best_streak, words_this_week, words_this_month, chats_this_week, quizzes_this_month.",
            features=["chat", "summary"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            now = datetime.now(UTC).replace(tzinfo=None)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            current, best = await context.activity_service.get_streak(context.user_id)
            week_summary = await context.activity_repo.get_summary(context.user_id, since=week_ago)
            month_summary = await context.activity_repo.get_summary(context.user_id, since=month_ago)
            vocab_size = await context.vocabulary_repo.count(context.user_id)

            return ToolResult.ok(
                "get_learning_statistics",
                vocabulary_size=vocab_size,
                current_streak=current,
                best_streak=best,
                words_this_week=week_summary.get("mnemonic_generated", 0),
                words_this_month=month_summary.get("mnemonic_generated", 0),
                chats_this_week=week_summary.get("ai_chat_message", 0),
                quizzes_this_month=month_summary.get("quiz_answered", 0),
                words_saved_total=vocab_size,
            )
        except Exception as exc:
            logger.warning("get_learning_statistics failed: %s", exc)
            return ToolResult.fail("get_learning_statistics", str(exc))


class GetProgressSummaryTool(PlatformTool):
    """Human-readable progress summary for injection into prompts."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_progress_summary",
            description="Return a human-readable summary of the user's overall learning progress.",
            parameters=[],
            return_description="Dict with key: summary (str).",
            features=["chat", "summary"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            uc = context.user_context
            parts = []
            if uc.vocabulary_size > 0:
                parts.append(f"{uc.vocabulary_size} words saved")
            if uc.current_streak_days > 0:
                parts.append(f"{uc.current_streak_days}-day streak")
            if uc.english_level:
                parts.append(f"{uc.english_level} level")
            if uc.learning_goal:
                parts.append(f"studying for {uc.learning_goal}")
            summary = ", ".join(parts) if parts else "No progress data recorded yet."
            return ToolResult.ok("get_progress_summary", summary=summary)
        except Exception as exc:
            return ToolResult.fail("get_progress_summary", str(exc))
