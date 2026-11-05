"""Quiz handlers (Feature C): AI-powered Telegram Quiz Polls.

Flow — standard quiz (vocabulary / grammar / gap_fill / mixed)
--------------------------------------------------------------
1. User taps 🧠 Quiz on dashboard → on_quiz_enter()
   Shows quiz type selection keyboard.

2. User taps a quiz type → on_quiz_start()
   - Builds UserContext + ToolContext
   - Calls QuizService.generate()
   - Sends the first question as a Telegram Quiz Poll
   - Stores session in FSM
   - Sets QuizStates.answering

3. Telegram sends poll_answer update → on_poll_answer()
   - Matches poll_id to question index
   - Records QUESTION_CORRECT / QUESTION_WRONG
   - Updates UserMemory weak_words for wrong answers
   - Sends next poll or shows results

4. User taps End Quiz → on_quiz_end()
   - Clears FSM, records QUIZ_COMPLETED with partial results.

Flow — reading quiz
-------------------
1-2. Same as above up to on_quiz_start().
3.   QuizService returns payload with a non-empty `passage` field.
4.   Handler sends the passage as a regular message with a
     "▶️ Start Questions" button.  State = QuizStates.reading_passage.
5.   User taps "▶️ Start Questions" → on_reading_begin()
     Sends question 0 as a Telegram Quiz Poll.
     State = QuizStates.answering.
6.   Same poll_answer flow as standard quiz.

Flow — listening quiz
---------------------
QuizService returns an empty questions list with title "Coming Soon".
Handler shows the Coming Soon message and returns to type selection.

Quiz timing
-----------
Every poll uses open_period from settings (default 20 s, config key QUIZ_OPEN_PERIOD).
open_period=0 disables the timer entirely (polls stay open until answered).

FSM state keys
--------------
  "quiz_output_id"     — FeatureOutput.id of this quiz
  "quiz_questions"     — list of serialised QuizQuestion dicts
  "quiz_current"       — index of the next question to send (0-based)
  "quiz_correct"       — count of correct answers so far
  "quiz_wrong"         — count of wrong answers so far
  "quiz_poll_map"      — {poll_id: question_index}
  "quiz_wrong_words"   — list of words answered incorrectly
  "quiz_start_ts"      — ISO timestamp when quiz started
  "quiz_chat_id"       — chat_id to send next question to
  "quiz_user_id"       — internal user_id (for PollAnswer handler)
  "quiz_lang"          — language code
  "quiz_type"          — the quiz_type string
"""

from __future__ import annotations

import dataclasses
import logging
import re
from datetime import datetime, UTC

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputPollOption, Message, PollAnswer

from app.database.models.learning_activity import ActivityType
from app.handlers.dashboard import edit_to_dashboard, send_dashboard
from app.keyboards.callback_data import DashboardCallback, QuizCallback
from app.keyboards.quiz_kb import (
    get_quiz_abort_keyboard,
    get_quiz_results_keyboard,
    get_quiz_type_keyboard,
    get_reading_start_keyboard,
)
from app.services.activity_service import ActivityService
from app.services.ai.router import AIRouter
from app.services.context.user_context import UserContext
from app.services.context.user_context_service import UserContextService
from app.services.feature_output_service import FeatureOutputService
from app.services.outputs.schemas import QuizPayload, QuizQuestion
from app.services.quiz_service import MIN_VOCAB_FOR_QUIZ, NotEnoughVocabularyError, QuizService
from app.services.settings_service import SettingsService
from app.services.tools.base import ToolContext
from app.services.tools.planner import AIPlanner
from app.services.user_memory_service import UserMemoryService
from app.services.user_service import UserService
from app.states.bot_states import QuizStates
from app.texts.messages import t

logger = logging.getLogger(__name__)

router = Router(name="quiz")

# FSM key constants
_OUTPUT_ID   = "quiz_output_id"
_QUESTIONS   = "quiz_questions"
_CURRENT     = "quiz_current"
_CORRECT     = "quiz_correct"
_WRONG       = "quiz_wrong"
_POLL_MAP    = "quiz_poll_map"
_WRONG_WORDS = "quiz_wrong_words"
_START_TS    = "quiz_start_ts"
_CHAT_ID     = "quiz_chat_id"
_USER_ID_KEY = "quiz_user_id"
_LANG_KEY    = "quiz_lang"
_TYPE_KEY    = "quiz_type"

_MAX_EXPLANATION = 200   # Telegram's poll explanation limit
_MAX_QUESTION    = 300   # Telegram's poll question limit
_MAX_OPTION      = 100   # Telegram's poll option limit


def _make_svc(
    ai_router: AIRouter,
    feature_output_service: FeatureOutputService,
    planner: AIPlanner | None,
    quiz_open_period: int = 20,
) -> QuizService:
    return QuizService(
        ai_router=ai_router,
        feature_output_service=feature_output_service,
        planner=planner,
        quiz_open_period=quiz_open_period,
    )


def _stamp_tool_context(
    template: ToolContext | None,
    user_id: int,
    user_context: UserContext,
) -> ToolContext | None:
    if template is None:
        return None
    return dataclasses.replace(template, user_id=user_id, user_context=user_context)


def _get_open_period(svc: QuizService) -> int | None:
    """Return open_period for Telegram poll (None disables timer)."""
    p = svc.open_period
    if p and 5 <= p <= 600:
        return p
    return None


# ── Entry point ────────────────────────────────────────────────────────── #

@router.callback_query(DashboardCallback.filter(F.action == "quiz"))
async def on_quiz_enter(
    callback: CallbackQuery,
    settings_service: SettingsService,
    ai_router: AIRouter | None,
) -> None:
    """User tapped 🧠 Quiz on the dashboard."""
    lang = await settings_service.get_language(callback.from_user.id)
    if ai_router is None:
        await callback.answer(t("quiz.no_router", lang), show_alert=True)
        return

    await callback.message.edit_text(
        t("quiz.welcome", lang),
        reply_markup=get_quiz_type_keyboard(lang),
    )
    await callback.answer()


# ── Quiz type selected → generate + send first question ────────────────── #

@router.callback_query(QuizCallback.filter(F.action == "start"))
async def on_quiz_start(
    callback: CallbackQuery,
    callback_data: QuizCallback,
    state: FSMContext,
    settings_service: SettingsService,
    user_service: UserService,
    user_context_service: UserContextService,
    feature_output_service: FeatureOutputService,
    activity_service: ActivityService,
    ai_router: AIRouter | None,
    ai_planner: AIPlanner | None,
    tool_context_template: ToolContext | None,
    quiz_service: QuizService | None = None,
) -> None:
    """User chose a quiz type — generate the quiz and handle the first step."""
    lang = await settings_service.get_language(callback.from_user.id)

    if ai_router is None:
        await callback.answer(t("quiz.no_router", lang), show_alert=True)
        return

    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(t("quiz.error", lang), show_alert=True)
        return

    quiz_type = callback_data.quiz_type

    # Listening quiz → show Coming Soon immediately
    if quiz_type == "listening":
        await callback.message.edit_text(
            t("quiz.listening_coming_soon", lang),
            reply_markup=get_quiz_type_keyboard(lang),
        )
        await callback.answer()
        return

    await callback.message.edit_text(t("quiz.generating", lang))

    user_context = await user_context_service.build(user.id)
    tool_context = _stamp_tool_context(tool_context_template, user.id, user_context)

    # Prefer the middleware-injected service (has correct open_period from config).
    # Fall back to constructing one ad-hoc if not available.
    svc: QuizService = quiz_service or _make_svc(ai_router, feature_output_service, ai_planner)

    # For vocabulary quizzes, use the configured question count from settings;
    # for all other types, use the generic default of 5.
    num_questions = svc.vocab_question_count if quiz_type == "vocabulary" else 5

    try:
        payload = await svc.generate(
            user_id=user.id,
            user_context=user_context,
            user_message=f"Generate a {quiz_type} quiz for me.",
            quiz_type=quiz_type,
            num_questions=num_questions,
            tool_context=tool_context,
        )
    except NotEnoughVocabularyError as exc:
        await callback.message.edit_text(
            t("quiz.not_enough_vocab", lang,
              count=str(exc.count), min=str(MIN_VOCAB_FOR_QUIZ)),
            reply_markup=get_quiz_type_keyboard(lang),
        )
        await callback.answer()
        return
    except Exception:
        logger.exception("on_quiz_start: generation failed uid=%s", user.id)
        await callback.message.edit_text(
            t("quiz.error", lang),
            reply_markup=get_quiz_results_keyboard(lang),
        )
        await callback.answer()
        return

    # Listening Coming Soon placeholder (empty questions)
    if not payload.questions:
        await callback.message.edit_text(
            t("quiz.listening_coming_soon", lang),
            reply_markup=get_quiz_type_keyboard(lang),
        )
        await callback.answer()
        return

    now = datetime.now(UTC).isoformat()
    base_fsm: dict = {
        _OUTPUT_ID:        0,
        _QUESTIONS:        [q.model_dump() for q in payload.questions],
        _CURRENT:          0,
        _CORRECT:          0,
        _WRONG:            0,
        _POLL_MAP:         {},
        _WRONG_WORDS:      [],
        _START_TS:         now,
        _CHAT_ID:          callback.message.chat.id,
        _USER_ID_KEY:      user.id,
        _LANG_KEY:         lang,
        _TYPE_KEY:         quiz_type,
        "quiz_open_period": svc.open_period,
    }

    # ── Reading quiz: show passage first ──────────────────────────────── #
    if quiz_type == "reading" and payload.passage:
        await state.set_state(QuizStates.reading_passage)
        await state.set_data(base_fsm)

        passage_msg = await callback.message.answer(
            t("quiz.reading_passage", lang, passage=payload.passage),
            parse_mode="HTML",
            reply_markup=get_reading_start_keyboard(lang, output_id=0),
        )
        await callback.answer()
        return

    # ── Standard quiz: send first question immediately ─────────────────── #
    # Store open_period in FSM so poll_answer handler can reuse it
    base_fsm["quiz_open_period"] = svc.open_period

    await state.set_state(QuizStates.answering)
    await state.set_data(base_fsm)

    await activity_service.record(
        user.id, ActivityType.QUIZ_STARTED,
        metadata={"quiz_type": quiz_type, "total": len(payload.questions)},
    )

    await _send_question(
        bot=callback.bot,
        state=state,
        chat_id=callback.message.chat.id,
        question=payload.questions[0],
        index=0,
        total=len(payload.questions),
        lang=lang,
        user_id=user.id,
        activity_service=activity_service,
        open_period=svc.open_period,
    )
    await callback.answer()


# ── Reading quiz: user taps "Start Questions" ──────────────────────────── #

@router.callback_query(QuizCallback.filter(F.action == "reading_begin"))
async def on_reading_begin(
    callback: CallbackQuery,
    state: FSMContext,
    activity_service: ActivityService,
) -> None:
    """User tapped '▶️ Start Questions' after reading the passage."""
    data = await state.get_data()
    questions_raw: list[dict] = data.get(_QUESTIONS, [])
    lang = data.get(_LANG_KEY, "en")
    user_id = data.get(_USER_ID_KEY, 0)

    if not questions_raw:
        await callback.answer(t("quiz.error", lang), show_alert=True)
        return

    await state.set_state(QuizStates.answering)

    await activity_service.record(
        user_id, ActivityType.QUIZ_STARTED,
        metadata={"quiz_type": "reading", "total": len(questions_raw)},
    )

    first_q = QuizQuestion.model_validate(questions_raw[0])
    open_period = data.get("quiz_open_period", 20)
    await _send_question(
        bot=callback.bot,
        state=state,
        chat_id=data.get(_CHAT_ID, callback.message.chat.id),
        question=first_q,
        index=0,
        total=len(questions_raw),
        lang=lang,
        user_id=user_id,
        activity_service=activity_service,
        open_period=open_period,
    )
    # Edit the passage message to remove the Start/End buttons
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()


# ── Poll answer received ───────────────────────────────────────────────── #

@router.poll_answer()
async def on_poll_answer(
    poll_answer: PollAnswer,
    state: FSMContext,
    bot: Bot,
    activity_service: ActivityService,
    user_memory_service: UserMemoryService,
    feature_output_service: FeatureOutputService,
    settings_service: SettingsService,
) -> None:
    """Telegram delivers poll_answer when a user answers a quiz poll."""
    data = await state.get_data()

    poll_map: dict = data.get(_POLL_MAP, {})
    poll_id = poll_answer.poll_id
    if poll_id not in poll_map:
        return  # stale answer or poll from another context

    question_index: int = poll_map[poll_id]
    questions_raw: list[dict] = data.get(_QUESTIONS, [])
    if question_index >= len(questions_raw):
        return

    question = QuizQuestion.model_validate(questions_raw[question_index])
    lang = data.get(_LANG_KEY, "en")
    user_id: int = data.get(_USER_ID_KEY, 0)
    chat_id: int = data.get(_CHAT_ID, 0)
    total = len(questions_raw)

    chosen = poll_answer.option_ids[0] if poll_answer.option_ids else -1
    is_correct = chosen == question.correct_option

    correct_count = data.get(_CORRECT, 0)
    wrong_count   = data.get(_WRONG, 0)
    wrong_words   = data.get(_WRONG_WORDS, [])

    if is_correct:
        correct_count += 1
        activity_type = ActivityType.QUESTION_CORRECT
    else:
        wrong_count += 1
        activity_type = ActivityType.QUESTION_WRONG
        word = _extract_word_from_question(question)
        if word:
            wrong_words.append(word)
            try:
                await user_memory_service.record_weak_word(user_id, word)
            except Exception:
                logger.warning("on_poll_answer: weak_word update failed uid=%s", user_id)

    await activity_service.record(
        user_id, activity_type,
        metadata={
            "question_index": question_index,
            "correct": is_correct,
            "chosen": chosen,
        },
    )

    next_index = question_index + 1
    await state.update_data({
        _CORRECT:     correct_count,
        _WRONG:       wrong_count,
        _WRONG_WORDS: wrong_words,
        _CURRENT:     next_index,
    })

    if next_index < total:
        next_q = QuizQuestion.model_validate(questions_raw[next_index])
        open_period = data.get("quiz_open_period", 20)
        await _send_question(
            bot=bot,
            state=state,
            chat_id=chat_id,
            question=next_q,
            index=next_index,
            total=total,
            lang=lang,
            user_id=user_id,
            activity_service=activity_service,
            open_period=open_period,
        )
    else:
        await _show_results(
            bot=bot,
            state=state,
            chat_id=chat_id,
            lang=lang,
            user_id=user_id,
            correct=correct_count,
            wrong=wrong_count,
            total=total,
            wrong_words=wrong_words,
            activity_service=activity_service,
            feature_output_service=feature_output_service,
            output_id=data.get(_OUTPUT_ID, 0),
            start_ts=data.get(_START_TS, ""),
        )


# ── End quiz early ─────────────────────────────────────────────────────── #

@router.callback_query(QuizCallback.filter(F.action == "end"))
async def on_quiz_end(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
    activity_service: ActivityService,
) -> None:
    """User tapped End Quiz."""
    lang = await settings_service.get_language(callback.from_user.id)
    data = await state.get_data()
    user_id = data.get(_USER_ID_KEY, 0)

    await activity_service.record(
        user_id, ActivityType.QUIZ_COMPLETED,
        metadata={
            "aborted": True,
            "correct": data.get(_CORRECT, 0),
            "wrong": data.get(_WRONG, 0),
        },
    )
    await state.clear()
    await callback.message.edit_text(t("quiz.aborted", lang))
    await edit_to_dashboard(callback, lang)
    await callback.answer()


# ── Private helpers ────────────────────────────────────────────────────── #

async def _send_question(
    *,
    bot: Bot,
    state: FSMContext,
    chat_id: int,
    question: QuizQuestion,
    index: int,
    total: int,
    lang: str,
    user_id: int,
    activity_service: ActivityService,
    open_period: int = 20,
) -> None:
    """Send one question as a Telegram Quiz Poll and update FSM poll_map."""
    q_text = question.question[:_MAX_QUESTION]
    options = [InputPollOption(text=opt[:_MAX_OPTION]) for opt in question.options]
    explanation = (question.explanation or "")[:_MAX_EXPLANATION]

    # Telegram requires open_period between 5 and 600 seconds; None = no timer
    tg_open_period: int | None = None
    if open_period and 5 <= open_period <= 600:
        tg_open_period = open_period

    try:
        poll_msg = await bot.send_poll(
            chat_id=chat_id,
            question=q_text,
            options=options,
            type="quiz",
            correct_option_id=question.correct_option,
            explanation=explanation or None,
            is_anonymous=False,
            open_period=tg_open_period,
            reply_markup=get_quiz_abort_keyboard(lang),
        )

        data = await state.get_data()
        poll_map: dict = data.get(_POLL_MAP, {})
        poll_map[poll_msg.poll.id] = index
        await state.update_data({_POLL_MAP: poll_map})

        await activity_service.record(
            user_id, ActivityType.QUESTION_SENT,
            metadata={"question_index": index, "total": total},
        )
    except Exception:
        logger.exception("_send_question: failed to send poll idx=%d uid=%s", index, user_id)


async def _show_results(
    *,
    bot: Bot,
    state: FSMContext,
    chat_id: int,
    lang: str,
    user_id: int,
    correct: int,
    wrong: int,
    total: int,
    wrong_words: list[str],
    activity_service: ActivityService,
    feature_output_service: FeatureOutputService,
    output_id: int,
    start_ts: str,
) -> None:
    """Send quiz results message and record QUIZ_COMPLETED."""
    elapsed = 0
    try:
        start = datetime.fromisoformat(start_ts)
        elapsed = int((datetime.now(UTC) - start.replace(tzinfo=UTC)).total_seconds())
    except Exception:
        pass

    accuracy = round(correct / total * 100) if total > 0 else 0

    text = t("quiz.results", lang,
        correct=str(correct), wrong=str(wrong),
        total=str(total), accuracy=str(accuracy), time=str(elapsed),
    )
    if wrong_words:
        text += "\n\n" + t("quiz.weak_topics", lang, words=", ".join(wrong_words[:5]))

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=get_quiz_results_keyboard(lang),
    )

    await activity_service.record(
        user_id, ActivityType.QUIZ_COMPLETED,
        score=correct / total if total > 0 else 0.0,
        metadata={
            "correct": correct, "wrong": wrong,
            "total": total, "accuracy": accuracy,
            "time_seconds": elapsed, "wrong_words": wrong_words,
        },
    )
    await state.clear()


def _extract_word_from_question(question: QuizQuestion) -> str | None:
    """Try to extract the target word from a quiz question for weak_words tracking."""
    q = question.question
    m = re.search(r"['\u2018\u2019\u201c\u201d]([a-zA-Z ]{2,30})['\u2018\u2019\u201c\u201d]", q)
    if m:
        return m.group(1).strip().lower()
    if question.options and 0 <= question.correct_option < len(question.options):
        return question.options[question.correct_option][:30].lower().strip()
    return None
