"""Inline keyboards for the admin Grammar Lessons management panel."""

from __future__ import annotations

from app.database.models.grammar_topic import GrammarTopic
from app.keyboards.callback_data import AdminCallback, AdminGrammarCallback
from app.texts.messages import t

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

_TOPICS_PER_PAGE = 5   # topics per page in admin list view


def get_admin_grammar_menu_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Main admin Grammar Lessons menu."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("admin.grammar.btn.add_forward", lang),
        callback_data=AdminGrammarCallback(action="add_forward"),
    )
    builder.button(
        text=t("admin.grammar.btn.add_manual", lang),
        callback_data=AdminGrammarCallback(action="add_manual"),
    )
    builder.button(
        text=t("admin.grammar.btn.list", lang),
        callback_data=AdminGrammarCallback(action="list"),
    )
    builder.button(
        text=t("admin.grammar.btn.back", lang),
        callback_data=AdminCallback(action="overview"),
    )
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def get_admin_grammar_back_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Single back-to-grammar-menu button."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("admin.grammar.btn.back", lang),
        callback_data=AdminGrammarCallback(action="menu"),
    )
    return builder.as_markup()


def get_admin_grammar_list_keyboard(
    topics: list[GrammarTopic],
    lang: str = "uz",
    *,
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Paginated list of all grammar topics (active + inactive) with action buttons."""
    builder = InlineKeyboardBuilder()
    total_pages = max(1, (len(topics) + _TOPICS_PER_PAGE - 1) // _TOPICS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * _TOPICS_PER_PAGE
    page_topics = topics[start: start + _TOPICS_PER_PAGE]

    for topic in page_topics:
        status = "🟢" if topic.is_active else "🔴"
        label = f"{status} {topic.title}"
        builder.button(
            text=label,
            callback_data=AdminGrammarCallback(action="edit", topic_id=topic.id),
        )

    # Pagination row
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(("◀️", page - 1))
        if page < total_pages - 1:
            nav_buttons.append(("▶️", page + 1))
        for label, p in nav_buttons:
            builder.button(
                text=label,
                callback_data=AdminGrammarCallback(action="list", page=p),
            )

    builder.button(
        text=t("admin.grammar.btn.back", lang),
        callback_data=AdminGrammarCallback(action="menu"),
    )
    # Layout: one topic per row, nav buttons side-by-side, back alone
    nav_count = min(2, total_pages - 1) if total_pages > 1 else 0
    layout = [1] * len(page_topics)
    if nav_count:
        layout.append(nav_count)
    layout.append(1)
    builder.adjust(*layout)
    return builder.as_markup()


def get_admin_grammar_topic_keyboard(
    topic: GrammarTopic,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Per-topic management keyboard: edit fields, toggle, move, delete."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("admin.grammar.btn.edit_name", lang),
        callback_data=AdminGrammarCallback(action="edit_name", topic_id=topic.id),
    )
    builder.button(
        text=t("admin.grammar.btn.edit_button", lang),
        callback_data=AdminGrammarCallback(action="edit_button", topic_id=topic.id),
    )
    builder.button(
        text=t("admin.grammar.btn.edit_msgid", lang),
        callback_data=AdminGrammarCallback(action="edit_msgid", topic_id=topic.id),
    )
    # Toggle button reflects current state
    toggle_label = (
        t("admin.grammar.btn.toggle_disable", lang)
        if topic.is_active
        else t("admin.grammar.btn.toggle_enable", lang)
    )
    builder.button(
        text=toggle_label,
        callback_data=AdminGrammarCallback(action="toggle", topic_id=topic.id),
    )
    builder.button(
        text=t("admin.grammar.btn.move_up", lang),
        callback_data=AdminGrammarCallback(action="move_up", topic_id=topic.id),
    )
    builder.button(
        text=t("admin.grammar.btn.move_down", lang),
        callback_data=AdminGrammarCallback(action="move_down", topic_id=topic.id),
    )
    builder.button(
        text=t("admin.grammar.btn.delete", lang),
        callback_data=AdminGrammarCallback(action="delete", topic_id=topic.id),
    )
    builder.button(
        text=t("admin.grammar.btn.back", lang),
        callback_data=AdminGrammarCallback(action="list"),
    )
    builder.adjust(1, 1, 1, 1, 2, 1, 1)
    return builder.as_markup()


def get_admin_grammar_confirm_delete_keyboard(
    topic_id: int,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Confirm / cancel delete keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("admin.grammar.btn.confirm_delete", lang),
        callback_data=AdminGrammarCallback(action="delete_confirm", topic_id=topic_id),
    )
    builder.button(
        text=t("admin.grammar.btn.cancel", lang),
        callback_data=AdminGrammarCallback(action="edit", topic_id=topic_id),
    )
    builder.adjust(2)
    return builder.as_markup()


def get_admin_grammar_cancel_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Single cancel button for FSM input flows."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("admin.grammar.btn.cancel", lang),
        callback_data=AdminGrammarCallback(action="menu"),
    )
    return builder.as_markup()
