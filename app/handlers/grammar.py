"""Grammar Learning handlers (Learn → Grammar).

Navigation flow
---------------
Dashboard
  → Learn (DashboardCallback action="learn")
  → Grammar (GrammarCallback action="topics")
  → Topic selected (GrammarCallback action="open_topic")
     ├── Lesson retrieved from Telegram channel
     ├── Record lesson open in UserGrammarProgress
     └── Show [❓ Ask AI] [🧠 Test Yourself] [⬅️ Back to Grammar]
          ├── Ask AI → GrammarStates.asking_question
          │    └── user message → grammar Q&A answer
          └── Test Yourself → grammar quiz (Telegram Quiz Polls)

Channel lesson retrieval
------------------------
Each GrammarTopic has a `channel_message_id`.  The handler uses
`bot.copy_message(chat_id, from_chat_id=grammar_channel_id, message_id=…)`
to copy the lesson to the user's chat.  This preserves original formatting
(bold, lists, code blocks) without the bot re-sending as forwarded.

If the channel ID is 0 (not configured) or the message does not exist:
  - Log the error.
  - Show a clean localised error message.
  - Do NOT mark the topic as studied.

Grammar Q&A (GrammarStates.asking_question)
-------------------------------------------
Any text message in this state is interpreted as a grammar question.
The handler:
  1. Reads current_grammar_topic_id from FSM.
  2. Fetches the GrammarTopic from DB.
  3. Builds AIContext with ContextPolicy.for_grammar_chat().
  4. Calls PromptBuilder.build_system_prompt(feature="grammar_chat").
  5. Calls AIRouter.complete() and validates the response.
  6. Returns HTML-formatted answer using Telegram parse_mode=HTML.

Grammar Quiz (GrammarStates.quiz_answering)
-------------------------------------------
Reuses QuizService with quiz_type="grammar_topic" and the current topic
injected into the prompt.  Telegram Quiz Polls are sent with open_period
from GRAMMAR_QUIZ_TIME_SECONDS.

FSM state keys
--------------
  "grammar_topic_id"     — GrammarTopic.id of the current lesson
  "grammar_topic_title"  — display title (to avoid DB round-trips)
  "grammar_topic_desc"   — description (for AI context)
  "grammar_quiz_questions"  — list of serialised QuizQuestion dicts
  "grammar_quiz_current"    — next question index
  "grammar_quiz_correct"    — correct count so far
  "grammar_quiz_wrong"      — wrong count so far
  "grammar_quiz_poll_map"   — {poll_id: question_index}
  "grammar_quiz_open_period" — timer in seconds (from config)
"""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputPollOption, Message, PollAnswer

from app.handlers.dashboard import edit_to_dashboard
from app.keyboards.callback_data import DashboardCallback, GrammarCallback
from app.keyboards.grammar_kb import (
    get_grammar_qa_abort_keyboard,
    get_grammar_quiz_results_keyboard,
    get_grammar_topics_keyboard,
    get_learn_keyboard,
    get_lesson_actions_keyboard,
)
from app.services.activity_service import ActivityService
from app.services.ai.router import AIRequest, AIRouter
from app.services.context.context_builder import ContextPolicy
from app.services.context.prompt_builder import PromptBuilder
from app.services.context.user_context import UserContext
from app.services.context.user_context_service import UserContextService
from app.services.grammar_service import GrammarService
from app.services.outputs.schemas import QuizPayload, QuizQuestion
from app.services.quiz_service import QuizService
from app.services.settings_service import SettingsService
from app.services.tools.base import ToolContext
from app.services.tools.planner import AIPlanner
from app.services.user_service import UserService
from app.states.bot_states import GrammarStates
from app.texts.messages import t

logger = logging.getLogger(__name__)

router = Router(name="grammar")

_prompt_builder = PromptBuilder()

# FSM key constants
_TOPIC_ID    = "grammar_topic_id"
_TOPIC_TITLE = "grammar_topic_title"
_TOPIC_DESC  = "grammar_topic_desc"
_QUIZ_QS     = "grammar_quiz_questions"
_QUIZ_CUR    = "grammar_quiz_current"
_QUIZ_CORRECT= "grammar_quiz_correct"
_QUIZ_WRONG  = "grammar_quiz_wrong"
_QUIZ_MAP    = "grammar_quiz_poll_map"
_QUIZ_PERIOD = "grammar_quiz_open_period"
_QUIZ_TOTAL  = "grammar_quiz_total"

_MAX_POLL_OPTION   = 100
_MAX_POLL_QUESTION = 300
_MAX_EXPLANATION   = 200


# ── Learn section entry ────────────────────────────────────────────────── #

@router.callback_query(DashboardCallback.filter(F.action == "learn"))
async def on_learn(
    callback: CallbackQuery,
    settings_service: SettingsService,
) -> None:
    """Dashboard → Learn button."""
    lang = await settings_service.get_language(callback.from_user.id)
    await callback.message.edit_text(
        t("learn.welcome", lang),
        reply_markup=get_learn_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Grammar topic list ─────────────────────────────────────────────────── #

@router.callback_query(GrammarCallback.filter(F.action == "topics"))
async def on_grammar_topics(
    callback: CallbackQuery,
    callback_data: GrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_service: GrammarService,
) -> None:
    """Show the paginated grammar topic selection keyboard."""
    lang = await settings_service.get_language(callback.from_user.id)
    await state.clear()

    topics = await grammar_service.list_active_topics()
    if not topics:
        await callback.message.edit_text(
            t("grammar.no_topics", lang),
            reply_markup=get_learn_keyboard(lang),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    page = callback_data.page
    await callback.message.edit_text(
        t("grammar.topics_title", lang),
        reply_markup=get_grammar_topics_keyboard(topics, lang, page=page),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Open a grammar lesson ──────────────────────────────────────────────── #

@router.callback_query(GrammarCallback.filter(F.action == "open_topic"))
async def on_open_topic(
    callback: CallbackQuery,
    callback_data: GrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    user_service: UserService,
    grammar_service: GrammarService,
) -> None:
    """Retrieve and display a grammar lesson from the Telegram channel."""
    lang = await settings_service.get_language(callback.from_user.id)
    topic_id = callback_data.topic_id

    topic = await grammar_service.get_topic(topic_id)
    if topic is None:
        await callback.answer(t("grammar.lesson_error", lang), show_alert=True)
        return

    # Resolve internal user_id
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(t("grammar.lesson_error", lang), show_alert=True)
        return

    # Acknowledge the CallbackQuery early to avoid Telegram timeout on slow ops
    await callback.answer()

    # Persist lesson open BEFORE channel retrieval — marks the topic as studied
    # (only if we can resolve the user; the increment is safe to undo on failure)
    try:
        await grammar_service.start_topic(user.id, topic_id)
    except Exception:
        logger.warning(
            "on_open_topic: start_topic failed uid=%s topic=%s",
            user.id, topic_id, exc_info=True,
        )

    # Store active grammar context in FSM for Q&A and quiz
    await state.update_data({
        _TOPIC_ID:    topic_id,
        _TOPIC_TITLE: topic.title,
        _TOPIC_DESC:  topic.description or "",
    })

    # Retrieve the channel lesson
    bot: Bot = callback.bot
    from app.config import settings as _settings
    channel_id = _settings.grammar_channel_id

    if not channel_id:
        await callback.message.edit_text(
            t("grammar.channel_not_configured", lang),
            reply_markup=get_learn_keyboard(lang),
            parse_mode="HTML",
        )
        return

    if not topic.channel_message_id:
        await callback.message.edit_text(
            t("grammar.lesson_not_configured", lang),
            reply_markup=get_lesson_actions_keyboard(topic_id, lang),
            parse_mode="HTML",
        )
        return

    try:
        # Copy preserves original formatting (bold, lists, etc.) without "Forwarded" header
        await bot.copy_message(
            chat_id=callback.message.chat.id,
            from_chat_id=channel_id,
            message_id=topic.channel_message_id,
        )
    except Exception as exc:
        logger.warning(
            "on_open_topic: channel copy failed channel=%s msg=%s — %s",
            channel_id, topic.channel_message_id, exc,
        )
        # If copy fails, show a header so the user isn't left without context
        await callback.message.edit_text(
            t("grammar.lesson_header", lang, title=topic.title),
            parse_mode="HTML",
        )

    # Show lesson action buttons in a NEW message (not editing — lesson was just sent)
    await callback.message.answer(
        t("grammar.lesson_header", lang, title=topic.title),
        reply_markup=get_lesson_actions_keyboard(topic_id, lang),
        parse_mode="HTML",
    )


# ── Ask AI: enter Q&A mode ─────────────────────────────────────────────── #

@router.callback_query(GrammarCallback.filter(F.action == "ask_ai"))
async def on_ask_ai(
    callback: CallbackQuery,
    callback_data: GrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_service: GrammarService,
) -> None:
    """Enter grammar Q&A mode for the current topic."""
    lang = await settings_service.get_language(callback.from_user.id)
    topic_id = callback_data.topic_id

    topic = await grammar_service.get_topic(topic_id)
    if topic is None:
        await callback.answer(t("grammar.lesson_error", lang), show_alert=True)
        return

    await state.set_state(GrammarStates.asking_question)
    await state.update_data({
        _TOPIC_ID:    topic_id,
        _TOPIC_TITLE: topic.title,
        _TOPIC_DESC:  topic.description or "",
    })

    await callback.message.answer(
        t("grammar.ask_ai_prompt", lang, title=topic.title),
        reply_markup=get_grammar_qa_abort_keyboard(topic_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(GrammarStates.asking_question)
async def on_grammar_question(
    message: Message,
    state: FSMContext,
    settings_service: SettingsService,
    user_service: UserService,
    user_context_service: UserContextService,
    ai_router: AIRouter | None,
    ai_planner: AIPlanner | None,
    tool_context_template: ToolContext | None,
) -> None:
    """Handle a user question while in grammar Q&A mode."""
    lang = await settings_service.get_language(message.from_user.id)

    if ai_router is None:
        await message.answer(t("grammar.ask_ai_error", lang))
        return

    data = await state.get_data()
    topic_id    = data.get(_TOPIC_ID, 0)
    topic_title = data.get(_TOPIC_TITLE, "")
    topic_desc  = data.get(_TOPIC_DESC, "")

    thinking = await message.answer(t("grammar.ask_ai_thinking", lang))

    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await thinking.delete()
        await message.answer(t("grammar.ask_ai_error", lang))
        return

    user_context = await user_context_service.build(user.id)

    # Build grammar-aware AIContext
    from app.services.context.context_builder import AIContext
    ai_context = AIContext(
        user_context=user_context,
        current_grammar_topic=topic_title,
        current_grammar_topic_id=topic_id,
        current_grammar_description=topic_desc,
    )

    # Extend with grammar progress if planner + tool_context available
    if ai_planner is not None and tool_context_template is not None:
        import dataclasses
        tc = dataclasses.replace(
            tool_context_template, user_id=user.id, user_context=user_context
        )
        try:
            from app.services.tools.base import ToolResult
            result = await ai_planner._registry.execute("get_studied_grammar_topics", tc)
            if result.success:
                studied = result.data.get("studied_topics", [])
                recent_titles = [s["title"] for s in studied if s.get("title")]
                ai_context = dataclasses.replace(
                    ai_context,
                    grammar_progress=studied,
                    recent_grammar_topics=recent_titles,
                )
        except Exception:
            logger.warning("on_grammar_question: grammar progress lookup failed", exc_info=True)

    system_prompt = _prompt_builder.build_system_prompt(ai_context, feature="grammar_chat")

    try:
        response = await ai_router.complete(
            AIRequest(
                system_prompt=system_prompt,
                user_message=message.text or "",
                temperature=0.5,
                max_tokens=1024,
                request_type="grammar_chat",
            ),
            is_premium=user_context.is_premium,
        )
        answer_text = _sanitise_html(response.raw_text)
    except Exception:
        logger.exception("on_grammar_question: AI call failed uid=%s", user.id)
        await thinking.delete()
        await message.answer(t("grammar.ask_ai_error", lang))
        return

    await thinking.delete()
    await message.answer(
        answer_text,
        parse_mode="HTML",
        reply_markup=get_grammar_qa_abort_keyboard(topic_id, lang),
    )


# ── Test Yourself: grammar quiz ────────────────────────────────────────── #

@router.callback_query(GrammarCallback.filter(F.action == "test"))
async def on_grammar_test(
    callback: CallbackQuery,
    callback_data: GrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    user_service: UserService,
    user_context_service: UserContextService,
    grammar_service: GrammarService,
    quiz_service: QuizService,
    ai_router: AIRouter | None,
    tool_context_template: ToolContext | None,
) -> None:
    """Generate and start a grammar quiz for the current topic.

    Implementation note: acknowledge the CallbackQuery early to avoid the
    Telegram 'query is too old' error. Do not call callback.answer() later in
    this handler.
    """
    lang = await settings_service.get_language(callback.from_user.id)

    # Quick pre-checks: if AI router or topic missing, reply with an alert quickly
    if ai_router is None:
        await callback.answer(t("grammar.quiz_error", lang), show_alert=True)
        return

    topic_id = callback_data.topic_id
    topic = await grammar_service.get_topic(topic_id)
    if topic is None:
        await callback.answer(t("grammar.quiz_error", lang), show_alert=True)
        return

    # Acknowledge the CallbackQuery immediately to avoid Telegram timeout
    await callback.answer()

    # Inform the user that quiz is being generated
    await callback.message.edit_text(t("grammar.quiz_generating", lang))

    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        # Cannot show a callback alert here because we've already answered the query;
        # send a message instead.
        await callback.message.edit_text(
            t("grammar.quiz_error", lang),
            reply_markup=get_lesson_actions_keyboard(topic_id, lang),
        )
        return

    user_context = await user_context_service.build(user.id)

    # Build tool context stamped for this user
    import dataclasses
    tool_ctx = None
    if tool_context_template is not None:
        tool_ctx = dataclasses.replace(
            tool_context_template, user_id=user.id, user_context=user_context
        )

    # Load config for grammar quiz
    from app.config import settings as _settings
    num_questions = max(2, min(10, _settings.grammar_quiz_questions))
    open_period_s = max(0, _settings.grammar_quiz_time_seconds)

    # Grammar topic quiz message — tell the AI exactly which topic to test
    topic_message = (
        f"Generate a grammar quiz specifically about: {topic.title}.\n"
        f"Description: {topic.description or topic.title}\n"
        f"Focus ONLY on {topic.title} — do not test other grammar topics."
    )

    try:
        payload = await quiz_service.generate(
            user_id=user.id,
            user_context=user_context,
            user_message=topic_message,
            quiz_type="grammar",
            num_questions=num_questions,
            tool_context=tool_ctx,
            current_grammar_topic=topic.title,
            current_grammar_topic_id=topic_id,
        )
    except Exception:
        logger.exception(
            "on_grammar_test: quiz generation failed uid=%s topic=%s",
            user.id, topic_id,
        )
        await callback.message.edit_text(
            t("grammar.quiz_error", lang),
            reply_markup=get_lesson_actions_keyboard(topic_id, lang),
        )
        return

    if not payload.questions:
        await callback.message.edit_text(
            t("grammar.quiz_error", lang),
            reply_markup=get_lesson_actions_keyboard(topic_id, lang),
        )
        return

    # Set FSM state
    await state.set_state(GrammarStates.quiz_answering)
    await state.set_data({
        _TOPIC_ID:     topic_id,
        _TOPIC_TITLE:  topic.title,
        _TOPIC_DESC:   topic.description or "",
        _QUIZ_QS:      [q.model_dump() for q in payload.questions],
        _QUIZ_CUR:     0,
        _QUIZ_CORRECT: 0,
        _QUIZ_WRONG:   0,
        _QUIZ_MAP:     {},
        _QUIZ_PERIOD:  open_period_s,
        _QUIZ_TOTAL:   len(payload.questions),
    })

    # Send first question
    await _send_grammar_poll(
        bot=callback.bot,
        state=state,
        chat_id=callback.message.chat.id,
        question=payload.questions[0],
        index=0,
        total=len(payload.questions),
        open_period=open_period_s,
        user_id=user.id,
        lang=lang,
    )


@router.poll_answer()
async def on_grammar_poll_answer(
    poll_answer: PollAnswer,
    state: FSMContext,
    bot: Bot,
    grammar_service: GrammarService,
    settings_service: SettingsService,
) -> None:
    """Handle a grammar quiz poll answer."""
    current_state = await state.get_state()
    if current_state != GrammarStates.quiz_answering.state:
        return   # not a grammar quiz poll — let other handlers deal with it

    data = await state.get_data()
    poll_map: dict = data.get(_QUIZ_MAP, {})
    if poll_answer.poll_id not in poll_map:
        return

    q_index: int    = poll_map[poll_answer.poll_id]
    questions_raw   = data.get(_QUIZ_QS, [])
    if q_index >= len(questions_raw):
        return

    q = QuizQuestion.model_validate(questions_raw[q_index])
    lang      = data.get("grammar_lang", "en")
    user_id   = data.get("grammar_user_id", 0)
    topic_id  = data.get(_TOPIC_ID, 0)
    chat_id   = data.get("grammar_chat_id", 0)
    total     = data.get(_QUIZ_TOTAL, len(questions_raw))

    chosen   = poll_answer.option_ids[0] if poll_answer.option_ids else -1
    correct  = chosen == q.correct_option
    correct_count = data.get(_QUIZ_CORRECT, 0) + (1 if correct else 0)
    wrong_count   = data.get(_QUIZ_WRONG,   0) + (0 if correct else 1)

    try:
        await grammar_service.record_question_result(user_id, topic_id, correct=correct)
    except Exception:
        logger.warning("on_grammar_poll_answer: record_question failed", exc_info=True)

    next_index = q_index + 1
    await state.update_data({
        _QUIZ_CORRECT: correct_count,
        _QUIZ_WRONG:   wrong_count,
        _QUIZ_CUR:     next_index,
    })

    if next_index < total:
        next_q = QuizQuestion.model_validate(questions_raw[next_index])
        open_period = data.get(_QUIZ_PERIOD, 20)
        await _send_grammar_poll(
            bot=bot,
            state=state,
            chat_id=chat_id,
            question=next_q,
            index=next_index,
            total=total,
            open_period=open_period,
            user_id=user_id,
            lang=lang,
        )
    else:
        # Quiz complete
        try:
            await grammar_service.complete_quiz(
                user_id, topic_id,
                correct=correct_count,
                total=total,
            )
        except Exception:
            logger.warning("on_grammar_poll_answer: complete_quiz failed", exc_info=True)

        mastery = await grammar_service.get_mastery(user_id, topic_id)
        accuracy = round(correct_count / total * 100) if total else 0
        topic_title = data.get(_TOPIC_TITLE, "")

        # Re-fetch lang from settings would need settings_service; use cached lang
        results_text = t(
            "grammar.quiz_results", lang,
            correct=str(correct_count),
            total=str(total),
            accuracy=str(accuracy),
            mastery=str(round(mastery * 100)),
        )
        from app.services.grammar_service import MASTERY_COMPLETED_THRESHOLD, MIN_QUESTIONS_TO_COMPLETE
        if mastery >= MASTERY_COMPLETED_THRESHOLD:
            results_text += "\n\n" + t("grammar.quiz_completed_status", lang)

        await bot.send_message(
            chat_id=chat_id,
            text=results_text,
            reply_markup=get_grammar_quiz_results_keyboard(topic_id, lang),
            parse_mode="HTML",
        )
        await state.clear()


# ── Private helpers ────────────────────────────────────────────────────── #

async def _send_grammar_poll(
    *,
    bot: Bot,
    state: FSMContext,
    chat_id: int,
    question: QuizQuestion,
    index: int,
    total: int,
    open_period: int,
    user_id: int,
    lang: str,
) -> None:
    """Send one grammar quiz question as a Telegram Quiz Poll."""
    options = [
        InputPollOption(text=opt[:_MAX_POLL_OPTION])
        for opt in question.options
    ]
    explanation = (question.explanation or "")[:_MAX_EXPLANATION]
    tg_period: int | None = open_period if (5 <= open_period <= 600) else None

    try:
        poll_msg = await bot.send_poll(
            chat_id=chat_id,
            question=question.question[:_MAX_POLL_QUESTION],
            options=options,
            type="quiz",
            correct_option_id=question.correct_option,
            explanation=explanation or None,
            is_anonymous=False,
            open_period=tg_period,
        )
        # Update FSM poll map
        data = await state.get_data()
        poll_map: dict = data.get(_QUIZ_MAP, {})
        poll_map[poll_msg.poll.id] = index

        # Store chat/user/lang for poll_answer handler
        await state.update_data({
            _QUIZ_MAP:         poll_map,
            "grammar_chat_id": chat_id,
            "grammar_user_id": user_id,
            "grammar_lang":    lang,
        })
    except Exception:
        logger.exception(
            "_send_grammar_poll: failed idx=%d uid=%s", index, user_id
        )


# Re-exported for backward compatibility and so handlers can import directly.
from app.utils.html_utils import sanitise_html as _sanitise_html
