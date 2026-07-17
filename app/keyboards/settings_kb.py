"""Inline keyboard for the Settings screen."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import SettingsCallback
from app.texts.messages import t


def get_settings_keyboard(lang: str = "uz", notifications_enabled: bool = True) -> InlineKeyboardMarkup:
    """Language picker + notifications toggle + back button."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha", callback_data=SettingsCallback(action="set_lang", value="uz"))
    builder.button(text="🇬🇧 English", callback_data=SettingsCallback(action="set_lang", value="en"))
    builder.button(text="🇷🇺 Русский", callback_data=SettingsCallback(action="set_lang", value="ru"))

    notifications_label = (
        t("btn_notifications_on", lang) if notifications_enabled else t("btn_notifications_off", lang)
    )
    builder.button(text=notifications_label, callback_data=SettingsCallback(action="toggle_notifications"))
    builder.button(text=t("btn_back_home", lang), callback_data=SettingsCallback(action="home"))

    builder.adjust(3, 1, 1)
    return builder.as_markup()
