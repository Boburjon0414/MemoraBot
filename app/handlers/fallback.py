"""Catch-all fallback for messages that don't match any other handler or FSM
state. Must be included last in the root router so more specific handlers
always get first refusal.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.handlers.dashboard import send_dashboard
from app.services.settings_service import SettingsService
from app.services.user_service import UserService
from app.texts.messages import t

router = Router(name="fallback")


@router.message()
async def fallback_message(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
) -> None:
    """Politely redirect unmatched input: unregistered users are pointed at
    /start, registered users (with no active FSM state) get the dashboard.
    """
    current_state = await state.get_state()
    if current_state is not None:
        # Should be unreachable in V1 since every defined state has its own
        # catch-all handler, but kept as a safety net against silent drops.
        return

    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(t("prompt_use_start", "uz"))
        return

    lang = await settings_service.get_language(message.from_user.id)
    await send_dashboard(message, lang)
