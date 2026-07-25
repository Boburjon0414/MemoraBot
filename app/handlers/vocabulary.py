"""My Vocabulary handlers (V1.6).

All handlers are deliberately thin — they translate Telegram events into
VocabularyService calls and render the results using formatters and
keyboards.  Zero business logic lives here.

Screens implemented
-------------------
  • List screen        — paginated word list with ⭐ / ✨ indicators
  • Search             — FSM state waiting for search text
  • Detail screen      — full word card with favorite, delete, prev/next
  • Update screen      — comparison view for pending system improvements
  • Delete confirm     — two-step confirmation before deletion

Navigation guarantee
--------------------
Every screen has a back path.  Handlers always pass `page` and
`search_query` through navigation so the user lands back in the right
place when pressing Back.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardMarkup

from app.handlers.dashboard import edit_to_dashboard
from app.keyboards.callback_data import DashboardCallback, VocabularyCallback, VocabularyWordCallback
from app.keyboards.vocabulary_kb import (
    get_vocab_delete_confirm_keyboard,
    get_vocabulary_detail_keyboard,
    get_vocabulary_list_keyboard,
    get_vocabulary_update_keyboard,
)
from app.repositories.vocabulary_repository import DEFAULT_PAGE_SIZE
from app.services.mnemonic_service import MnemonicService
from app.services.settings_service import SettingsService
from app.services.user_service import UserService
from app.services.vocabulary_service import VocabularyService
from app.states.bot_states import VocabularyStates
from app.texts.messages import t
from app.utils.formatters import format_vocab_detail, format_vocab_update_comparison

logger = logging.getLogger(__name__)

router = Router(name="vocabulary")


# ── Entry point from dashboard ─────────────────────────────────────────── #

@router.callback_query(DashboardCallback.filter(F.action == "vocabulary"))
async def open_vocabulary(
    callback: CallbackQuery,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
) -> None:
    """User tapped 'My Vocabulary' on the dashboard."""
    await state.clear()
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    await _render_list(callback, vocabulary_service, lang, db_user_id=user.id, page=0, search_query=None)
    await callback.answer()


# ── List screen ────────────────────────────────────────────────────────── #

@router.callback_query(VocabularyCallback.filter(F.action == "open"))
async def vocab_list_page(
    callback: CallbackQuery,
    callback_data: VocabularyCallback,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
) -> None:
    """Navigate to a page of the vocabulary list (also used by Back buttons)."""
    await state.clear()
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    search_query = callback_data.search_query or None
    await _render_list(
        callback, vocabulary_service, lang,
        db_user_id=user.id,
        page=callback_data.page,
        search_query=search_query,
    )
    await callback.answer()


@router.callback_query(VocabularyCallback.filter(F.action == "noop"))
async def vocab_noop(callback: CallbackQuery) -> None:
    """Absorb taps on the 'Page N/M' indicator button (no action intended)."""
    await callback.answer()


# ── Search ─────────────────────────────────────────────────────────────── #

@router.callback_query(VocabularyCallback.filter(F.action == "search"))
async def enter_vocab_search(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    """Enter search mode: show a prompt and wait for the user to type."""
    lang = await settings_service.get_language(callback.from_user.id)
    await state.set_state(VocabularyStates.searching)
    await callback.message.edit_text(
        t("vocab.search_prompt", lang),
        reply_markup=_search_cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(VocabularyStates.searching, F.text)
async def process_vocab_search(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
) -> None:
    """User typed a search query; show filtered results."""
    await state.clear()
    lang = await settings_service.get_language(message.from_user.id)
    user = await user_service.get_by_telegram_id(message.from_user.id)
    query = message.text.strip()

    entries, total = await vocabulary_service.get_page(
        user_id=user.id,
        page=0,
        search_query=query,
    )

    if total == 0:
        await message.answer(
            t("vocab.search_no_results", lang, query=query),
            reply_markup=_search_back_keyboard(lang),
        )
        return

    text = t("vocab.search_results_header", lang, query=query, total=str(total))
    await message.answer(
        text,
        reply_markup=get_vocabulary_list_keyboard(
            entries=entries,
            page=0,
            total=total,
            lang=lang,
            search_query=query,
        ),
    )


@router.callback_query(VocabularyCallback.filter(F.action == "cancel_search"))
async def cancel_vocab_search(
    callback: CallbackQuery,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
) -> None:
    """User cancelled search — go back to the unfiltered list."""
    await state.clear()
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    await _render_list(callback, vocabulary_service, lang, db_user_id=user.id, page=0, search_query=None)
    await callback.answer()


# ── Detail screen ──────────────────────────────────────────────────────── #

@router.callback_query(VocabularyWordCallback.filter(F.action == "detail"))
async def show_vocab_word(
    callback: CallbackQuery,
    callback_data: VocabularyWordCallback,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
    user_service: UserService,
) -> None:
    """Show the full detail card for a vocabulary entry."""
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service .get_by_telegram_id(callback.from_user.id)
    if user is None:
        return
    entry = await vocabulary_service.get_detail(
    user_id=user.id,
    entry_id=callback_data.entry_id,
    )

    if entry is None:
        # Entry was deleted (e.g. from another session) — go back to list.
        await _render_list(callback, vocabulary_service, lang, page=callback_data.page)
        await callback.answer(t("vocab.entry_not_found", lang))
        return

    search_query = callback_data.search_query or None
    prev_id, next_id = await vocabulary_service.get_adjacent_ids(
        user_id=entry.user_id,
        current_word=entry.word,
        search_query=search_query,
    )

    await callback.message.edit_text(
        format_vocab_detail(entry, lang),
        reply_markup=get_vocabulary_detail_keyboard(
            entry=entry,
            lang=lang,
            prev_id=prev_id,
            next_id=next_id,
            page=callback_data.page,
            search_query=search_query,
        ),
    )
    await callback.answer()


# ── Favorite toggle ────────────────────────────────────────────────────── #

@router.callback_query(VocabularyWordCallback.filter(F.action == "favorite"))
async def toggle_vocab_favorite(
    callback: CallbackQuery,
    callback_data: VocabularyWordCallback,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
    user_service: UserService,
) -> None:
    """Toggle the favorite flag and refresh the detail screen."""
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        return
    new_value = await vocabulary_service.toggle_favorite(
        user_id=user.id,
        entry_id=callback_data.entry_id,
        )

    answer_key = "vocab.answer_favorited" if new_value else "vocab.answer_unfavorited"
    await callback.answer(t(answer_key, lang))

    # Refresh detail screen in place
    entry = await vocabulary_service.get_detail(
        user_id=user.id,
        entry_id=callback_data.entry_id,
    )
    if entry is None:
        await _render_list(callback, vocabulary_service, lang, page=callback_data.page)
        return

    search_query = callback_data.search_query or None
    prev_id, next_id = await vocabulary_service.get_adjacent_ids(
        user_id=entry.user_id,
        current_word=entry.word,
        search_query=search_query,
    )
    await callback.message.edit_text(
        format_vocab_detail(entry, lang),
        reply_markup=get_vocabulary_detail_keyboard(
            entry=entry,
            lang=lang,
            prev_id=prev_id,
            next_id=next_id,
            page=callback_data.page,
            search_query=search_query,
        ),
    )


# ── Delete (two-step) ──────────────────────────────────────────────────── #

@router.callback_query(VocabularyWordCallback.filter(F.action == "delete"))
async def delete_vocab_word_ask(
    callback: CallbackQuery,
    callback_data: VocabularyWordCallback,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
    user_service: UserService,
) -> None:
    """First step: ask the user to confirm deletion."""
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        return
    entry = await vocabulary_service.get_detail(
        user_id=user.id, 
        entry_id=callback_data.entry_id,
        )
    if entry is None:
        await _render_list(callback, vocabulary_service, lang, page=callback_data.page)
        await callback.answer()
        return

    await callback.message.edit_text(
        t("vocab.delete_confirm_prompt", lang, word=entry.word.capitalize()),
        reply_markup=get_vocab_delete_confirm_keyboard(
            entry_id=entry.id,
            lang=lang,
            page=callback_data.page,
            search_query=callback_data.search_query or None,
        ),
    )
    await callback.answer()


@router.callback_query(VocabularyWordCallback.filter(F.action == "delete_confirm"))
async def delete_vocab_word_confirm(
    callback: CallbackQuery,
    callback_data: VocabularyWordCallback,
    user_service: UserService,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
) -> None:
    """Second step: perform the deletion and return to the list."""
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        return
    await vocabulary_service.delete(
        user_id=user.id, 
        entry_id=callback_data.entry_id,
        )
    await callback.answer(t("vocab.answer_deleted", lang))
    # Return to the list; clamp to page 0 if the deleted entry was the last
    # on its page (list re-renders naturally with updated count).
    await _render_list(
        callback, vocabulary_service, lang,
        db_user_id=user.id,
        page=callback_data.page,
        search_query=callback_data.search_query or None,
    )


# ── Pending update flow ────────────────────────────────────────────────── #

@router.callback_query(VocabularyWordCallback.filter(F.action == "view_update"))
async def view_pending_update(
    callback: CallbackQuery,
    callback_data: VocabularyWordCallback,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
    mnemonic_service: MnemonicService,
    user_service: UserService,
) -> None:
    """Show the comparison screen: current mnemonic vs pending improvement."""
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        return
    entry = await vocabulary_service.get_detail(user_id=user.id, entry_id=callback_data.entry_id)

    if entry is None or entry.pending_mnemonic_id is None:
        # Entry or pending update disappeared — go back to detail.
        await callback.answer(t("vocab.entry_not_found", lang))
        await _render_list(callback, vocabulary_service, lang, page=callback_data.page)
        return

    pending = await mnemonic_service.get_by_id(entry.pending_mnemonic_id)
    if pending is None:
        # Pending mnemonic was removed from the library — clear stale reference.
        await vocabulary_service.reject_pending_update(entry.id)
        await callback.answer(t("vocab.update_no_longer_available", lang))
        entry = await vocabulary_service.get_detail(user_id=user.id, entry_id=callback_data.entry_id)
        # Refresh detail screen
        search_query = callback_data.search_query or None
        prev_id, next_id = await vocabulary_service.get_adjacent_ids(
            user_id=entry.user_id, current_word=entry.word, search_query=search_query
        )
        await callback.message.edit_text(
            format_vocab_detail(entry, lang),
            reply_markup=get_vocabulary_detail_keyboard(
                entry=entry, lang=lang,
                prev_id=prev_id, next_id=next_id,
                page=callback_data.page, search_query=search_query,
            ),
        )
        return

    await callback.message.edit_text(
        format_vocab_update_comparison(entry, pending, lang),
        reply_markup=get_vocabulary_update_keyboard(
            entry_id=entry.id,
            lang=lang,
            page=callback_data.page,
            search_query=callback_data.search_query or None,
        ),
    )
    await callback.answer()


@router.callback_query(VocabularyWordCallback.filter(F.action == "accept_update"))
async def accept_pending_update(
    callback: CallbackQuery,
    callback_data: VocabularyWordCallback,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
    user_service: UserService,
) -> None:
    """User chose '✨ Update Mnemonic' — promote pending to active."""
    lang = await settings_service.get_language(callback.from_user.id)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        return
    try:
        entry = await vocabulary_service.accept_pending_update(callback_data.entry_id)
    except ValueError:
        await callback.answer(t("vocab.update_no_longer_available", lang), show_alert=True)
        await _render_list(callback, vocabulary_service, lang, page=callback_data.page)
        return

    await callback.answer(t("vocab.answer_updated", lang))
    search_query = callback_data.search_query or None
    prev_id, next_id = await vocabulary_service.get_adjacent_ids(
        user_id=entry.user_id, current_word=entry.word, search_query=search_query
    )
    await callback.message.edit_text(
        format_vocab_detail(entry, lang),
        reply_markup=get_vocabulary_detail_keyboard(
            entry=entry, lang=lang,
            prev_id=prev_id, next_id=next_id,
            page=callback_data.page, search_query=search_query,
        ),
    )


@router.callback_query(VocabularyWordCallback.filter(F.action == "reject_update"))
async def reject_pending_update(
    callback: CallbackQuery,
    callback_data: VocabularyWordCallback,
    settings_service: SettingsService,
    vocabulary_service: VocabularyService,
    user_service: UserService,
) -> None:
    """User chose 'Keep Current' — dismiss the pending update."""
    lang = await settings_service.get_language(callback.from_user.id)
    await vocabulary_service.reject_pending_update(callback_data.entry_id)
    await callback.answer(t("vocab.answer_kept_current", lang))

    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        return
    entry = await vocabulary_service.get_detail(
        user_id=user.id, 
        entry_id=callback_data.entry_id,
        )
    if entry is None:
        await _render_list(callback, vocabulary_service, lang, page=callback_data.page)
        return

    search_query = callback_data.search_query or None
    prev_id, next_id = await vocabulary_service.get_adjacent_ids(
        user_id=entry.user_id, current_word=entry.word, search_query=search_query
    )
    await callback.message.edit_text(
        format_vocab_detail(entry, lang),
        reply_markup=get_vocabulary_detail_keyboard(
            entry=entry, lang=lang,
            prev_id=prev_id, next_id=next_id,
            page=callback_data.page, search_query=search_query,
        ),
    )


# ── Private helpers ────────────────────────────────────────────────────── #

async def _render_list(
    callback: CallbackQuery,
    vocabulary_service: VocabularyService,
    lang: str,
    db_user_id: int,
    page: int = 0,
    search_query: str | None = None,
) -> None:
    """Render the vocabulary list screen into the current message.

    Handles the empty-state gracefully (shows a prompt to generate words).
    Clamps `page` down if it overshoots (e.g. after deleting the last
    entry on the last page).

    Args:
        db_user_id: The database users.id (NOT telegram_id). Callers must
                    resolve this via UserService before calling.
    """
    entries, total = await vocabulary_service.get_page(
        user_id=db_user_id,
        page=page,
        search_query=search_query,
    )

    # Clamp: if page is beyond the last page (deletion edge case), use page 0
    import math
    if total > 0 and page > 0:
        max_page = math.ceil(total / DEFAULT_PAGE_SIZE) - 1
        if page > max_page:
            page = max_page
            entries, total = await vocabulary_service.get_page(
                user_id=db_user_id,
                page=page,
                search_query=search_query,
            )

    if total == 0 and not search_query:
        await callback.message.edit_text(
            t("vocab.empty", lang),
            reply_markup=_empty_vocab_keyboard(lang),
        )
        return

    header = t("vocab.title", lang, total=str(total))
    if search_query:
        header = t("vocab.search_results_header", lang, query=search_query, total=str(total))

    await callback.message.edit_text(
        header,
        reply_markup=get_vocabulary_list_keyboard(
            entries=entries,
            page=page,
            total=total,
            lang=lang,
            search_query=search_query,
        ),
    )


def _empty_vocab_keyboard(lang: str) -> "InlineKeyboardMarkup":
    """Keyboard shown when the user has no vocabulary entries yet."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from app.keyboards.callback_data import DashboardCallback
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("btn_mnevoca", lang),
        callback_data=DashboardCallback(action="mnevoca"),
    )
    builder.button(
        text=t("btn_back_home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    builder.adjust(1)
    return builder.as_markup()


def _search_cancel_keyboard(lang: str) -> "InlineKeyboardMarkup":
    """Minimal keyboard shown while waiting for a search query."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("vocab.btn.cancel_search", lang),
        callback_data=VocabularyCallback(action="cancel_search", page=0, search_query=""),
    )
    builder.adjust(1)
    return builder.as_markup()


def _search_back_keyboard(lang: str) -> "InlineKeyboardMarkup":
    """Keyboard shown on the search-no-results screen."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("vocab.btn.back_to_list", lang),
        callback_data=VocabularyCallback(action="open", page=0, search_query=""),
    )
    builder.adjust(1)
    return builder.as_markup()
