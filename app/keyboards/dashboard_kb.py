"""The main dashboard inline keyboard (Feature 1)."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import DashboardCallback, LearnCallback
from app.texts.messages import t


def get_dashboard_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Build the main dashboard keyboard.

    Layout: MneVoca, My Vocabulary, AI Chat, Quiz, Statistics,
    Invite Friends, Settings, About.
    Button grid: 2-2-2-2 (8 buttons, pairs of 2).
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_mnevoca", lang),       callback_data=DashboardCallback(action="mnevoca"))
    builder.button(text=t("btn_my_vocabulary", lang),  callback_data=DashboardCallback(action="vocabulary"))
    builder.button(text=t("btn_ai_chat", lang),        callback_data=DashboardCallback(action="ai_chat"))
    builder.button(text=t("btn_quiz", lang),           callback_data=DashboardCallback(action="quiz"))
    builder.button(text=t("btn_learn", lang),          callback_data=DashboardCallback(action="learn"))
    builder.button(text=t("btn_statistics", lang),     callback_data=DashboardCallback(action="statistics"))
    builder.button(text=t("btn_invite_friends", lang), callback_data=DashboardCallback(action="invite_friends"))
    builder.button(text=t("btn_settings", lang),       callback_data=DashboardCallback(action="settings"))
    builder.button(text=t("btn_about", lang),          callback_data=DashboardCallback(action="about"))
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def get_back_to_dashboard_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """A single 'back to dashboard' button, used from screens like About."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_back_home", lang), callback_data=DashboardCallback(action="home"))
    return builder.as_markup()
