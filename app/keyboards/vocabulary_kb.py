"""Inline keyboards for the My Vocabulary flow (V1.6).

Screens
-------
  List screen     — paginated word buttons + search + home
  Detail screen   — favorite toggle, delete, prev/next, back, pending update
  Update screen   — update mnemonic vs keep current (shown when pending exists)

Every screen has a natural exit path (back to list or home), satisfying
the "user should never get lost" UX requirement.
"""

from __future__ import annotations

import math

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.vocabulary import VocabularyEntry
from app.keyboards.callback_data import DashboardCallback, VocabularyCallback, VocabularyWordCallback
from app.texts.messages import t


def get_vocabulary_list_keyboard(
    entries: list[VocabularyEntry],
    page: int,
    total: int,
    lang: str,
    page_size: int = 8,
    search_query: str | None = None,
) -> InlineKeyboardMarkup:
    """Build the My Vocabulary list screen keyboard.

    Layout:
      [word buttons — one per entry, with ⭐ and ✨ indicators]
      [⬅ Prev]  [Page N/M]  [Next ➡]   (only when multiple pages)
      [🔍 Search]
      [🏠 Home]
    """
    builder = InlineKeyboardBuilder()

    # ── Word entry buttons ─────────────────────────────────────────────── #
    for entry in entries:
        label = _list_item_label(entry)
        builder.button(
            text=label,
            callback_data=VocabularyWordCallback(
                action="detail",
                entry_id=entry.id,
                page=page,
            ),
        )

    builder.adjust(1)  # one word per row

    # ── Pagination row ─────────────────────────────────────────────────── #
    total_pages = max(1, math.ceil(total / page_size))
    if total_pages > 1:
        nav = InlineKeyboardBuilder()
        if page > 0:
            nav.button(
                text=t("vocab.btn.prev", lang),
                callback_data=VocabularyCallback(
                    action="open",
                    page=page - 1,
                    search_query=search_query or "",
                ),
            )
        nav.button(
            text=t("vocab.page_indicator", lang, current=str(page + 1), total=str(total_pages)),
            callback_data=VocabularyCallback(action="noop", page=page, search_query=""),
        )
        if page < total_pages - 1:
            nav.button(
                text=t("vocab.btn.next", lang),
                callback_data=VocabularyCallback(
                    action="open",
                    page=page + 1,
                    search_query=search_query or "",
                ),
            )
        nav.adjust(3)
        builder.attach(nav)

    # ── Utility buttons ────────────────────────────────────────────────── #
    utility = InlineKeyboardBuilder()
    utility.button(
        text=t("vocab.btn.search", lang),
        callback_data=VocabularyCallback(action="search", page=0, search_query=""),
    )
    if search_query:
        # Offer to clear the current search filter
        utility.button(
            text=t("vocab.btn.clear_search", lang),
            callback_data=VocabularyCallback(action="open", page=0, search_query=""),
        )
    utility.button(
        text=t("btn_back_home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    utility.adjust(1)
    builder.attach(utility)

    return builder.as_markup()


def get_vocabulary_detail_keyboard(
    entry: VocabularyEntry,
    lang: str,
    prev_id: int | None,
    next_id: int | None,
    page: int,
    search_query: str | None = None,
) -> InlineKeyboardMarkup:
    """Build the word detail screen keyboard.

    Layout when NO pending update:
      [⭐ Favorite / ✅ Favorited]  [🗑 Delete]
      [⬅ Prev]  [➡ Next]            (when adjacent entries exist)
      [✨ Update Available]          (only when pending_mnemonic_id is set)
      [⬅ Back to Vocabulary]

    The favorite button label reflects current state.
    """
    builder = InlineKeyboardBuilder()

    # ── Favorite toggle ────────────────────────────────────────────────── #
    fav_key = "vocab.btn.unfavorite" if entry.is_favorite else "vocab.btn.favorite"
    builder.button(
        text=t(fav_key, lang),
        callback_data=VocabularyWordCallback(
            action="favorite",
            entry_id=entry.id,
            page=page,
            search_query=search_query or "",
        ),
    )

    # ── Delete ────────────────────────────────────────────────────────── #
    builder.button(
        text=t("vocab.btn.delete", lang),
        callback_data=VocabularyWordCallback(
            action="delete",
            entry_id=entry.id,
            page=page,
            search_query=search_query or "",
        ),
    )
    builder.adjust(2)  # favorite + delete on the same row

    # ── Prev / Next navigation ─────────────────────────────────────────── #
    if prev_id is not None or next_id is not None:
        nav = InlineKeyboardBuilder()
        if prev_id is not None:
            nav.button(
                text=t("vocab.btn.prev_word", lang),
                callback_data=VocabularyWordCallback(
                    action="detail",
                    entry_id=prev_id,
                    page=page,
                    search_query=search_query or "",
                ),
            )
        if next_id is not None:
            nav.button(
                text=t("vocab.btn.next_word", lang),
                callback_data=VocabularyWordCallback(
                    action="detail",
                    entry_id=next_id,
                    page=page,
                    search_query=search_query or "",
                ),
            )
        nav.adjust(2)
        builder.attach(nav)

    # ── Pending update indicator ───────────────────────────────────────── #
    if entry.pending_mnemonic_id is not None:
        pending_row = InlineKeyboardBuilder()
        pending_row.button(
            text=t("vocab.btn.view_update", lang),
            callback_data=VocabularyWordCallback(
                action="view_update",
                entry_id=entry.id,
                page=page,
                search_query=search_query or "",
            ),
        )
        pending_row.adjust(1)
        builder.attach(pending_row)

    # ── Back to list ──────────────────────────────────────────────────── #
    back_row = InlineKeyboardBuilder()
    back_row.button(
        text=t("vocab.btn.back_to_list", lang),
        callback_data=VocabularyCallback(
            action="open",
            page=page,
            search_query=search_query or "",
        ),
    )
    back_row.adjust(1)
    builder.attach(back_row)

    return builder.as_markup()


def get_vocabulary_update_keyboard(
    entry_id: int,
    lang: str,
    page: int,
    search_query: str | None = None,
) -> InlineKeyboardMarkup:
    """Keyboard shown on the pending-update comparison screen.

    Layout:
      [✨ Update Mnemonic]
      [Keep Current]
      [⬅ Back]
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("vocab.btn.accept_update", lang),
        callback_data=VocabularyWordCallback(
            action="accept_update",
            entry_id=entry_id,
            page=page,
            search_query=search_query or "",
        ),
    )
    builder.button(
        text=t("vocab.btn.keep_current", lang),
        callback_data=VocabularyWordCallback(
            action="reject_update",
            entry_id=entry_id,
            page=page,
            search_query=search_query or "",
        ),
    )
    builder.button(
        text=t("vocab.btn.back_to_word", lang),
        callback_data=VocabularyWordCallback(
            action="detail",
            entry_id=entry_id,
            page=page,
            search_query=search_query or "",
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_vocab_delete_confirm_keyboard(
    entry_id: int,
    lang: str,
    page: int,
    search_query: str | None = None,
) -> InlineKeyboardMarkup:
    """Confirmation keyboard before deleting a vocabulary entry."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("vocab.btn.delete_confirm", lang),
        callback_data=VocabularyWordCallback(
            action="delete_confirm",
            entry_id=entry_id,
            page=page,
            search_query=search_query or "",
        ),
    )
    builder.button(
        text=t("vocab.btn.delete_cancel", lang),
        callback_data=VocabularyWordCallback(
            action="detail",
            entry_id=entry_id,
            page=page,
            search_query=search_query or "",
        ),
    )
    builder.adjust(2)
    return builder.as_markup()


# ── Private helpers ────────────────────────────────────────────────────── #

def _list_item_label(entry: VocabularyEntry) -> str:
    """Format one word button label for the list screen.

    Examples:
      'abandon'          → 'abandon'
      (favorite)         → '⭐ abandon'
      (pending update)   → '✨ abandon'
      (both)             → '⭐✨ abandon'
    """
    prefix = ""
    if entry.is_favorite:
        prefix += "⭐"
    if entry.pending_mnemonic_id is not None:
        prefix += "✨"
    if prefix:
        prefix += " "
    return f"{prefix}{entry.word.capitalize()}"
