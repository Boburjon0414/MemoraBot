"""AIPlanner: orchestrates tool execution before AI generation.

The planner is the intelligence layer between the user's message and the AI
model. Its only job is orchestration — it never generates text.

Responsibilities
----------------
1. Analyse the user's message to determine intent and required data.
2. Select which tools to run from the registry.
3. Execute selected tools in parallel (where safe) via ToolRegistry.
4. Merge ToolResults into the AIContext for PromptBuilder.
5. Return the enriched AIContext and a plan trace (for logging/debug).

Design
------
The planner uses a keyword/pattern-based intent detector to select tools.
This is deliberately simple and fast — no LLM call, no NLP library,
no added latency. It matches common temporal and topical patterns:

  "last week" / "recently" / "this week"  → vocabulary and activity tools
  "quiz" / "test me"                       → quiz output tools + weak words
  "flashcard" / "flash card"               → flashcard output tools
  "document" / "pdf" / "uploaded"          → document tools
  "summary" / "summari"                    → summary output tools
  "presentation" / "slide"                 → presentation output tools
  "statistics" / "progress" / "streak"     → statistics tools
  "word" / "vocabulary" / "searched"       → vocabulary tools
  "level" / "CEFR" / "B2"                 → user profile tools

For any message that doesn't match a specific pattern, the planner runs
a default minimal tool set (user profile + recent words) so the AI always
has at least basic context.

Provider independence
---------------------
The planner knows nothing about Gemini, Groq, or any other model. It only
calls ToolRegistry.execute() and constructs AIContext. PromptBuilder and
AIRouter handle model-specific concerns downstream.

PlanTrace
---------
Every plan execution produces a PlanTrace recording which tools were selected,
which succeeded, which failed, and what data was retrieved. This is purely
for logging and debugging — it is never sent to the AI model.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.context.context_builder import AIContext, ContextPolicy
from app.services.context.user_context import UserContext
from app.services.tools.base import ToolContext, ToolResult
from app.services.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


# ── Intent detection patterns ──────────────────────────────────────────── #

_TEMPORAL = re.compile(
    r"\b(last week|this week|yesterday|today|recently|last month|"
    r"this month|last \d+ days?|past \d+ days?)\b",
    re.IGNORECASE,
)
_QUIZ = re.compile(r"\b(quiz|test me|test my|practice test|multiple.choice|gap.fill)\b", re.IGNORECASE)
_FLASHCARD = re.compile(r"\b(flashcard|flash card|study card|review card)\b", re.IGNORECASE)
_DOCUMENT = re.compile(r"\b(document|pdf|uploaded|file|text i uploaded|my notes?)\b", re.IGNORECASE)
_SUMMARY = re.compile(r"\b(summar|summarise|summarize)\b", re.IGNORECASE)
_PRESENTATION = re.compile(r"\b(presentation|slide|slides|deck)\b", re.IGNORECASE)
_STATS = re.compile(r"\b(statistic|progress|streak|how many|how much|how long|dashboard)\b", re.IGNORECASE)
_VOCAB = re.compile(r"\b(word|vocabulary|vocab|searched|looked up|mnemonic)\b", re.IGNORECASE)
_PROFILE = re.compile(r"\b(my level|cefr|english level|learning goal|my goal|weak|weakness)\b", re.IGNORECASE)
_CONTINUE = re.compile(r"\b(continue|resume|last time|previous|yesterday|again)\b", re.IGNORECASE)


@dataclass
class PlanTrace:
    """Records what the planner decided and what happened.

    Never sent to the AI — only for logging and debugging.
    """
    message: str
    selected_tools: list[str] = field(default_factory=list)
    succeeded: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    tool_data: dict[str, Any] = field(default_factory=dict)

    def log(self) -> None:
        logger.debug(
            "AIPlanner: tools=%s succeeded=%s failed=%s data_keys=%s",
            self.selected_tools,
            self.succeeded,
            self.failed,
            list(self.tool_data.keys()),
        )


class AIPlanner:
    """Selects and executes platform tools, returning an enriched AIContext.

    Constructed per-request by ServicesMiddleware and injected as
    `data["ai_planner"]`. AI-powered handlers call
    `await planner.plan(message, user_context, tool_context, feature)`.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def plan(
        self,
        message: str,
        user_context: UserContext,
        tool_context: ToolContext,
        feature: str = "chat",
    ) -> tuple[AIContext, PlanTrace]:
        """Analyse `message`, execute needed tools, return enriched AIContext.

        Args:
            message:      The raw user message to analyse.
            user_context: Pre-built by UserContextService.
            tool_context: Session-scoped repositories for tool execution.
            feature:      Which feature is calling ('chat', 'quiz', etc.)

        Returns:
            (AIContext, PlanTrace) — AIContext is populated with tool results;
            PlanTrace records what happened for logging.
        """
        trace = PlanTrace(message=message)

        # Select tools based on intent detection
        tool_names = self._select_tools(message, feature)
        trace.selected_tools = tool_names

        # Execute all selected tools — concurrently where safe
        results = await self._execute_all(tool_names, tool_context)

        # Record success/failure
        for name, result in results.items():
            if result.success:
                trace.succeeded.append(name)
                trace.tool_data.update(result.data)
            else:
                trace.failed.append(name)
                logger.warning("AIPlanner: tool %r failed — %s", name, result.error)

        trace.log()

        # Merge results into AIContext
        ai_context = self._build_context(user_context, trace.tool_data)
        return ai_context, trace

    # ── Intent detection ───────────────────────────────────────────────── #

    def _select_tools(self, message: str, feature: str) -> list[str]:
        """Return a deduplicated, ordered list of tool names to execute.

        Always includes user profile and streak as a baseline.
        Adds domain-specific tools based on message patterns.
        """
        tools: list[str] = []

        # Baseline — always run for any AI request
        tools.extend(["get_user_profile", "get_streak"])

        # Temporal reference → recent vocabulary and activity
        if _TEMPORAL.search(message) or _VOCAB.search(message):
            tools.append("get_recent_words")
            tools.append("get_recent_activity")

        # Quiz intent — always pull rich vocabulary data for adaptive quizzing
        if _QUIZ.search(message) or feature == "quiz":
            tools.extend([
                "get_vocabulary_quiz_words",   # primary vocabulary source (Feature C.1)
                "get_recent_words",
                "get_weak_words",
                "get_recent_quizzes",
            ])

        # Flashcard intent
        if _FLASHCARD.search(message):
            tools.extend(["get_recent_words", "get_saved_words", "get_recent_flashcards"])

        # Document/RAG intent
        if _DOCUMENT.search(message):
            tools.extend(["get_uploaded_documents", "get_recent_document"])
            if "search" in message.lower() or "find" in message.lower() or "about" in message.lower():
                tools.append("search_document_chunks")

        # Summary intent
        if _SUMMARY.search(message):
            tools.extend(["get_recent_summaries", "get_uploaded_documents"])

        # Presentation intent
        if _PRESENTATION.search(message):
            tools.extend(["get_recent_presentations", "get_uploaded_documents"])

        # Statistics / progress intent
        if _STATS.search(message):
            tools.append("get_learning_statistics")

        # Continue/resume intent — fetch recent artifacts in all categories
        if _CONTINUE.search(message):
            tools.extend([
                "get_recent_quizzes", "get_recent_flashcards",
                "get_recent_summaries", "get_recent_presentations",
                "get_recent_chat_sessions",
            ])

        # Profile / level / weakness intent
        if _PROFILE.search(message):
            tools.extend(["get_weak_words"])

        # Deduplicate preserving order, and filter to feature-available tools
        available = {t.definition.name for t in self._registry.list_for_feature(feature)}
        seen: set[str] = set()
        filtered: list[str] = []
        for t in tools:
            if t not in seen and t in available:
                seen.add(t)
                filtered.append(t)
        return filtered

    # ── Tool execution ─────────────────────────────────────────────────── #

    async def _execute_all(
        self,
        tool_names: list[str],
        tool_context: ToolContext,
    ) -> dict[str, ToolResult]:
        """Execute all tools concurrently.

        Tools that don't have parameters are safe to run in parallel
        (all are read-only). We gather all coroutines in one asyncio.gather().
        """
        if not tool_names:
            return {}

        tasks = {
            name: self._registry.execute(name, tool_context)
            for name in tool_names
        }

        results_list = await asyncio.gather(*tasks.values(), return_exceptions=True)
        results: dict[str, ToolResult] = {}

        for name, result in zip(tasks.keys(), results_list):
            if isinstance(result, Exception):
                results[name] = ToolResult.fail(name, str(result))
            elif isinstance(result, ToolResult):
                results[name] = result
            else:
                results[name] = ToolResult.fail(name, "Unexpected return type from tool.")

        return results

    # ── Context assembly ───────────────────────────────────────────────── #

    def _build_context(
        self,
        user_context: UserContext,
        tool_data: dict[str, Any],
    ) -> AIContext:
        """Merge tool data into an AIContext value object.

        Only fields present in tool_data are populated. Missing fields
        fall back to the defaults from UserContext or empty lists —
        never fabricated values.
        """
        # User profile enrichment
        english_level = tool_data.get("english_level") or user_context.english_level
        learning_goal = tool_data.get("learning_goal") or user_context.learning_goal
        native_language = tool_data.get("native_language") or user_context.native_language
        active_topic = tool_data.get("active_topic") or user_context.active_topic
        weak_words_from_tool = tool_data.get("weak_words") or user_context.recent_weak_words

        # Build enriched UserContext (create a new frozen instance)
        from dataclasses import replace as dc_replace
        enriched_uc = UserContext(
            user_id=user_context.user_id,
            preferred_language=user_context.preferred_language,
            is_premium=user_context.is_premium,
            english_level=english_level,
            learning_goal=learning_goal,
            native_language=native_language,
            vocabulary_size=tool_data.get("vocabulary_size", user_context.vocabulary_size),
            current_streak_days=tool_data.get("current_streak", user_context.current_streak_days),
            best_streak_days=tool_data.get("best_streak", user_context.best_streak_days),
            recent_weak_words=weak_words_from_tool,
            active_topic=active_topic,
        )

        # Vocabulary history — prefer rich quiz-words data when available
        vocab_words_rich = tool_data.get("vocab_words", [])
        recent_words = (
            [entry["word"] for entry in vocab_words_rich if "word" in entry]
            if vocab_words_rich
            else tool_data.get("words", [])
        )

        # Platform artifacts
        recent_quiz_topics = tool_data.get("quizzes", [])
        recent_flashcard_topics = tool_data.get("flashcard_sets", [])
        recent_summary_titles = tool_data.get("summaries", [])

        # Activity
        activity_this_week = tool_data.get("activity", {})

        # Documents
        docs = tool_data.get("documents", [])
        document_titles = [d["title"] for d in docs if isinstance(d, dict) and "title" in d]

        # Semantic search results — stored separately in context
        search_chunks = tool_data.get("chunks", [])

        return AIContext(
            user_context=enriched_uc,
            recent_words_week=recent_words,
            recent_words_today=[],   # planner doesn't distinguish today vs week
            weak_words=weak_words_from_tool,
            recent_quiz_topics=recent_quiz_topics,
            recent_flashcard_topics=recent_flashcard_topics,
            recent_summary_titles=recent_summary_titles,
            activity_this_week=activity_this_week,
            document_titles=document_titles,
            search_chunks=search_chunks,
        )
