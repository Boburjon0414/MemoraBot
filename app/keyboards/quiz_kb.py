"""Inline keyboards for the Quiz feature (Feature C)."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import DashboardCallback, QuizCallback
from app.texts.messages import t


def get_quiz_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Quiz type selection keyboard — shown when user enters quiz mode."""
    builder = InlineKeyboardBuilder()

    quiz_types = [
        ("vocabulary", t("quiz.btn.vocabulary", lang)),
        ("grammar",    t("quiz.btn.grammar", lang)),
        ("gap_fill",   t("quiz.btn.gap_fill", lang)),
        ("reading",    t("quiz.btn.reading", lang)),
        ("listening",  t("quiz.btn.listening", lang)),
        ("mixed",      t("quiz.btn.mixed", lang)),
    ]
    for qtype, label in quiz_types:
        builder.button(
            text=label,
            callback_data=QuizCallback(action="start", quiz_type=qtype),
        )

    builder.button(
        text=t("btn_home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_quiz_abort_keyboard(lang: str, output_id: int = 0) -> InlineKeyboardMarkup:
    """Single 'End Quiz' button shown between questions."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("quiz.btn.end", lang),
        callback_data=QuizCallback(action="end", output_id=output_id),
    )
    return builder.as_markup()


def get_quiz_results_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard shown after quiz results — start new quiz or go home."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("quiz.btn.new_quiz", lang),
        callback_data=QuizCallback(action="start", quiz_type="mixed"),
    )
    builder.button(
        text=t("btn_home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_reading_start_keyboard(lang: str, output_id: int = 0) -> InlineKeyboardMarkup:
    """Keyboard shown after the passage is displayed — user taps to begin questions."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("quiz.btn.reading_start", lang),
        callback_data=QuizCallback(action="reading_begin", output_id=output_id),
    )
    builder.button(
        text=t("quiz.btn.end", lang),
        callback_data=QuizCallback(action="end", output_id=output_id),
    )
    builder.adjust(1)
    return builder.as_markup()
