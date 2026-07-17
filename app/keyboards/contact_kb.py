"""Reply keyboard used to request the user's Telegram contact during registration."""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.texts.messages import t


def get_contact_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """A single-button reply keyboard that requests the user's own contact.

    One tap shares both full name and phone number at once (Telegram's
    `request_contact` shares the user's own saved contact info), which is
    exactly what Feature 1 asks for.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("share_contact_button", lang), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
