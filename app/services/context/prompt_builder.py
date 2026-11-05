"""PromptBuilder: constructs AI system prompts strictly from `AIContext`.

AI Safety Rules (enforced here)
---------------------------------
1. A section is only included if the underlying data actually exists.
2. No placeholder text like "English Level: Unknown" or "No documents yet".
3. No fabricated history, invented quiz results, or assumed documents.
4. Every injected value comes directly from the AIContext fields — which
   themselves come only from the database (via ContextBuilder).

Design pattern
--------------
`build_system_prompt()` iterates over a list of section builders.  Each
section builder checks whether its data is present and either returns a
formatted string or returns None.  Sections that return None are silently
omitted — the AI simply doesn't see that section, which is safer than
seeing "Unknown" or an empty bullet list.

This means the system prompt is always:
  - Minimal when the user is new (only the persona + language + rules)
  - Rich when the user has history (level, goal, weak words, recent vocab,
    previous quizzes, uploaded documents — all grounded in real data)

Temporal language
-----------------
The prompt includes natural temporal references ("this week", "today") only
when the corresponding data is non-empty.  This allows the AI to answer:
  "What did I search today?"  → uses recent_words_today
  "Quiz me on last week's words" → uses recent_words_week
  "Continue my previous quiz"    → uses recent_quiz_topics

Feature persona variants
------------------------
`build_system_prompt()` accepts a `feature` string that selects a persona
prefix appropriate for the calling feature (chat, quiz, flashcards, etc.).
The rest of the prompt assembly is shared — one code path for all features.
"""

from __future__ import annotations

from app.services.context.context_builder import AIContext

# ── Persona prefixes per feature ───────────────────────────────────────── #

_PERSONAS: dict[str, str] = {
    "chat": (
        "You are MemoraBot's AI Learning Assistant — a knowledgeable, encouraging personal tutor "
        "specialising in English language learning, vocabulary acquisition, grammar, and exam preparation. "
        "You have access to this learner's full platform history and must use it to give personalised, "
        "grounded responses. You never invent history, documents, or quiz results."
    ),
    "quiz": (
        "You are MemoraBot's Quiz Generator. Generate high-quality quiz questions "
        "based strictly on the learner's vocabulary history and stated weak areas. "
        "Never invent words the user has not encountered. "
        "Return valid JSON only — no preamble, no markdown fences."
    ),
    "flashcards": (
        "You are MemoraBot's Flashcard Generator. Create concise, memorable flashcards "
        "from the learner's saved vocabulary and stated learning goals. "
        "Return valid JSON only — no preamble, no markdown fences."
    ),
    "summary": (
        "You are MemoraBot's Summarisation Engine. Summarise the provided content "
        "into clear, structured bullet points tailored to the learner's level. "
        "Return valid JSON only — no preamble, no markdown fences."
    ),
    "presentation": (
        "You are MemoraBot's Presentation Outline Generator. Create structured, "
        "learner-appropriate slide outlines from the provided content. "
        "Return valid JSON only — no preamble, no markdown fences."
    ),
    "grammar_chat": (
        "You are MemoraBot's Grammar Tutor — a patient, encouraging English grammar expert. "
        "The learner is currently studying the grammar topic listed in CURRENT GRAMMAR LESSON. "
        "Answer grammar questions using that lesson as grounding. "
        "Use Telegram HTML formatting: <b>bold</b>, <i>italic</i>, <code>code</code>. "
        "NEVER use Markdown like **bold** or *italic*. "
        "Keep answers concise (max 5 sentences or 3 bullet points). "
        "Adapt difficulty to the learner's CEFR level. "
        "Never invent grammar rules — only explain correct English."
    ),
    "grammar_quiz": (
        "You are MemoraBot's Grammar Quiz Generator. "
        "Generate grammar questions ONLY about the topic in CURRENT GRAMMAR LESSON. "
        "Do NOT test other grammar topics unless explicitly required by the current topic. "
        "Return valid JSON only — no preamble, no markdown fences."
    ),
}

_DEFAULT_PERSONA = _PERSONAS["chat"]

# ── Core behaviour rules ───────────────────────────────────────────────── #

_BEHAVIOUR_RULES = """\
RESPONSE RULES:
- Respond in the same language the user writes in (English, Uzbek, or Russian).
- Never start a reply with "I", "Sure", "Of course", "Certainly", "Absolutely", or "Great".
- Never claim documents exist unless they appear in UPLOADED DOCUMENTS below.
- Never claim quiz history exists unless it appears in QUIZ HISTORY below.
- Never claim a CEFR level unless it appears in USER PROFILE below.
- If the user references something not in this context, politely ask them to clarify.
- Be direct and informative. No hollow affirmations.
- Keep responses concise (2–4 paragraphs) unless the user explicitly asks for more.\
"""


class PromptBuilder:
    """Assembles AI system prompts from an `AIContext` instance.

    Stateless — safe to instantiate once and reuse across requests.
    """

    def build_system_prompt(
        self,
        context: AIContext,
        *,
        feature: str = "chat",
    ) -> str:
        """Build a complete system prompt from `context`.

        Only includes sections whose underlying data is non-empty.
        Sections are separated by double newlines for readability.

        Args:
            context: The fully assembled AIContext from ContextBuilder.
            feature: Which persona to use ('chat', 'quiz', 'flashcards',
                     'summary', 'presentation'). Defaults to 'chat'.

        Returns:
            A complete system prompt string ready for AIRequest.system_prompt.
        """
        persona = _PERSONAS.get(feature, _DEFAULT_PERSONA)
        sections: list[str] = [persona]

        # Each builder returns a string or None
        builders = [
            self._build_grammar_lesson,         # grammar context first (highest relevance)
            self._build_user_profile,
            self._build_learning_history,
            self._build_platform_artifacts,
            self._build_activity_timeline,
            self._build_uploaded_documents,
            self._build_search_results,
            self._build_behaviour_rules,
        ]

        for builder in builders:
            section = builder(context)
            if section:
                sections.append(section)

        return "\n\n".join(sections)

    # ── Section builders ───────────────────────────────────────────────── #

    def _build_user_profile(self, ctx: AIContext) -> str | None:
        """USER PROFILE section — only includes fields that are non-None."""
        uc = ctx.user_context
        lines: list[str] = []

        if uc.english_level:
            lines.append(f"English level: {uc.english_level} (CEFR)")
        if uc.learning_goal:
            lines.append(f"Learning goal: {uc.learning_goal}")
        if uc.native_language:
            lines.append(f"Native language: {uc.native_language}")
        if uc.vocabulary_size > 0:
            lines.append(f"Saved vocabulary: {uc.vocabulary_size} words")
        if uc.current_streak_days > 0:
            lines.append(f"Study streak: {uc.current_streak_days} days")
        if uc.active_topic:
            lines.append(f"Current study topic: {uc.active_topic}")
        if ctx.weak_words:
            lines.append(f"Struggling with: {', '.join(ctx.weak_words[:8])}")

        if not lines:
            return None

        return "USER PROFILE:\n" + "\n".join(f"- {line}" for line in lines)

    def _build_learning_history(self, ctx: AIContext) -> str | None:
        """VOCABULARY HISTORY section — only when data is non-empty."""
        lines: list[str] = []

        if ctx.recent_words_today:
            words = ", ".join(ctx.recent_words_today[:10])
            lines.append(f"Looked up today: {words}")

        if ctx.recent_words_week:
            # Exclude today's words to avoid repetition
            today_set = set(ctx.recent_words_today)
            week_only = [w for w in ctx.recent_words_week if w not in today_set][:15]
            if week_only:
                lines.append(f"Looked up this week: {', '.join(week_only)}")

        if not lines:
            return None

        return "VOCABULARY HISTORY:\n" + "\n".join(f"- {line}" for line in lines)

    def _build_platform_artifacts(self, ctx: AIContext) -> str | None:
        """PREVIOUS AI CONTENT section — quizzes, flashcards, summaries."""
        lines: list[str] = []

        if ctx.recent_quiz_topics:
            topics = ", ".join(ctx.recent_quiz_topics)
            lines.append(f"Recent quizzes on: {topics}")

        if ctx.recent_flashcard_topics:
            topics = ", ".join(ctx.recent_flashcard_topics)
            lines.append(f"Recent flashcard sets on: {topics}")

        if ctx.recent_summary_titles:
            titles = ", ".join(ctx.recent_summary_titles)
            lines.append(f"Recent summaries: {titles}")

        if not lines:
            return None

        return "PREVIOUS AI CONTENT:\n" + "\n".join(f"- {line}" for line in lines)

    def _build_activity_timeline(self, ctx: AIContext) -> str | None:
        """ACTIVITY THIS WEEK section — human-readable counts."""
        if not ctx.activity_this_week:
            return None

        # Map ActivityType values to readable labels
        _labels = {
            "mnemonic_generated": "vocabulary lookups",
            "vocabulary_saved": "words saved",
            "quiz_answered": "quiz answers",
            "flashcard_reviewed": "flashcard reviews",
            "ai_chat_message": "AI chat messages",
            "document_uploaded": "documents uploaded",
        }

        lines: list[str] = []
        for activity_type, count in sorted(
            ctx.activity_this_week.items(), key=lambda x: x[1], reverse=True
        ):
            label = _labels.get(activity_type, activity_type.replace("_", " "))
            lines.append(f"{count} {label}")

        if not lines:
            return None

        return "ACTIVITY THIS WEEK:\n" + "\n".join(f"- {line}" for line in lines)

    def _build_uploaded_documents(self, ctx: AIContext) -> str | None:
        """UPLOADED DOCUMENTS section — only when docs exist."""
        if not ctx.document_titles:
            return None

        lines = [f'"{title}"' for title in ctx.document_titles[:8]]
        return "UPLOADED DOCUMENTS:\n" + "\n".join(f"- {line}" for line in lines)

    def _build_grammar_lesson(self, ctx: AIContext) -> str | None:
        """CURRENT GRAMMAR LESSON section — injected when in a grammar session.

        Appears first in the prompt so the AI knows what topic to focus on
        before seeing vocabulary history or other context.  Only emitted when
        a grammar session is active (current_grammar_topic is set).
        """
        if not ctx.current_grammar_topic:
            return None
        lines = [f"Topic: {ctx.current_grammar_topic}"]
        if ctx.current_grammar_description:
            lines.append(f"Description: {ctx.current_grammar_description}")
        if ctx.recent_grammar_topics:
            lines.append(f"User has also studied: {', '.join(ctx.recent_grammar_topics[:5])}")
        return "CURRENT GRAMMAR LESSON:\n" + "\n".join(f"- {line}" for line in lines)

    def _build_search_results(self, ctx: AIContext) -> str | None:
        """RELEVANT DOCUMENT PASSAGES section — when semantic search was run."""
        if not ctx.search_chunks:
            return None
        lines = []
        for i, chunk in enumerate(ctx.search_chunks[:5], 1):
            text = chunk.get("text", "")[:400]
            score = chunk.get("score", 0)
            page = chunk.get("page_number")
            citation = f" (page {page})" if page else ""
            lines.append(f"[{i}]{citation} {text}")
        return "RELEVANT DOCUMENT PASSAGES:\n" + "\n\n".join(lines)

    def _build_behaviour_rules(self, ctx: AIContext) -> str | None:
        """Always include the behaviour rules — never None."""
        return _BEHAVIOUR_RULES
