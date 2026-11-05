"""Inline keyboards for the Grammar Learning feature (Learn → Grammar)."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.grammar_topic import GrammarTopic
from app.keyboards.callback_data import DashboardCallback, GrammarCallback
from app.texts.messages import t

_TOPICS_PER_PAGE = 8   # topics shown per keyboard page


def get_learn_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Learn section — shows Grammar (and future Learn sub-features)."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("learn.btn.grammar", lang),
        callback_data=GrammarCallback(action="topics", topic_id=0),
    )
    builder.button(
        text=t("btn_home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_grammar_topics_keyboard(
    topics: list[GrammarTopic],
    lang: str,
    *,
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Grammar topic selection keyboard with pagination.

    Topics are shown 8 per page.  Navigation row appears when there is
    more than one page.
    """
    builder = InlineKeyboardBuilder()
    total_pages = max(1, (len(topics) + _TOPICS_PER_PAGE - 1) // _TOPICS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * _TOPICS_PER_PAGE
    page_topics = topics[start: start + _TOPICS_PER_PAGE]

    for topic in page_topics:
        # Use admin-configured button_name if set, else fall back to title
        label = topic.button_name or topic.title
        builder.button(
            text=label,
            callback_data=GrammarCallback(action="open_topic", topic_id=topic.id),
        )

    # Pagination row (only when multiple pages exist)
    if total_pages > 1:
        if page > 0:
            builder.button(
                text="◀️",
                callback_data=GrammarCallback(action="topics", topic_id=0, page=page - 1),
            )
        if page < total_pages - 1:
            builder.button(
                text="▶️",
                callback_data=GrammarCallback(action="topics", topic_id=0, page=page + 1),
            )

    builder.button(
        text=t("btn_home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    # Layout: one topic per row, nav buttons on same row, home alone
    builder.adjust(*([1] * len(page_topics)), 2 if total_pages > 1 and 0 < page < total_pages - 1 else 1, 1)
    return builder.as_markup()


def get_lesson_actions_keyboard(
    topic_id: int, lang: str
) -> InlineKeyboardMarkup:
    """Shown after a grammar lesson is displayed.

    Buttons: ❓ Ask AI | 🧠 Test Yourself | ⬅️ Back to Grammar
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("grammar.btn.ask_ai", lang),
        callback_data=GrammarCallback(action="ask_ai", topic_id=topic_id),
    )
    builder.button(
        text=t("grammar.btn.test", lang),
        callback_data=GrammarCallback(action="test", topic_id=topic_id),
    )
    builder.button(
        text=t("grammar.btn.back_topics", lang),
        callback_data=GrammarCallback(action="topics", topic_id=0),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_grammar_qa_abort_keyboard(topic_id: int, lang: str) -> InlineKeyboardMarkup:
    """Exit grammar Q&A mode and return to the lesson screen."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("grammar.btn.stop_asking", lang),
        callback_data=GrammarCallback(action="open_topic", topic_id=topic_id),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_grammar_quiz_results_keyboard(
    topic_id: int, lang: str
) -> InlineKeyboardMarkup:
    """Shown after grammar quiz results."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("grammar.btn.test_again", lang),
        callback_data=GrammarCallback(action="test", topic_id=topic_id),
    )
    builder.button(
        text=t("grammar.btn.back_topics", lang),
        callback_data=GrammarCallback(action="topics", topic_id=0),
    )
    builder.button(
        text=t("btn_home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    builder.adjust(1)
    return builder.as_markup()
