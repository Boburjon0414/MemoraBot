"""MneVoca handlers (Feature 2): the core mnemonic-generation flow.

Deliberately thin — all real work (calling the AI provider, caching,
regenerating, saving ratings, quota tracking) happens in `MnemonicService`,
`MnemonicFeedbackService`, and `UsageService`. This module only translates
between Telegram events and those services.

V1.2: `process_word` now checks the free-plan quota (only for words that
would actually require a fresh AI generation — cached words are always
free), and `regenerate_mnemonic` passes the specific version being
regenerated away from through to `MnemonicService.regenerate`, so its
implicit "not good enough" signal is tracked accurately.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core.exceptions import AIProviderError
from app.database.models.learning_activity import ActivityType
from app.handlers.dashboard import edit_to_dashboard
from app.keyboards.callback_data import DashboardCallback, MneVocaCallback, MnemonicRatingCallback
from app.keyboards.mnevoca_kb import get_mnevoca_entry_keyboard, get_mnevoca_result_keyboard
from app.services.activity_service import ActivityService
from app.services.mnemonic_feedback_service import MnemonicFeedbackService
from app.services.mnemonic_service import MnemonicService
from app.services.settings_service import SettingsService
from app.services.usage_service import UsageService
from app.services.user_service import UserService
from app.services.vocabulary_service import VocabularyService
from app.states.bot_states import MneVocaStates
from app.texts.messages import t
from app.utils.formatters import format_mnemonic_result
from app.utils.validators import is_valid_english_word

logger = logging.getLogger(__name__)

router = Router(name="mnevoca")


@router.callback_query(DashboardCallback.filter(F.action == "mnevoca"))
async def enter_mnevoca(callback: CallbackQuery, state: FSMContext, settings_service: SettingsService) -> None:
    """User tapped 'MneVoca' on the dashboard: enter vocabulary mode."""
    lang = await settings_service.get_language(callback.from_user.id)
    await state.set_state(MneVocaStates.waiting_for_word)
    await callback.message.edit_text(t("mnevoca_prompt", lang), reply_markup=get_mnevoca_entry_keyboard(lang))
    await callback.answer()


@router.callback_query(MneVocaCallback.filter(F.action == "another"))
async def another_word(callback: CallbackQuery, state: FSMContext, settings_service: SettingsService) -> None:
    """User wants to look up a different word right after seeing a result."""
    lang = await settings_service.get_language(callback.from_user.id)
    await state.set_state(MneVocaStates.waiting_for_word)
    await callback.message.edit_text(t("mnevoca_prompt", lang), reply_markup=get_mnevoca_entry_keyboard(lang))
    await callback.answer()


@router.callback_query(MneVocaCallback.filter(F.action == "home"))
async def mnevoca_home(callback: CallbackQuery, state: FSMContext, settings_service: SettingsService) -> None:
    await state.clear()
    lang = await settings_service.get_language(callback.from_user.id)
    await edit_to_dashboard(callback, lang)
    await callback.answer()


@router.message(MneVocaStates.waiting_for_word, F.text)
async def process_word(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    mnemonic_service: MnemonicService,
    feedback_service: MnemonicFeedbackService,
    usage_service: UsageService,
    vocabulary_service: VocabularyService,  # V1.6: auto-save
    activity_service: ActivityService,       # Step 1: event log
) -> None:
    """Generate (or serve from the library) and send a mnemonic for the typed word."""
    word = message.text.strip()
    lang = await settings_service.get_language(message.from_user.id)

    if not is_valid_english_word(word):
        await message.answer(t("mnevoca_invalid_word", lang))
        return

    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        # Defensive: MneVoca is only reachable via the dashboard, which is
        # only reachable after registration, so this should not normally happen.
        logger.warning("Unregistered telegram_id=%s reached MneVoca word input", message.from_user.id)
        await state.clear()
        await message.answer(t("mnevoca_error", lang))
        return

    # Free-plan quota only applies to words that would need a fresh AI call —
    # anything already in the library is free regardless of quota.
    would_generate = await mnemonic_service.would_require_generation(word)
    if would_generate and not await usage_service.has_quota_remaining(message.from_user.id):
        await message.answer(t("free_plan_limit_reached", lang, limit=str(usage_service.limit)))
        return

    thinking_message = await message.answer(t("mnevoca_generating", lang))

    try:
        entry = await mnemonic_service.get_or_generate(user_id=user.id, word=word)
    except AIProviderError:
        await thinking_message.edit_text(t("mnevoca_error", lang))
        return

    if would_generate:
        await usage_service.record_generation(message.from_user.id)

    user_rating = await feedback_service.get_user_rating(
        telegram_id=message.from_user.id, mnemonic_history_id=entry.id
    )
    await thinking_message.edit_text(
        format_mnemonic_result(entry, lang),
        reply_markup=get_mnevoca_result_keyboard(lang, entry.id, user_rating),
    )

    # V1.6: Auto-save to personal vocabulary.
    # Idempotent: creates on first lookup, detects system upgrades on repeat
    # lookups, ignores manual regenerations (same prompt_version).
    vocab_entry = await vocabulary_service.save_from_mnemonic(user_id=user.id, mnemonic=entry)

    # Step 1: Record learning activity events.
    # Both calls are fire-and-forget: failures are logged as warnings and
    # never interrupt the primary mnemonic flow.
    await activity_service.record(
        user.id,
        ActivityType.MNEMONIC_GENERATED,
        mnemonic_id=entry.id,
        metadata={"word": entry.word, "was_cache_hit": not would_generate},
    )
    if vocab_entry is not None:
        await activity_service.record(
            user.id,
            ActivityType.VOCABULARY_SAVED,
            mnemonic_id=entry.id,
            vocabulary_entry_id=vocab_entry.id,
            metadata={"word": entry.word},
        )

@router.message(MneVocaStates.waiting_for_word)
async def process_word_invalid_type(message: Message, settings_service: SettingsService) -> None:
    """Catch non-text input (stickers, photos, ...) while waiting for a word."""
    lang = await settings_service.get_language(message.from_user.id)
    await message.answer(t("mnevoca_invalid_word", lang))


@router.callback_query(MneVocaCallback.filter(F.action == "regenerate"))
async def regenerate_mnemonic(
    callback: CallbackQuery,
    callback_data: MneVocaCallback,
    user_service: UserService,
    settings_service: SettingsService,
    mnemonic_service: MnemonicService,
    feedback_service: MnemonicFeedbackService,
    vocabulary_service: VocabularyService,  # V1.6: auto-save
) -> None:
    """Task 4: "🔄 Generate Another Mnemonic" — ignore the cache, force a new version."""
    lang = await settings_service.get_language(callback.from_user.id)
    await callback.answer()

    existing = await mnemonic_service.get_by_id(callback_data.mnemonic_id)
    if existing is None:
        await callback.message.edit_text(t("mnevoca_error", lang))
        return

    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.message.edit_text(t("mnevoca_error", lang))
        return

    await callback.message.edit_text(t("mnevoca_generating", lang))

    try:
        entry = await mnemonic_service.regenerate(
            user_id=user.id, word=existing.word, source_mnemonic_id=existing.id
        )
    except AIProviderError:
        await callback.message.edit_text(t("mnevoca_error", lang))
        return

    # V1.6: Auto-save hook. Same prompt_version as active system, so
    # save_from_mnemonic treats this as a same-version regeneration and
    # does NOT overwrite the user's active vocabulary entry.
    await vocabulary_service.save_from_mnemonic(user_id=user.id, mnemonic=entry)

    user_rating = await feedback_service.get_user_rating(
        telegram_id=callback.from_user.id, mnemonic_history_id=entry.id
    )
    await callback.message.edit_text(
        format_mnemonic_result(entry, lang),
        reply_markup=get_mnevoca_result_keyboard(lang, entry.id, user_rating),
    )


@router.callback_query(MnemonicRatingCallback.filter())
async def rate_mnemonic(
    callback: CallbackQuery,
    callback_data: MnemonicRatingCallback,
    settings_service: SettingsService,
    feedback_service: MnemonicFeedbackService,
) -> None:
    """Task 5: 👍/👎 — store the rating and reflect the choice on the keyboard."""
    lang = await settings_service.get_language(callback.from_user.id)
    is_helpful = callback_data.value == "up"

    feedback = await feedback_service.rate(
        telegram_id=callback.from_user.id,
        mnemonic_history_id=callback_data.mnemonic_id,
        is_helpful=is_helpful,
    )
    if feedback is None:
        await callback.answer(t("mnevoca_error", lang), show_alert=True)
        return

    await callback.answer(t("rating_thanks", lang))
    new_markup = get_mnevoca_result_keyboard(lang, callback_data.mnemonic_id, is_helpful)
    await callback.message.edit_reply_markup(reply_markup=new_markup)
