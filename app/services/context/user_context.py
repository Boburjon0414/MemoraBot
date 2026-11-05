"""The `UserContext` value object: an immutable per-request snapshot of
everything MemoraBot knows about a learner's profile.

Design rationale
----------------
Any AI feature that wants to personalise its response (chat, quiz
generation, RAG Q&A, mnemonic style selection) needs the same five or
six facts about the user: their UI language, their English level, their
learning goal, their current streak, how many words they've saved, and
which words they've recently struggled with.

Without a shared value object, every service would independently query
`user_settings`, `vocabulary_entries`, and `learning_activities` to
reconstruct those same facts for every request — N queries per feature
instead of one shared query.

`UserContext` is built once per request by `UserContextService` and
injected into handler data as `data["user_context"]`.  Services that need
it declare it as a constructor parameter; they never fetch it themselves.

Immutability (`frozen=True`)
----------------------------
The dataclass is frozen so it can be safely shared between services within
one request without risk of one service mutating state that another service
reads later.  All fields are plain Python types (str, int, list) with no
SQLAlchemy lazy-loading surprises.

`to_prompt_block()`
-------------------
Returns a concise natural-language paragraph that can be injected verbatim
into any AI system prompt as a `$user_context` template variable:

  "The learner prefers Uzbek. They are at B2 level, studying for IELTS.
   They have 47 words saved and are on a 5-day study streak.
   Recently struggled with: ephemeral, serendipity, ubiquitous."

This lets every AI feature benefit from personalisation without each one
knowing how to build the context string itself.

Current limitations (Step 2)
-----------------------------
  `english_level`, `learning_goal`, `native_language`, and
  `recent_weak_words` are populated with None / [] here because the
  `user_memory` table that stores them does not exist yet.  They are
  included in the dataclass now so that the AI prompt infrastructure
  (`to_prompt_block()`, future RAGService, AIChatService, QuizService)
  can reference them without needing changes in Step 8 when they become
  populated.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserContext:
    """An immutable, per-request snapshot of a learner's profile.

    All fields are populated by `UserContextService.build()` at the start
    of each request.  Fields that require the `user_memory` table (added in
    Step 8) default to None / empty list until that step ships.
    """

    # ── Identity ───────────────────────────────────────────────────────── #
    user_id: int

    # ── UI & language preferences (from user_settings) ─────────────────── #
    preferred_language: str          # "uz" | "en" | "ru"
    is_premium: bool

    # ── Learning profile (from user_memory — Step 8) ───────────────────── #
    english_level: str | None        # CEFR: "A1" | "A2" | "B1" | "B2" | "C1" | "C2"
    learning_goal: str | None        # "IELTS", "business English", "daily conversation", …
    native_language: str | None      # "uz", "ru", "tr", … (for mnemonic style hints)

    # ── Progress metrics (live data) ───────────────────────────────────── #
    vocabulary_size: int             # count of vocabulary_entries rows for this user
    current_streak_days: int         # consecutive calendar days with any activity
    best_streak_days: int            # all-time best streak

    # ── Adaptive data (from user_memory — Step 8) ──────────────────────── #
    recent_weak_words: list[str] = field(default_factory=list)
    # Words the user answered incorrectly in recent quiz sessions.
    # Used to steer mnemonic style and quiz difficulty.
    # Populated in Step 8; empty list until then.

    # ── Active topic (from user_memory — Step 8) ───────────────────────── #
    active_topic: str | None = None
    # The topic or category the user was most recently studying.
    # Used to prime AI chat context and quiz topic selection.

    # ─────────────────────────────────────────────────────────────────────── #

    def to_prompt_block(self) -> str:
        """Render the learning profile as a concise, injection-ready paragraph.

        The output is designed to be inserted into any AI system prompt as
        a `{user_context}` template slot.  It is intentionally brief —
        2–5 sentences — so it doesn't consume the context window.

        Returns a generic fallback string when no profile data is available,
        so callers never receive an empty string.

        Example output (fully populated)::

            "The learner prefers Uzbek. They are at B2 level, studying for
             IELTS. They have 47 words saved and are on a 5-day study streak.
             Recently struggled with: ephemeral, serendipity, ubiquitous."

        Example output (Step 2 — partially populated)::

            "The learner prefers Uzbek. They have 12 words saved and are on
             a 2-day study streak."
        """
        parts: list[str] = []

        # Language preference
        lang_display = {
            "uz": "Uzbek",
            "en": "English",
            "ru": "Russian",
        }.get(self.preferred_language, self.preferred_language)
        parts.append(f"The learner prefers {lang_display}.")

        # English level + learning goal (both optional until Step 8)
        if self.english_level and self.learning_goal:
            parts.append(
                f"They are at {self.english_level} level, studying for {self.learning_goal}."
            )
        elif self.english_level:
            parts.append(f"They are at {self.english_level} level.")
        elif self.learning_goal:
            parts.append(f"Their learning goal is: {self.learning_goal}.")

        # Progress
        progress_parts: list[str] = []
        if self.vocabulary_size > 0:
            progress_parts.append(f"{self.vocabulary_size} word{'s' if self.vocabulary_size != 1 else ''} saved")
        if self.current_streak_days > 0:
            progress_parts.append(
                f"on a {self.current_streak_days}-day study streak"
            )
        if progress_parts:
            parts.append(f"They have {', and '.join(progress_parts)}.")

        # Weak words (optional until Step 8)
        if self.recent_weak_words:
            word_list = ", ".join(self.recent_weak_words[:5])
            parts.append(f"Recently struggled with: {word_list}.")

        # Active topic (optional until Step 8)
        if self.active_topic:
            parts.append(f"Currently studying topic: {self.active_topic}.")

        if not parts:
            return "No learning profile available yet."

        return " ".join(parts)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<UserContext user_id={self.user_id} lang={self.preferred_language!r} "
            f"vocab={self.vocabulary_size} streak={self.current_streak_days}>"
        )
