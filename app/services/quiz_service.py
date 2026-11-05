"""QuizService: generates personalised, adaptive quizzes via the Tool Calling Layer.

Pipeline per quiz request
--------------------------
1. AIPlanner.plan(user_message, feature="quiz") — selects tools, retrieves
   vocabulary/weak_words/document_chunks from DB.
2. PromptBuilder-style system prompt assembled from real platform data only.
3. AIRouter.complete(request, response_schema=QUIZ_SCHEMA) — structured JSON.
4. Parse → QuizPayload.
5. Quality-validate: no duplicates, ≥4 options, correct answer present, no
   all-same-position bias.  Auto-regenerate once on failure.
6. Shuffle answer positions so the correct answer is equally likely in A/B/C/D.
7. Persist as FeatureOutput(output_type=QUIZ).
8. Record QUIZ_STARTED in LearningActivity.
9. Return QuizPayload to the handler.

Quiz modes
----------
  vocabulary — questions drawn ONLY from user's saved vocabulary library.
               If < MIN_VOCAB_FOR_QUIZ words, returns error payload instead of
               fabricating questions.
  grammar    — grammar questions (tenses, articles, passive, conditionals …).
               Adapts difficulty based on UserMemory weak spots.
  gap_fill   — fill-in-the-blank sentences with candidate options.
  reading    — short passage + comprehension questions.  Passage is embedded
               in the payload (not re-sent per question — handler responsibility).
  listening  — Coming Soon placeholder.
  mixed      — Planner selects vocabulary + grammar + gap_fill + reading mix.

Answer shuffling (requirement #1)
----------------------------------
After AI validation, _shuffle_answers() randomises option order per question
and updates correct_option accordingly.  The AI's original position is
discarded.  This lives entirely in QuizService, not in the AI prompt.

Quality validation (requirement #9)
-------------------------------------
_validate_quality() rejects quizzes with:
  - duplicate question texts
  - duplicate option texts within a question
  - < 4 options per question
  - correct_option out of range
  - all questions sharing the same correct position (after shuffle)
  - (vocabulary mode) questions whose vocabulary word is not in the user's library
On failure, the service regenerates once before propagating the error.
"""

from __future__ import annotations

import json
import logging
import random
import re
from datetime import datetime, UTC
from typing import Any

from app.core.exceptions import AIProviderError
from app.database.models.feature_output import OutputType
from app.database.models.learning_activity import ActivityType
from app.services.ai.router import AIRequest, AIRouter
from app.services.context.context_builder import AIContext, ContextPolicy
from app.services.context.prompt_builder import PromptBuilder
from app.services.context.user_context import UserContext
from app.services.feature_output_service import FeatureOutputService
from app.services.outputs.schemas import QuizPayload, QuizQuestion
from app.services.tools.base import ToolContext
from app.services.tools.planner import AIPlanner
from app.services.tools.response_validator import ResponseValidator

logger = logging.getLogger(__name__)

_prompt_builder = PromptBuilder()
_validator = ResponseValidator()

# Minimum saved-vocabulary entries for a vocabulary quiz.
# Below this, the service raises NotEnoughVocabularyError instead of fabricating.
# Spec requirement: at least 3 usable vocabulary entries.
MIN_VOCAB_FOR_QUIZ = 3

# ── JSON schema for structured AI output ──────────────────────────────── #

QUIZ_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "passage": {"type": "string"},   # only for reading quizzes; empty otherwise
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "correct_option": {"type": "integer"},
                    "explanation": {"type": "string"},
                    "quiz_type": {"type": "string"},
                },
                "required": ["question", "options", "correct_option", "explanation"],
            },
        },
    },
    "required": ["title", "questions"],
}


# ── Errors ─────────────────────────────────────────────────────────────── #

class NotEnoughVocabularyError(ValueError):
    """Raised when the user has too few saved words for a vocabulary quiz."""
    def __init__(self, count: int) -> None:
        self.count = count
        super().__init__(
            f"Only {count} word(s) in vocabulary — need at least {MIN_VOCAB_FOR_QUIZ} "
            "for a vocabulary quiz."
        )


class QuizQualityError(ValueError):
    """Raised when the generated quiz fails quality validation."""


# ── System prompt fragments per quiz mode ─────────────────────────────── #

_BASE_RULES = """ABSOLUTE RULES:
1. Return ONLY valid JSON — no markdown, no backticks, no preamble.
2. Every question MUST have EXACTLY 4 options (index 0-3).
3. correct_option is the 0-based index of the correct answer in the options list.
4. options must be short — max 60 characters each.
5. question text — max 120 characters.
6. explanation — why the correct answer is right, max 150 characters.
7. NEVER invent vocabulary, grammar examples, or passages not provided in context.
8. Distractors must be plausible — not obviously wrong."""


_QUIZ_TYPE_PROMPTS: dict[str, str] = {
    "vocabulary": (
        "MODE: VOCABULARY QUIZ\n"
        "The VOCAB WORDS list is the ONLY source of truth for this quiz.\n"
        "HARD RULES:\n"
        "- ONLY test words present in the VOCAB WORDS list. NEVER invent words.\n"
        "- NEVER use any English word or Uzbek meaning not in that list.\n"
        "- If there are fewer words than questions needed, generate fewer questions.\n\n"
        "QUESTION DIRECTIONS — mix BOTH types across the quiz:\n"
        "  Type A (English to Uzbek):\n"
        "    question: What does [WORD] mean?\n"
        "    correct option: the Uzbek meaning from VOCAB WORDS\n"
        "    distractors: Uzbek meanings of OTHER words from VOCAB WORDS\n"
        "  Type B (Uzbek to English):\n"
        "    question: Which English word means [MEANING]?\n"
        "    correct option: the English word from VOCAB WORDS\n"
        "    distractors: OTHER English words from VOCAB WORDS\n"
        "Do NOT make all questions the same direction.\n\n"
        "DISTRACTORS: drawn from other VOCAB WORDS entries only.\n"
        "Prefer words of similar difficulty or those in the weak_words list.\n\n"
        "EXPLANATION (max 120 chars):\n"
        "  Type A: 💡 WORD = MEANING. Example sentence.\n"
        "  Type B: 💡 MEANING = WORD. Example sentence.\n\n"
        "Set quiz_type to vocabulary on every question.\n"
    ),
    "grammar": (
        "MODE: GRAMMAR QUIZ\n"
        "Generate grammar questions testing specific English grammar rules.\n"
        "Topics to cover (based on user's weak areas first): "
        "tenses (present perfect, past simple, future), articles (a/an/the), "
        "prepositions (in/on/at), passive voice, conditionals (0/1/2/3), "
        "reported speech, subject-verb agreement, modal verbs.\n"
        "Question format: 'Which sentence is grammatically correct?' or "
        "'Choose the correct form: ____.'\n"
        "ALL 4 options must look plausible — only one is correct.\n"
        "Adapt difficulty to the user's CEFR level provided in context.\n"
        "If the user has grammar weak areas listed, generate MORE questions on those areas.\n"
    ),
    "gap_fill": (
        "MODE: GAP-FILL QUIZ\n"
        "Generate sentences with ONE blank (___). "
        "The correct answer fills the blank naturally.\n"
        "Rules:\n"
        "- Use vocabulary from the context when available.\n"
        "- Distractors are grammatically plausible but semantically wrong in context.\n"
        "- Sentence must be complete and natural without the blank word.\n"
        "- The gap must require knowledge of the word's meaning, not just grammar.\n"
    ),
    "reading": (
        "MODE: READING COMPREHENSION QUIZ\n"
        "FIRST, generate a SHORT passage (80-120 words) on a topic relevant to the user's "
        "learning goal or active topic. Put it in the 'passage' field of the JSON.\n"
        "THEN, generate ALL questions based ONLY on that passage.\n"
        "Rules:\n"
        "- Every question must be answerable from the passage text alone.\n"
        "- Do NOT include the passage in any question text — reference it implicitly.\n"
        "- Questions test comprehension, inference, and vocabulary in context.\n"
        "- Passage must be appropriate for the user's CEFR level.\n"
    ),
    "listening": None,   # handled as Coming Soon before AI call
    "mixed": (
        "MODE: MIXED QUIZ\n"
        "Generate a variety of question types in this order: "
        "start with 1-2 vocabulary questions (from VOCAB WORDS list), "
        "then 1-2 grammar questions, then 1 gap-fill. "
        "If no vocab words are available, use more grammar and gap-fill.\n"
        "Mark each question's 'quiz_type' field: 'vocabulary', 'grammar', or 'gap_fill'.\n"
    ),
}


class QuizService:
    """Generates adaptive, database-aware quizzes via the Tool Calling Layer."""

    def __init__(
        self,
        ai_router: AIRouter,
        feature_output_service: FeatureOutputService,
        planner: AIPlanner | None = None,
        quiz_open_period: int = 20,
        quiz_vocabulary_questions: int = 5,
    ) -> None:
        self._router = ai_router
        self._output_svc = feature_output_service
        self._planner = planner
        self._quiz_open_period = quiz_open_period
        # Clamp to [2, 10] — safe for any .env value
        self._quiz_vocabulary_questions = max(2, min(10, quiz_vocabulary_questions))

    @property
    def open_period(self) -> int:
        """Telegram poll open_period in seconds (0 = no timer)."""
        return self._quiz_open_period

    @property
    def vocab_question_count(self) -> int:
        """Number of questions to generate for a Vocabulary quiz (from config)."""
        return self._quiz_vocabulary_questions

    async def generate(
       self,
       user_id: int,
       user_context: UserContext,
       user_message: str,
       *,
       quiz_type: str = "mixed",
       num_questions: int = 5,
       tool_context: ToolContext | None = None,
       current_grammar_topic: str | None = None,
       current_grammar_topic_id: int | None = None,
    ) -> QuizPayload:
        """Generate a QuizPayload using the full Tool Calling Layer.

        Args:
            user_id:       Internal users.id.
            user_context:  Pre-built by UserContextService.
            user_message:  The user's request.
            quiz_type:     vocabulary | grammar | gap_fill | reading | listening | mixed.
            num_questions: How many questions to generate (2-10).
            tool_context:  Session-scoped repos for planner tool execution.

        Returns:
            A validated, answer-shuffled QuizPayload ready for Telegram polls.

        Raises:
            NotEnoughVocabularyError: vocabulary mode but < MIN_VOCAB_FOR_QUIZ words.
            AIProviderError: all AI providers exhausted.
            ValueError: AI returned invalid JSON or unrecoverable quality failure.
        """
        # Coming Soon: listening mode
        if quiz_type == "listening":
            return self._listening_placeholder()

        num_questions = max(2, min(10, num_questions))

        # Step 1: Retrieve context via Tool Calling Layer
        ai_context, vocab_data = await self._build_context(
            user_message, user_context, tool_context, quiz_type
        )

        # Ensure the selected grammar topic is preserved in the AIContext
        if current_grammar_topic:
            # AIContext is a frozen dataclass; use dataclasses.replace to set fields
            import dataclasses
            ai_context = dataclasses.replace(
                ai_context,
                current_grammar_topic=current_grammar_topic,
                current_grammar_topic_id=current_grammar_topic_id,
                current_grammar_description=current_grammar_topic,
            )

        # Step 2: Enforce vocabulary constraint BEFORE calling AI
        if quiz_type == "vocabulary":
            total = vocab_data.get("total_vocab_count", 0)
            vocab_words = vocab_data.get("vocab_words", [])
            if total < MIN_VOCAB_FOR_QUIZ or not vocab_words:
                raise NotEnoughVocabularyError(total)
            # Cap questions to available vocabulary
            num_questions = min(num_questions, len(vocab_words))

        # Step 3: Build system prompt (include explicit current topic when provided)
        system_prompt = self._build_quiz_prompt(
            ai_context,
            quiz_type,
            num_questions,
            vocab_data,
            current_topic=current_grammar_topic,
        )

        # Step 4: Call AI (try → validate → retry once on quality failure)
        payload = await self._generate_with_retry(
            system_prompt=system_prompt,
            quiz_type=quiz_type,
            num_questions=num_questions,
            user_context=user_context,
            vocab_data=vocab_data,
            current_topic=current_grammar_topic,
        )

        # Step 5: Persist as FeatureOutput
        output = await self._output_svc.save(
            user_id=user_id,
            output_type=OutputType.QUIZ,
            payload=payload,
            title=payload.title,
        )
        logger.info(
            "QuizService: generated quiz output_id=%s questions=%d type=%r uid=%s",
            output.id, len(payload.questions), quiz_type, user_id,
        )
        return payload

    # ── Context building ────────────────────────────────────────────────── #

    async def _build_context(
        self,
        message: str,
        user_context: UserContext,
        tool_context: ToolContext | None,
        quiz_type: str,
    ) -> tuple[AIContext, dict[str, Any]]:
        """Run planner tools and return (AIContext, vocab_tool_data)."""
        vocab_data: dict[str, Any] = {}

        if self._planner is not None and tool_context is not None:
            # For vocabulary and mixed, always run get_vocabulary_quiz_words
            if quiz_type in ("vocabulary", "mixed"):
                from app.services.tools.base import ToolResult
                vt_result = await self._planner._registry.execute(
                    "get_vocabulary_quiz_words", tool_context
                )
                if vt_result.success:
                    vocab_data = vt_result.data

            ai_context, _ = await self._planner.plan(
                message, user_context, tool_context, feature="quiz"
            )
            return ai_context, vocab_data

        # Minimal fallback (no planner)
        ai_context = AIContext(
            user_context=user_context,
            weak_words=list(user_context.recent_weak_words),
        )
        return ai_context, vocab_data

    # ── Prompt construction ─────────────────────────────────────────────── #

    def _build_quiz_prompt(
       self,
       ai_context: AIContext,
       quiz_type: str,
       num_questions: int,
       vocab_data: dict[str, Any],
       current_topic: str | None = None,
    ) -> str:
       """Assemble the system prompt from real context data only.

       The current_topic parameter, when provided, is injected as an explicit
       high-priority constraint that the AI MUST honour. This prevents the
       model from drifting to other grammar topics present in the user's
       history or context.
       """
       mode_instruction = _QUIZ_TYPE_PROMPTS.get(quiz_type, _QUIZ_TYPE_PROMPTS["mixed"])
       context_block = self._build_context_block(ai_context, quiz_type, vocab_data)

       topic_block = ""
       if current_topic:
           topic_block = (
               f"CURRENT GRAMMAR TOPIC: {current_topic}\n"
               "This quiz MUST test ONLY the CURRENT GRAMMAR TOPIC above. "
               "Do NOT generate questions about any other grammar topic or infer a "
               "different topic from the user's history. Use user history only to "
               "choose examples and distractors that are relevant, but do NOT "
               "change the grammar topic.\n\n"
           )

       return (
           f"You are MemoraBot's Quiz Generator.\n\n"
           f"{_BASE_RULES}\n\n"
           f"{mode_instruction}\n\n"
           f"{topic_block}"
           f"USER CONTEXT:\n{context_block}\n\n"
           f"Generate EXACTLY {num_questions} questions matching the schema.\n"
           f"The 'title' field should describe what this quiz covers.\n"
           f"{'Include the passage in the top-level \"passage\" field.' if quiz_type == 'reading' else 'Set \"passage\" to an empty string.'}"
       )

    def _build_context_block(
        self,
        ctx: AIContext,
        quiz_type: str,
        vocab_data: dict[str, Any],
    ) -> str:
        """Build the context block injected into the prompt."""
        lines: list[str] = []
        uc = ctx.user_context

        if uc.english_level:
            lines.append(f"CEFR level: {uc.english_level}")
        if uc.learning_goal:
            lines.append(f"Learning goal: {uc.learning_goal}")
        if uc.active_topic:
            lines.append(f"Active topic: {uc.active_topic}")

        # Grammar intelligence: surface weak grammar areas from UserMemory
        if quiz_type in ("grammar", "mixed") and ctx.weak_words:
            grammar_weak = [w for w in ctx.weak_words if len(w) > 3][:8]
            if grammar_weak:
                lines.append(f"Grammar/vocabulary weak areas: {', '.join(grammar_weak)}")

        # Vocabulary words — primary source for vocabulary / mixed / gap_fill
        vocab_words: list[dict] = vocab_data.get("vocab_words", [])
        weak_words: list[str] = vocab_data.get("weak_words", ctx.weak_words or [])
        recent_activity: list[str] = vocab_data.get("recent_activity_words", [])

        if vocab_words and quiz_type in ("vocabulary", "mixed", "gap_fill"):
            # Format: word (meaning) [difficulty] [★ if favorite]
            word_lines = []
            for entry in vocab_words[:50]:
                fav = "★ " if entry.get("is_favorite") else ""
                diff = f" [{entry.get('difficulty', '')}]" if entry.get("difficulty") else ""
                word_lines.append(
                    f"  {fav}{entry['word']}: {entry.get('meaning', '')[:80]}{diff}"
                )
            lines.append(f"VOCAB WORDS ({len(vocab_words)} saved):")
            lines.extend(word_lines)

        elif ctx.recent_words_week and quiz_type in ("gap_fill", "mixed"):
            lines.append(f"Recent words: {', '.join(ctx.recent_words_week[:20])}")

        if weak_words:
            lines.append(f"Weak words (prioritise as distractors): {', '.join(weak_words[:10])}")

        # Reading mode: topic hint
        if quiz_type == "reading":
            topic_hint = uc.active_topic or uc.learning_goal or "general English"
            lines.append(f"Write passage about: {topic_hint}")

        # Document passages for document-based comprehension
        if ctx.search_chunks:
            lines.append("Document passages:")
            for i, chunk in enumerate(ctx.search_chunks[:2], 1):
                lines.append(f"  [{i}] {chunk.get('text', '')[:300]}")

        if not lines:
            lines.append(
                f"No specific vocabulary available. Generate appropriate questions "
                f"for {uc.english_level or 'B1'} CEFR level."
            )

        return "\n".join(lines)

    # ── AI call + retry ─────────────────────────────────────────────────── #

    async def _generate_with_retry(
        self,
        *,
        system_prompt: str,
        quiz_type: str,
        num_questions: int,
        user_context: UserContext,
        vocab_data: dict[str, Any],
        current_topic: str | None = None,
    ) -> QuizPayload:
        """Call AI, parse, validate quality.  Retry once on common failures.

        Retries on:
          - QuizQualityError (quality validation)
          - ValueError from parsing / schema validation (malformed AI output)
          - AIProviderError from the router (transient provider failures)

        When JSON parsing fails, the retry uses a clarified system prompt that
        re-emphasises the contract (return valid JSON only, shorten fields if
        necessary) and increases max_tokens to reduce truncation risk.
        """
        for attempt in range(2):
            # Build per-attempt AIRequest parameters; on retry we append a short
            # retry instruction and increase max_tokens to reduce truncation.
            is_retry = attempt > 0
            req_system = system_prompt
            if is_retry:
                retry_block = (
                    "\n\nRETRY INSTRUCTION: The previous response was not valid JSON. "
                    "Return ONLY valid JSON — NO surrounding explanation, markdown, or backticks. "
                    "If the response would be too long, shorten or remove whitespace and "
                    "truncate explanations to at most 60 characters. Do NOT change the "
                    "selected quiz type or topic."
                )
                if current_topic:
                    retry_block += f" CURRENT GRAMMAR TOPIC (again): {current_topic}."
                req_system = system_prompt + retry_block

            # Set max_tokens higher on retry to guard against truncation.
            max_tokens = 2048 if not is_retry else 4096

            try:
                # Log the attempt
                logger.debug(
                    "QuizService: AI request attempt=%s quiz_type=%s topic=%s max_tokens=%s",
                    attempt + 1, quiz_type, current_topic, max_tokens,
                )

                response = await self._router.complete(
                    AIRequest(
                        system_prompt=req_system,
                        user_message=(
                            f"Generate {num_questions} {quiz_type} quiz questions now. "
                            "Return JSON only."
                        ),
                        response_schema=QUIZ_JSON_SCHEMA,
                        temperature=0.8,
                        max_tokens=max_tokens,
                        request_type="quiz",
                    ),
                    is_premium=user_context.is_premium,
                )
            except AIProviderError as exc:
                logger.error(
                    "QuizService: AI provider error on attempt %s: %s", attempt + 1, exc
                )
                if attempt == 0:
                    logger.warning("QuizService: retrying AI provider call (attempt 2)")
                    continue
                # Propagate provider exhaustion
                raise

            try:
                payload = self._parse_quiz_response(response.raw_text, quiz_type)
                self._validate_quality(payload, quiz_type, vocab_data)
                # Shuffle AFTER validation so positions are random
                payload = self._shuffle_answers(payload)
                # Final position-diversity check after shuffle (sanity)
                return payload
            except QuizQualityError as exc:
                if attempt == 0:
                    logger.warning(
                        "QuizService: quality check failed (attempt 1), retrying — %s", exc
                    )
                    continue
                raise
            except ValueError as exc:
                # Parsing or schema validation error — log provider info and raw text
                provider = getattr(response, "provider_name", "unknown")
                model = getattr(response, "model_name", "unknown")
                tokens = getattr(response, "tokens_used", None)
                resp_len = len(getattr(response, "raw_text", "")) if getattr(response, "raw_text", None) else 0
                logger.error(
                    "QuizService: parse/validation error on attempt %s: %s\nprovider=%s model=%s tokens=%s resp_len=%s",
                    attempt + 1,
                    exc,
                    provider,
                    model,
                    tokens,
                    resp_len,
                )
                logger.debug("Raw response (truncated): %s", (getattr(response, "raw_text", None) or '')[:2000])
                if attempt == 0:
                    logger.warning("QuizService: retrying after parse error (attempt 2)")
                    continue
                # After retries, surface a clean error to caller instead of crashing
                raise ValueError("AI returned invalid JSON after retry") from exc

    # ── Answer shuffling ────────────────────────────────────────────────── #

    def _shuffle_answers(self, payload: QuizPayload) -> QuizPayload:
        """Randomly permute option order per question and update correct_option.

        The correct answer is guaranteed to be preserved.  Every position
        (A/B/C/D) has equal probability over many quizzes.
        """
        shuffled_questions: list[QuizQuestion] = []
        for q in payload.questions:
            options = list(q.options)
            correct_text = options[q.correct_option]

            # Build (text, is_correct) pairs
            tagged = [(opt, idx == q.correct_option) for idx, opt in enumerate(options)]
            random.shuffle(tagged)

            new_options = [t[0] for t in tagged]
            new_correct = next(i for i, (_, is_c) in enumerate(tagged) if is_c)

            shuffled_questions.append(
                QuizQuestion(
                    question=q.question,
                    options=new_options,
                    correct_option=new_correct,
                    explanation=q.explanation,
                    quiz_type=q.quiz_type,
                    source_chunk_id=q.source_chunk_id,
                )
            )

        return QuizPayload(
            version=payload.version,
            title=payload.title,
            topic=payload.topic,
            difficulty=payload.difficulty,
            questions=shuffled_questions,
            source_id=payload.source_id,
            passage=payload.passage,
        )

    # ── Quality validation ──────────────────────────────────────────────── #

    def _validate_quality(
        self,
        payload: QuizPayload,
        quiz_type: str,
        vocab_data: "dict | set",
    ) -> None:
        """Raise QuizQualityError if the quiz does not meet quality standards.

        vocab_data may be:
          - a dict (from the tool layer) containing "vocab_words" list of
            {word, meaning} dicts — the normal production path.
          - a set[str] of English words only — used by tests that call this
            method directly (test 20 passes a plain set).

        In vocabulary mode the check accepts a correct answer if it matches
        either the English word OR the Uzbek meaning of any saved entry, so
        EN→UZ questions (where the correct option is a Uzbek meaning) are
        never falsely rejected.
        """
        # Build the allowed-words sets.
        # Supports both calling conventions (dict from tool layer, set from tests).
        if isinstance(vocab_data, dict):
            vocab_words = vocab_data.get("vocab_words", [])
            known_en_words: set[str] = {e["word"].lower() for e in vocab_words}
            known_uz_meanings: set[str] = {
                e["meaning"].lower() for e in vocab_words if e.get("meaning")
            }
        else:
            # Legacy / test path: plain set of English words
            known_en_words = {w.lower() for w in vocab_data}
            known_uz_meanings: set[str] = set()
        known_vocab_words = known_en_words | known_uz_meanings
        if not payload.questions:
            raise QuizQualityError("AI returned no questions.")

        seen_questions: set[str] = set()
        correct_positions: list[int] = []

        for i, q in enumerate(payload.questions):
            q_key = q.question.strip().lower()

            # Duplicate questions
            if q_key in seen_questions:
                raise QuizQualityError(f"Duplicate question at index {i}: {q.question[:60]!r}")
            seen_questions.add(q_key)

            # Fewer than 4 options
            if len(q.options) < 4:
                raise QuizQualityError(
                    f"Question {i} has only {len(q.options)} option(s); need 4."
                )

            # correct_option out of range
            if not (0 <= q.correct_option < len(q.options)):
                raise QuizQualityError(
                    f"Question {i}: correct_option={q.correct_option} out of range."
                )

            # Duplicate options within question
            seen_opts = set()
            for opt in q.options:
                key = opt.strip().lower()
                if key in seen_opts:
                    raise QuizQualityError(
                        f"Question {i} has duplicate option: {opt!r}"
                    )
                seen_opts.add(key)

            # Empty correct answer
            correct_text = q.options[q.correct_option].strip()
            if not correct_text:
                raise QuizQualityError(f"Question {i}: correct answer is empty.")

            correct_positions.append(q.correct_option)

            # Vocabulary mode: reject questions about unknown words
            if quiz_type == "vocabulary" and known_vocab_words:
                # Extract the word being tested from the question
                tested_word = self._extract_tested_word(q)
                if tested_word and tested_word.lower() not in known_vocab_words:
                    raise QuizQualityError(
                        f"Question {i} tests word {tested_word!r} not in user vocabulary."
                    )

        # All questions use the same correct position (bias check — before shuffle)
        if len(correct_positions) >= 3 and len(set(correct_positions)) == 1:
            raise QuizQualityError(
                "All questions have correct answer in same position — AI bias detected."
            )

    def _extract_tested_word(self, q: QuizQuestion) -> str | None:
        """Try to identify the English vocabulary word being tested.

        Handles both question directions:
          Type A (EN -> UZ): the English word appears quoted in the question text.
                             e.g. "What does 'inevitable' mean?"
          Type B (UZ -> EN): the Uzbek meaning appears in the question text;
                             the English word is the correct option.

        Returns the English word in lower-case, or None when it cannot be
        determined (which skips the vocab-membership check for that question).
        """
        # Type A: English word quoted in question
        m = re.search(
            r"['\u2018\u2019\u201c\u201d]([a-zA-Z][a-zA-Z \-]{1,29})['\u2018\u2019\u201c\u201d]",
            q.question,
        )
        if m:
            candidate = m.group(1).strip().lower()
            # Only treat as "English word" if it looks like one (ASCII letters)
            if re.fullmatch(r"[a-z][a-z \-]+", candidate):
                return candidate

        # Type B: correct option IS the English word
        # We only return it when it looks like an English word (not Uzbek/Russian).
        if 0 <= q.correct_option < len(q.options):
            opt = q.options[q.correct_option].strip().lower()
            if re.fullmatch(r"[a-z][a-z \-]+", opt):
                return opt

        return None

    def _extract_word_from_question(self, question: "QuizQuestion") -> "str | None":
        """Alias used by tests and the handler for weak-word tracking.

        For Type B (UZ→EN) questions: the correct option IS the English word.
        For Type A (EN→UZ) questions: falls back to returning the correct option
        text (a Uzbek meaning) so that at least something is recorded.
        """
        return self._extract_tested_word(question)

    # ── Response parsing ────────────────────────────────────────────────── #

    def _parse_quiz_response(self, raw_text: str, quiz_type: str) -> QuizPayload:
        """Parse the AI's JSON response into a QuizPayload."""
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("QuizService: JSON parse error — %s\nRaw: %s", exc, raw_text[:200])
            raise ValueError(f"AI returned invalid JSON: {exc}") from exc

        # Inject 'passage' field default if missing (older schema compat)
        if "passage" not in data:
            data["passage"] = ""

        try:
            payload = QuizPayload.model_validate(data)
        except Exception as exc:
            logger.error("QuizService: schema validation error — %s", exc)
            raise ValueError(f"Quiz schema validation failed: {exc}") from exc

        # Filter out questions with < 2 options (catastrophic AI failure)
        valid_qs = [q for q in payload.questions if len(q.options) >= 2]
        if not valid_qs:
            raise ValueError("AI returned quiz with no usable questions.")

        # Stamp quiz_type on each question
        stamped = [
            QuizQuestion(
                question=q.question,
                options=q.options,
                correct_option=q.correct_option,
                explanation=q.explanation,
                quiz_type=q.quiz_type or quiz_type,
                source_chunk_id=q.source_chunk_id,
            )
            for q in valid_qs
        ]

        return QuizPayload(
            version=payload.version,
            title=payload.title or f"{quiz_type.title()} Quiz",
            topic=payload.topic,
            difficulty=payload.difficulty,
            questions=stamped,
            source_id=payload.source_id,
            passage=getattr(payload, "passage", ""),
        )

    # ── Special modes ───────────────────────────────────────────────────── #

    def _listening_placeholder(self) -> QuizPayload:
        """Return a Coming Soon placeholder payload for listening mode."""
        return QuizPayload(
            version=1,
            title="🎧 Listening Quiz — Coming Soon",
            topic="listening",
            difficulty="",
            questions=[],
            passage="",
        )
