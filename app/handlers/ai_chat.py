"""AI Chat handlers (Feature A + A.2): full Tool Calling Layer pipeline.

Every handler stamps the tool_context_template with the resolved user_id
and user_context before constructing AIChatService.
"""

from __future__ import annotations

import dataclasses
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core.exceptions import AIProviderError
from app.database.models.learning_activity import ActivityType
from app.handlers.dashboard import edit_to_dashboard, send_dashboard
from app.keyboards.ai_chat_kb import get_ai_chat_session_keyboard
from app.keyboards.callback_data import AIChatCallback, DashboardCallback
from app.services.activity_service import ActivityService
from app.services.ai_chat_service import AIChatService
from app.services.ai.router import AIRouter
from app.services.context.context_builder import ContextBuilder
from app.services.context.memory_update_hook import MemoryUpdateHook
from app.services.context.user_context import UserContext
from app.services.context.user_context_service import UserContextService
from app.services.feature_output_service import FeatureOutputService
from app.services.settings_service import SettingsService
from app.services.tools.base import ToolContext
from app.services.tools.planner import AIPlanner
from app.services.user_service import UserService
from app.states.bot_states import AIChatStates
from app.texts.messages import t

logger = logging.getLogger(__name__)
router = Router(name="ai_chat")
_SESSION_KEY = "ai_chat_session_id"


def _make_svc(
    ai_router: AIRouter,
    feature_output_service: FeatureOutputService,
    planner: AIPlanner | None,
    context_builder: ContextBuilder | None,
    memory_update_hook: MemoryUpdateHook | None,
) -> AIChatService:
    return AIChatService(
        ai_router=ai_router,
        feature_output_service=feature_output_service,
        planner=planner,
        context_builder=context_builder,
        memory_hook=memory_update_hook,
    )


def _stamp_tool_context(
    template: ToolContext,
    user_id: int,
    user_context: UserContext,
) -> ToolContext:
    """Return a new ToolContext with user_id and user_context filled in."""
    return dataclasses.replace(template, user_id=user_id, user_context=user_context)


# ── Entry point ────────────────────────────────────────────────────────── #

@router.callback_query(DashboardCallback.filter(F.action == "ai_chat"))
async def on_ai_chat_enter(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
    user_service: UserService,
    user_context_service: UserContextService,
    feature_output_service: FeatureOutputService,
    ai_router: AIRouter | None,
    ai_planner: AIPlanner | None,
    context_builder: ContextBuilder | None,
    memory_update_hook: MemoryUpdateHook | None,
) -> None:
    lang = await settings_service.get_language(callback.from_user.id)
    if ai_router is None:
        await callback.answer(t("ai_chat.no_router", lang), show_alert=True)
        return

    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(t("ai_chat.error", lang), show_alert=True)
        return

    user_context = await user_context_service.build(user.id)
    svc = _make_svc(ai_router, feature_output_service, ai_planner, context_builder, memory_update_hook)
    session_id, _ = await svc.get_or_create_session(user_id=user.id, user_context=user_context)

    await state.set_state(AIChatStates.in_session)
    await state.update_data({_SESSION_KEY: session_id})
    await callback.message.edit_text(
        t("ai_chat.welcome", lang),
        reply_markup=get_ai_chat_session_keyboard(lang, session_id),
    )
    await callback.answer()


# ── Chat turn ──────────────────────────────────────────────────────────── #

@router.message(AIChatStates.in_session, F.text)
async def on_chat_message(
    message: Message,
    state: FSMContext,
    settings_service: SettingsService,
    user_service: UserService,
    user_context_service: UserContextService,
    feature_output_service: FeatureOutputService,
    activity_service: ActivityService,
    ai_router: AIRouter | None,
    ai_planner: AIPlanner | None,
    context_builder: ContextBuilder | None,
    memory_update_hook: MemoryUpdateHook | None,
    tool_context_template: ToolContext | None,
) -> None:
    lang = await settings_service.get_language(message.from_user.id)
    if ai_router is None:
        await message.answer(t("ai_chat.no_router", lang))
        return

    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer(t("ai_chat.error", lang))
        return

    fsm_data = await state.get_data()
    session_id = fsm_data.get(_SESSION_KEY)
    if not session_id:
        await state.clear()
        await message.answer(t("ai_chat.error", lang))
        return

    user_context = await user_context_service.build(user.id)

    # Stamp tool_context with this request's user
    tool_context = None
    if tool_context_template is not None:
        tool_context = _stamp_tool_context(tool_context_template, user.id, user_context)

    svc = _make_svc(ai_router, feature_output_service, ai_planner, context_builder, memory_update_hook)
    thinking_msg = await message.answer(t("ai_chat.thinking", lang))

    try:
        reply = await svc.chat(
            user_id=user.id,
            session_id=session_id,
            user_message=message.text,
            user_context=user_context,
            tool_context=tool_context,
        )
    except AIProviderError:
        logger.warning("on_chat_message: AIProviderError uid=%s", user.id)
        await thinking_msg.edit_text(t("ai_chat.error", lang))
        return
    except Exception:
        logger.exception("on_chat_message: unexpected error uid=%s", user.id)
        await thinking_msg.edit_text(t("ai_chat.error", lang))
        return

    await thinking_msg.edit_text(reply)
    await activity_service.record(
        user.id,
        ActivityType.AI_CHAT_MESSAGE,
        metadata={"session_id": session_id, "chars": len(message.text)},
    )


# ── Session controls ───────────────────────────────────────────────────── #

@router.callback_query(AIChatCallback.filter(F.action == "end"))
async def on_chat_end(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    lang = await settings_service.get_language(callback.from_user.id)
    await state.clear()
    await callback.answer(t("ai_chat.session_ended", lang))
    await edit_to_dashboard(callback, lang)


@router.callback_query(AIChatCallback.filter(F.action == "new"))
async def on_chat_new(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
    user_service: UserService,
    user_context_service: UserContextService,
    feature_output_service: FeatureOutputService,
    ai_router: AIRouter | None,
    ai_planner: AIPlanner | None,
    context_builder: ContextBuilder | None,
    memory_update_hook: MemoryUpdateHook | None,
) -> None:
    lang = await settings_service.get_language(callback.from_user.id)
    if ai_router is None:
        await callback.answer(t("ai_chat.no_router", lang), show_alert=True)
        return
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(t("ai_chat.error", lang), show_alert=True)
        return

    user_context = await user_context_service.build(user.id)
    svc = _make_svc(ai_router, feature_output_service, ai_planner, context_builder, memory_update_hook)
    session_id, _ = await svc.new_session(user_id=user.id)

    await state.set_state(AIChatStates.in_session)
    await state.update_data({_SESSION_KEY: session_id})
    await callback.message.edit_text(
        t("ai_chat.welcome", lang),
        reply_markup=get_ai_chat_session_keyboard(lang, session_id),
    )
    await callback.answer(t("ai_chat.new_session", lang))


@router.message(AIChatStates.in_session, Command("end"))
async def on_chat_end_command(
    message: Message,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    lang = await settings_service.get_language(message.from_user.id)
    await state.clear()
    await message.answer(t("ai_chat.session_ended", lang))
    await send_dashboard(message, lang)
