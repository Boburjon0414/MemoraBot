"""`/start` entry point and the contact-based registration flow (Feature 1).

Registered first in the root router so that `/start` always wins and resets
FSM state, even if the user sends it mid-flow from inside another feature.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.handlers.dashboard import send_dashboard
from app.keyboards.contact_kb import get_contact_keyboard
from app.services.settings_service import SettingsService
from app.services.user_service import UserService
from app.states.bot_states import RegistrationStates
from app.texts.messages import t
from app.utils.formatters import format_full_name

logger = logging.getLogger(__name__)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
) -> None:
    """Greet the user: registered users go straight to the dashboard, new
    users are asked to share their contact.
    """
    await state.clear()
    user = await user_service.get_by_telegram_id(message.from_user.id)

    if user is not None:
        lang = await settings_service.get_language(user.telegram_id)
        await message.answer(t("welcome_back", lang, name=user.full_name))
        await send_dashboard(message, lang)
        return

    display_name = message.from_user.full_name or "do'stim"
    await message.answer(
        t("welcome_new", "uz", name=display_name),
        reply_markup=get_contact_keyboard("uz"),
    )
    await state.set_state(RegistrationStates.waiting_for_contact)


@router.message(RegistrationStates.waiting_for_contact, F.contact)
async def process_contact(message: Message, state: FSMContext, user_service: UserService) -> None:
    """Complete registration once the user shares their Telegram contact."""
    contact = message.contact
    assert contact is not None  # guaranteed by the F.contact filter

    if contact.user_id != message.from_user.id:
        # Telegram lets a user forward someone else's contact card; we only
        # want their own, since it's what identifies *this* account.
        await message.answer(t("contact_invalid", "uz"), reply_markup=get_contact_keyboard("uz"))
        return

    full_name = format_full_name(contact.first_name, contact.last_name)
    user = await user_service.register_user(
        telegram_id=message.from_user.id,
        full_name=full_name,
        phone_number=contact.phone_number,
        username=message.from_user.username,
    )

    await state.clear()
    await message.answer(
        t("registration_success", "uz", name=user.full_name),
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_dashboard(message, "uz")


@router.message(RegistrationStates.waiting_for_contact)
async def process_contact_invalid(message: Message) -> None:
    """Nudge the user if they send anything other than a contact while registering."""
    await message.answer(t("contact_prompt_retry", "uz"), reply_markup=get_contact_keyboard("uz"))
