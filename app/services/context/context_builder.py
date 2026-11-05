"""ContextBuilder: the single service responsible for assembling complete
AI context from the database before any AI call is made.

Architecture rationale
----------------------
Before this service existed, every AI feature (AIChatService, QuizService,
etc.) independently queried whatever data it needed: UserContext gave it the
profile, and then it hand-assembled a system prompt. This works for one
feature but breaks down at scale:

  - A chat message like "Create flashcards from my previous summaries" needs
    to look up FeatureOutput rows.  AIChatService doesn't know about that.
  - "Quiz me on words I searched this week" needs LearningActivity history.
    QuizService doesn't know about that.
  - Every feature duplicates the same DB-querying boilerplate.
  - There's no single place to enforce the AI Safety Rules (never invent
    history, never hallucinate documents, never fabricate quiz results).

ContextBuilder solves this by being the ONLY service that touches the DB
for context-gathering purposes.  It returns an `AIContext` value object
that every AI feature receives.  The feature then passes `AIContext` to
`PromptBuilder` which assembles the actual prompt text.

Feature context policies
------------------------
Each AI feature declares which context slices it needs via a `ContextPolicy`
dataclass.  ContextBuilder only queries what is declared — this avoids
injecting irrelevant data (e.g. a quiz request doesn't need chat history,
and a vocabulary flashcard request doesn't need document chunks).

AI Safety Rules (enforced here)
---------------------------------
  - Never include a section in context if the underlying data is empty.
  - Never invent vocabulary, quiz results, documents, CEFR level, or goals.
  - If data is unavailable, the context section is simply absent.
  - PromptBuilder reads only what ContextBuilder provides — it cannot
    fabricate something that isn't in AIContext.

Lookup windows
--------------
  WEEK_DAYS  = 7   days — "recently", "this week"
  TODAY_DAYS = 1   day  — "today"
  MONTH_DAYS = 30  days — "last month", broader history
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC

from app.database.models.feature_output import OutputType
from app.database.models.learning_activity import ActivityType
from app.repositories.activity_repository import ActivityRepository
from app.repositories.feature_output_repository import FeatureOutputRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.services.context.user_context import UserContext
from app.services.outputs.schemas import (
    ChatSessionPayload,
    FlashcardPayload,
    QuizPayload,
    SummaryPayload,
)

logger = logging.getLogger(__name__)

WEEK_DAYS = 7
TODAY_DAYS = 1
MONTH_DAYS = 30


# ── Context policy ─────────────────────────────────────────────────────── #

@dataclass
class ContextPolicy:
    """Declares which context slices a feature needs.

    Only slices marked True are queried — avoids unnecessary DB calls and
    keeps the context window focused on relevant information.
    """
    include_recent_vocabulary: bool = False   # words searched this week
    include_weak_words: bool = False          # words answered wrong in quizzes
    include_recent_quizzes: bool = False      # last N quiz outputs
    include_recent_flashcards: bool = False   # last N flashcard outputs
    include_recent_summaries: bool = False    # last N summary outputs
    include_recent_chats: bool = False        # last N chat session titles
    include_activity_timeline: bool = False   # high-level activity counts
    include_document_titles: bool = False     # names of uploaded ContentSources
    include_grammar_progress: bool = False    # studied grammar topics + mastery
    current_grammar_topic_id: int | None = None  # active lesson topic_id for grammar Q&A

    # Pre-built policies for each feature
    @classmethod
    def for_chat(cls) -> "ContextPolicy":
        return cls(
            include_recent_vocabulary=True,
            include_weak_words=True,
            include_recent_quizzes=True,
            include_recent_flashcards=True,
            include_recent_summaries=True,
            include_recent_chats=False,   # we already have the session
            include_activity_timeline=True,
            include_document_titles=True,
        )

    @classmethod
    def for_quiz(cls) -> "ContextPolicy":
        return cls(
            include_recent_vocabulary=True,
            include_weak_words=True,
            include_recent_quizzes=True,
            include_activity_timeline=False,
        )

    @classmethod
    def for_flashcards(cls) -> "ContextPolicy":
        return cls(
            include_recent_vocabulary=True,
            include_recent_flashcards=True,
        )

    @classmethod
    def for_summary(cls) -> "ContextPolicy":
        return cls(
            include_recent_summaries=True,
            include_document_titles=True,
        )

    @classmethod
    def for_presentation(cls) -> "ContextPolicy":
        return cls(
            include_recent_summaries=True,
            include_document_titles=True,
        )

    @classmethod
    def for_grammar_chat(cls, current_topic_id: int | None = None) -> "ContextPolicy":
        """Grammar Q&A: include studied topics + active lesson context."""
        return cls(
            include_recent_vocabulary=True,
            include_weak_words=True,
            include_grammar_progress=True,
            current_grammar_topic_id=current_topic_id,
        )

    @classmethod
    def for_grammar_quiz(cls, current_topic_id: int | None = None) -> "ContextPolicy":
        """Grammar quiz generation: include grammar progress + vocabulary."""
        return cls(
            include_recent_vocabulary=True,
            include_weak_words=True,
            include_grammar_progress=True,
            current_grammar_topic_id=current_topic_id,
        )

    @classmethod
    def minimal(cls) -> "ContextPolicy":
        """No additional context beyond UserContext — fast for simple queries."""
        return cls()


# ── AIContext value object ─────────────────────────────────────────────── #

@dataclass(frozen=True)
class AIContext:
    """Complete, database-grounded context for one AI request.

    Every field is populated strictly from database queries.  Fields that
    have no data are empty lists or None — never fabricated placeholders.

    PromptBuilder reads this object to assemble the system prompt; it
    cannot add information that isn't present here.
    """
    # ── Who the user is ────────────────────────────────────────────────── #
    user_context: UserContext           # profile: level, goal, streak, vocab size

    # ── What they've been learning ─────────────────────────────────────── #
    recent_words_week: list[str] = field(default_factory=list)
    # Words the user looked up in the last 7 days. Source: LearningActivity.

    recent_words_today: list[str] = field(default_factory=list)
    # Words looked up today. Subset of recent_words_week.

    weak_words: list[str] = field(default_factory=list)
    # Words the user answered incorrectly in quizzes. Source: UserMemory.

    # ── Previous AI-generated content ─────────────────────────────────── #
    recent_quiz_topics: list[str] = field(default_factory=list)
    # Topics of the last N quizzes. Source: FeatureOutput.

    recent_flashcard_topics: list[str] = field(default_factory=list)
    # Topics of the last N flashcard sets. Source: FeatureOutput.

    recent_summary_titles: list[str] = field(default_factory=list)
    # Titles of the last N summaries. Source: FeatureOutput.

    # ── Platform activity ──────────────────────────────────────────────── #
    activity_this_week: dict[str, int] = field(default_factory=dict)
    # {activity_type: count} for the last 7 days. Source: LearningActivity.

    # ── Uploaded documents ─────────────────────────────────────────────── #
    document_titles: list[str] = field(default_factory=list)
    # Titles of ContentSources in "ready" status. Source: content_sources.

    # ── Semantic search results (from search_document_chunks tool) ─────── #
    search_chunks: list[dict] = field(default_factory=list)
    # List of dicts: {text, score, document_id, chunk_index, page_number}
    # Populated by the planner when document search is triggered.

    # ── Grammar Learning context (Feature: Learn → Grammar) ────────────── #
    current_grammar_topic: str | None = None
    # Title of the grammar topic currently being studied (e.g. "Present Perfect").
    # Set from FSM state when the user is in a grammar session.

    current_grammar_topic_id: int | None = None
    # GrammarTopic.id of the current lesson; None when not in a grammar session.

    current_grammar_description: str | None = None
    # Topic description injected from GrammarTopic.description — grounds AI answers.

    grammar_progress: list[dict] = field(default_factory=list)
    # List of studied topics: [{title, status, mastery_score, questions_answered}]
    # Only topics the user has actually opened a lesson for.

    recent_grammar_topics: list[str] = field(default_factory=list)
    # Titles of the N most recently studied grammar topics (for prompt context).


# ── ContextBuilder service ─────────────────────────────────────────────── #

class ContextBuilder:
    """Gathers complete AI context from the database for one user.

    This is the only service that performs multi-table context assembly.
    All other AI-facing services (AIChatService, QuizService, etc.) receive
    a finished `AIContext` and pass it to `PromptBuilder` — they never
    query the DB for context themselves.

    Constructed per-request by ServicesMiddleware; all repository dependencies
    are session-scoped.
    """

    def __init__(
        self,
        activity_repo: ActivityRepository,
        feature_output_repo: FeatureOutputRepository,
        vocabulary_repo: VocabularyRepository,
    ) -> None:
        self._activity_repo = activity_repo
        self._output_repo = feature_output_repo
        self._vocabulary_repo = vocabulary_repo

    async def build(
        self,
        user_context: UserContext,
        policy: ContextPolicy,
    ) -> AIContext:
        """Assemble an `AIContext` for `user_context.user_id` under `policy`.

        Every query is independently guarded — a failure in one slice does
        not prevent the others from being assembled. Failures are logged as
        warnings; the slice defaults to its empty value.

        Args:
            user_context: Pre-built by UserContextService. ContextBuilder
                          does NOT rebuild it — it extends it.
            policy:       Declares which slices to query.

        Returns:
            An immutable `AIContext` with only the requested slices populated.
        """
        uid = user_context.user_id
        now = datetime.now(UTC).replace(tzinfo=None)
        week_ago = now - timedelta(days=WEEK_DAYS)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Collect slices concurrently where possible
        recent_words_week: list[str] = []
        recent_words_today: list[str] = []
        weak_words: list[str] = list(user_context.recent_weak_words)
        recent_quiz_topics: list[str] = []
        recent_flashcard_topics: list[str] = []
        recent_summary_titles: list[str] = []
        activity_this_week: dict[str, int] = {}
        document_titles: list[str] = []

        if policy.include_recent_vocabulary:
            try:
                recent_words_week = await self._activity_repo.get_recent_mnemonic_words(
                    uid, since=week_ago, limit=30
                )
                recent_words_today = await self._activity_repo.get_recent_mnemonic_words(
                    uid, since=today_start, limit=15
                )
            except Exception:
                logger.warning("ContextBuilder: failed to fetch recent vocabulary uid=%s", uid, exc_info=True)

        if policy.include_recent_quizzes:
            try:
                quiz_rows = await self._output_repo.get_recent_by_type(
                    uid, OutputType.QUIZ.value, limit=5
                )
                for row in quiz_rows:
                    topic = _extract_topic_from_output(row.payload_json)
                    if topic:
                        recent_quiz_topics.append(topic)
            except Exception:
                logger.warning("ContextBuilder: failed to fetch quiz history uid=%s", uid, exc_info=True)

        if policy.include_recent_flashcards:
            try:
                fc_rows = await self._output_repo.get_recent_by_type(
                    uid, OutputType.FLASHCARD_SET.value, limit=5
                )
                for row in fc_rows:
                    topic = _extract_topic_from_output(row.payload_json)
                    if topic:
                        recent_flashcard_topics.append(topic)
            except Exception:
                logger.warning("ContextBuilder: failed to fetch flashcard history uid=%s", uid, exc_info=True)

        if policy.include_recent_summaries:
            try:
                sum_rows = await self._output_repo.get_recent_by_type(
                    uid, OutputType.SUMMARY.value, limit=5
                )
                for row in sum_rows:
                    title = row.title or _extract_topic_from_output(row.payload_json)
                    if title:
                        recent_summary_titles.append(title)
            except Exception:
                logger.warning("ContextBuilder: failed to fetch summary history uid=%s", uid, exc_info=True)

        if policy.include_activity_timeline:
            try:
                activity_this_week = await self._activity_repo.get_summary(
                    uid, since=week_ago
                )
            except Exception:
                logger.warning("ContextBuilder: failed to fetch activity summary uid=%s", uid, exc_info=True)

        if policy.include_document_titles:
            try:
                document_titles = await self._get_document_titles(uid)
            except Exception:
                logger.warning("ContextBuilder: failed to fetch document titles uid=%s", uid, exc_info=True)

        return AIContext(
            user_context=user_context,
            recent_words_week=recent_words_week,
            recent_words_today=recent_words_today,
            weak_words=weak_words,
            recent_quiz_topics=recent_quiz_topics,
            recent_flashcard_topics=recent_flashcard_topics,
            recent_summary_titles=recent_summary_titles,
            activity_this_week=activity_this_week,
            document_titles=document_titles,
        )

    async def _get_document_titles(self, user_id: int) -> list[str]:
        """Fetch titles of ready ContentSources for the user."""
        from sqlalchemy import select
        from app.database.models.content_source import ContentSource, ContentSourceStatus
        result = await self._activity_repo._session.execute(
            select(ContentSource.title)
            .where(ContentSource.user_id == user_id)
            .where(ContentSource.status == ContentSourceStatus.READY.value)
            .where(ContentSource.title.is_not(None))
            .order_by(ContentSource.created_at.desc())
            .limit(10)
        )
        return [row[0] for row in result.fetchall() if row[0]]


def _extract_topic_from_output(payload_json: str) -> str | None:
    """Extract a display topic/title from a raw payload_json string.

    Tries the 'topic' key first (quiz, flashcard), then 'title' (summary,
    presentation). Returns None on any parsing failure — never raises.
    """
    try:
        data = json.loads(payload_json)
        return data.get("topic") or data.get("title") or None
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None
