"""User profile tools — read user memory and settings."""

from __future__ import annotations

import logging
from typing import Any

from app.services.tools.base import (
    PlatformTool, ToolContext, ToolDefinition, ToolParameter, ToolResult,
)

logger = logging.getLogger(__name__)
_FEATURES = ["chat", "quiz", "flashcards", "summary", "presentation"]


class GetUserProfileTool(PlatformTool):
    """Return the full user learning profile from UserMemory."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_user_profile",
            description="Return the user's complete learning profile: CEFR level, learning goal, native language, active topic, and weak words.",
            parameters=[],
            return_description="Dict with keys: english_level, learning_goal, native_language, active_topic, weak_words (list).",
            features=_FEATURES,
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            mem = await context.memory_repo.get_by_user_id(context.user_id)
            if mem is None:
                return ToolResult.empty("get_user_profile")
            from app.repositories.user_memory_repository import _load_json_list
            return ToolResult.ok(
                "get_user_profile",
                english_level=mem.english_level,
                learning_goal=mem.learning_goal,
                native_language=mem.native_language,
                active_topic=mem.active_topic,
                weak_words=_load_json_list(mem.weak_words_json),
                topic_interests=_load_json_list(mem.topic_interests_json),
            )
        except Exception as exc:
            logger.warning("get_user_profile failed: %s", exc)
            return ToolResult.fail("get_user_profile", str(exc))


class GetLearningGoalTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_learning_goal",
            description="Return only the user's stated learning goal (e.g. 'IELTS Academic', 'business English').",
            parameters=[],
            return_description="Dict with key: learning_goal (str or None).",
            features=_FEATURES,
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            mem = await context.memory_repo.get_by_user_id(context.user_id)
            return ToolResult.ok("get_learning_goal", learning_goal=mem.learning_goal if mem else None)
        except Exception as exc:
            return ToolResult.fail("get_learning_goal", str(exc))


class GetCEFRLevelTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_cefr_level",
            description="Return the user's self-reported CEFR English level (A1–C2), or None if not set.",
            parameters=[],
            return_description="Dict with key: english_level (str or None).",
            features=_FEATURES,
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            mem = await context.memory_repo.get_by_user_id(context.user_id)
            return ToolResult.ok("get_cefr_level", english_level=mem.english_level if mem else None)
        except Exception as exc:
            return ToolResult.fail("get_cefr_level", str(exc))


class GetActiveTopicTool(PlatformTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_active_topic",
            description="Return the topic the user is currently focused on, or None if not set.",
            parameters=[],
            return_description="Dict with key: active_topic (str or None).",
            features=_FEATURES,
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            mem = await context.memory_repo.get_by_user_id(context.user_id)
            return ToolResult.ok("get_active_topic", active_topic=mem.active_topic if mem else None)
        except Exception as exc:
            return ToolResult.fail("get_active_topic", str(exc))
