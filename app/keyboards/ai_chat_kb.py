"""Inline keyboards for the AI Chat feature (Feature A)."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import AIChatCallback
from app.texts.messages import t


def get_ai_chat_session_keyboard(lang: str, session_id: int) -> InlineKeyboardMarkup:
    """Keyboard shown below the AI Chat welcome message.

    Provides two actions:
      - New Chat: clear history and start fresh
      - End Chat: close session and return to dashboard
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("ai_chat.btn_new", lang),
        callback_data=AIChatCallback(action="new", session_id=session_id),
    )
    builder.button(
        text=t("ai_chat.btn_end", lang),
        callback_data=AIChatCallback(action="end", session_id=session_id),
    )
    builder.adjust(2)
    return builder.as_markup()
