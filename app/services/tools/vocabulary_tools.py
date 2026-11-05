"""Vocabulary tools — read word history and saved vocabulary."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from typing import Any

from app.database.models.learning_activity import ActivityType
from app.services.tools.base import (
    PlatformTool, ToolContext, ToolDefinition, ToolParameter, ToolResult,
)

logger = logging.getLogger(__name__)


class GetRecentWordsTool(PlatformTool):
    """Words the user looked up in the last N days."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_words",
            description="Return words the user looked up in the last N days (from LearningActivity). Use for quiz/flashcard generation and gap-fill exercises.",
            parameters=[
                ToolParameter("days", "int", "Number of days to look back (1=today, 7=week, 30=month).", required=False, default=7),
                ToolParameter("limit", "int", "Maximum number of words to return.", required=False, default=30),
            ],
            return_description="Dict with key: words (list[str]), each the English word looked up.",
            features=["chat", "quiz", "flashcards", "summary"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            days = int(kwargs.get("days", 7))
            limit = int(kwargs.get("limit", 30))
            since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
            words = await context.activity_repo.get_recent_mnemonic_words(
                context.user_id, since=since, limit=limit
            )
            return ToolResult.ok("get_recent_words", words=words, days=days)
        except Exception as exc:
            logger.warning("get_recent_words failed: %s", exc)
            return ToolResult.fail("get_recent_words", str(exc))


class GetSavedWordsTool(PlatformTool):
    """Words saved to the user's personal vocabulary."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_saved_words",
            description="Return words in the user's saved vocabulary list.",
            parameters=[
                ToolParameter("limit", "int", "Maximum number of words.", required=False, default=50),
            ],
            return_description="Dict with key: words (list[str]).",
            features=["chat", "quiz", "flashcards"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            limit = int(kwargs.get("limit", 50))
            # Fetch vocabulary entries and extract the word field
            from sqlalchemy import select
            from app.database.models.vocabulary import VocabularyEntry
            result = await context.vocabulary_repo._session.execute(
                select(VocabularyEntry.word)
                .where(VocabularyEntry.user_id == context.user_id)
                .limit(limit)
            )
            words = [row[0] for row in result.fetchall() if row[0]]
            return ToolResult.ok("get_saved_words", words=words)
        except Exception as exc:
            logger.warning("get_saved_words failed: %s", exc)
            return ToolResult.fail("get_saved_words", str(exc))


class GetWeakWordsTool(PlatformTool):
    """Words the user answered incorrectly in quizzes."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_weak_words",
            description="Return words the user has struggled with in quizzes, newest first.",
            parameters=[
                ToolParameter("limit", "int", "Maximum words to return.", required=False, default=20),
            ],
            return_description="Dict with key: weak_words (list[str]).",
            features=["chat", "quiz", "flashcards"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            limit = int(kwargs.get("limit", 20))
            words = await context.activity_repo.get_recent_mnemonic_words(
                context.user_id,
                since=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=90),
                limit=limit,
            )
            from app.repositories.user_memory_repository import _load_json_list
            mem = await context.memory_repo.get_by_user_id(context.user_id)
            weak = _load_json_list(mem.weak_words_json if mem else None)
            return ToolResult.ok("get_weak_words", weak_words=weak[-limit:])
        except Exception as exc:
            logger.warning("get_weak_words failed: %s", exc)
            return ToolResult.fail("get_weak_words", str(exc))


class GetVocabularyQuizWordsTool(PlatformTool):
    """Rich vocabulary data for quiz generation — the authoritative source for vocabulary quizzes.

    Returns saved words with their meanings, difficulty, and favorite status so the
    quiz generator can build personalized questions without inventing unseen words.
    Also includes weak words from UserMemory and recent looked-up words from activity.

    This is the single tool the planner MUST run for quiz feature=vocabulary.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_vocabulary_quiz_words",
            description=(
                "Return ALL user vocabulary (saved words with meanings, difficulty, favorite status), "
                "plus weak words and recent activity words, for quiz generation. "
                "Use this — not get_recent_words — whenever generating a VOCABULARY quiz. "
                "Never generate questions about words not in this list."
            ),
            parameters=[
                ToolParameter("limit", "int", "Maximum vocabulary entries to return.", required=False, default=60),
                ToolParameter("include_weak", "bool", "Include weak words from UserMemory.", required=False, default=True),
                ToolParameter("include_recent_activity", "bool", "Include recently looked-up words (last 30 days).", required=False, default=True),
            ],
            return_description=(
                "Dict with keys: "
                "vocab_words (list[dict] with word/meaning/difficulty/is_favorite/example_sentence), "
                "weak_words (list[str]), "
                "recent_activity_words (list[str]), "
                "total_vocab_count (int)."
            ),
            features=["quiz"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            limit = int(kwargs.get("limit", 60))
            include_weak = bool(kwargs.get("include_weak", True))
            include_recent_activity = bool(kwargs.get("include_recent_activity", True))

            from sqlalchemy import select
            from app.database.models.vocabulary import VocabularyEntry

            # Primary source: saved vocabulary library
            result = await context.vocabulary_repo._session.execute(
                select(
                    VocabularyEntry.word,
                    VocabularyEntry.meaning,
                    VocabularyEntry.difficulty,
                    VocabularyEntry.is_favorite,
                    VocabularyEntry.example_sentence,
                )
                .where(VocabularyEntry.user_id == context.user_id)
                .order_by(
                    VocabularyEntry.is_favorite.desc(),
                    VocabularyEntry.added_at.desc(),
                )
                .limit(limit)
            )
            rows = result.fetchall()
            vocab_words = [
                {
                    "word": row[0],
                    "meaning": row[1],
                    "difficulty": row[2],
                    "is_favorite": row[3],
                    "example_sentence": row[4],
                }
                for row in rows
            ]

            total_vocab_count = await context.vocabulary_repo.count(context.user_id)

            # Weak words from UserMemory
            weak_words: list[str] = []
            if include_weak:
                from app.repositories.user_memory_repository import _load_json_list
                mem = await context.memory_repo.get_by_user_id(context.user_id)
                weak_words = _load_json_list(mem.weak_words_json if mem else None)

            # Recent activity words (supplementary — may overlap with vocab)
            recent_activity_words: list[str] = []
            if include_recent_activity:
                since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
                recent_activity_words = await context.activity_repo.get_recent_mnemonic_words(
                    context.user_id, since=since, limit=30
                )

            return ToolResult.ok(
                "get_vocabulary_quiz_words",
                vocab_words=vocab_words,
                weak_words=weak_words,
                recent_activity_words=recent_activity_words,
                total_vocab_count=total_vocab_count,
            )
        except Exception as exc:
            logger.warning("get_vocabulary_quiz_words failed: %s", exc)
            return ToolResult.fail("get_vocabulary_quiz_words", str(exc))


class GetRecentMnemonicsTool(PlatformTool):
    """Recent mnemonic entries with full metadata."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_recent_mnemonics",
            description="Return recently looked-up words with their mnemonic stories and meanings.",
            parameters=[
                ToolParameter("days", "int", "Days to look back.", required=False, default=7),
                ToolParameter("limit", "int", "Max entries.", required=False, default=10),
            ],
            return_description="Dict with key: mnemonics (list of dicts with word, meaning, mnemonic_story).",
            features=["chat", "quiz", "flashcards"],
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        try:
            days = int(kwargs.get("days", 7))
            limit = int(kwargs.get("limit", 10))
            since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)

            # Get activity rows, then join with mnemonic_history for metadata
            rows = await context.activity_repo.get_recent_by_type(
                context.user_id, ActivityType.MNEMONIC_GENERATED, since=since, limit=limit
            )
            result_list = []
            for row in rows:
                if row.mnemonic_id:
                    from sqlalchemy import select
                    from app.database.models.mnemonic_history import MnemonicHistory
                    mn = await context.activity_repo._session.execute(
                        select(MnemonicHistory).where(MnemonicHistory.id == row.mnemonic_id)
                    )
                    mh = mn.scalar_one_or_none()
                    if mh:
                        result_list.append({
                            "word": mh.word,
                            "meaning": mh.meaning,
                            "mnemonic_story": mh.mnemonic_story,
                            "difficulty": mh.difficulty,
                        })
            return ToolResult.ok("get_recent_mnemonics", mnemonics=result_list)
        except Exception as exc:
            logger.warning("get_recent_mnemonics failed: %s", exc)
            return ToolResult.fail("get_recent_mnemonics", str(exc))
