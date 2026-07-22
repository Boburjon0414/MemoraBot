"""Private `/admin` analytics interface.

The handler only presents data. Query logic stays in ``AnalyticsService``;
authorization is deliberately checked on every command and callback.

V1.5: All hardcoded strings replaced with t(). Admin's UI language is
resolved via settings_service and passed through to formatters/keyboards.
"""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards.admin_kb import (
    get_admin_back_keyboard,
    get_admin_menu_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_prompt_keyboard,
)
from app.keyboards.callback_data import AdminCallback, BroadcastCallback
from app.services.analytics_service import AnalyticsService
from app.services.broadcast_service import BroadcastService
from app.services.settings_service import SettingsService
from app.states.bot_states import BroadcastStates
from app.texts.messages import t
from app.utils.admin_formatters import (
    format_admin_overview,
    format_ai_report,
    format_growth_report,
    format_quality_report,
    format_word_ranking,
)

router = Router(name="admin")


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_list


async def _get_lang(settings_service: SettingsService, telegram_id: int) -> str:
    """Resolve the admin's preferred UI language. Falls back to 'uz'."""
    try:
        return await settings_service.get_language(telegram_id)
    except Exception:
        return "uz"


async def _deny_callback(callback: CallbackQuery, lang: str = "uz") -> None:
    await callback.answer(t("admin.denied_callback", lang), show_alert=True)


@router.message(Command("admin"))
async def open_admin_panel(
    message: Message,
    analytics_service: AnalyticsService,
    settings_service: SettingsService,
) -> None:
    """Open the protected analytics dashboard for an authorised administrator."""
    if not _is_admin(message.from_user.id):
        lang = await _get_lang(settings_service, message.from_user.id)
        await message.answer(t("admin.denied", lang))
        return

    lang = await _get_lang(settings_service, message.from_user.id)
    overview = await analytics_service.overview()
    await message.answer(
        format_admin_overview(overview, lang),
        reply_markup=get_admin_menu_keyboard(lang),
    )


@router.callback_query(AdminCallback.filter(F.action == "overview"))
async def admin_overview(
    callback: CallbackQuery,
    analytics_service: AnalyticsService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return
    overview = await analytics_service.overview()
    await callback.message.edit_text(
        format_admin_overview(overview, lang),
        reply_markup=get_admin_menu_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "requested"))
async def most_requested(
    callback: CallbackQuery,
    analytics_service: AnalyticsService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return
    items = await analytics_service.most_requested_words()
    text = format_word_ranking(
        t("admin.most_requested.title", lang),
        items,
        t("admin.most_requested.unit", lang),
        lang,
    )
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard(lang))
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "regenerated"))
async def most_regenerated(
    callback: CallbackQuery,
    analytics_service: AnalyticsService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return
    items = await analytics_service.most_regenerated_words()
    text = format_word_ranking(
        t("admin.most_regenerated.title", lang),
        items,
        t("admin.most_regenerated.unit", lang),
        lang,
    )
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard(lang))
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "quality"))
async def quality_report(
    callback: CallbackQuery,
    analytics_service: AnalyticsService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return
    best = await analytics_service.highest_rated_active()
    worst = await analytics_service.lowest_rated_active()
    await callback.message.edit_text(
        format_quality_report(best, worst, lang),
        reply_markup=get_admin_back_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "ai"))
async def ai_report(
    callback: CallbackQuery,
    analytics_service: AnalyticsService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return
    providers = await analytics_service.ai_provider_usage()
    prompts = await analytics_service.prompt_version_performance()
    await callback.message.edit_text(
        format_ai_report(providers, prompts, lang),
        reply_markup=get_admin_back_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "growth"))
async def growth_report(
    callback: CallbackQuery,
    analytics_service: AnalyticsService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return
    items = await analytics_service.library_growth_by_day()
    await callback.message.edit_text(
        format_growth_report(items, lang),
        reply_markup=get_admin_back_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "close"))
async def close_admin_panel(
    callback: CallbackQuery,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return
    await callback.message.delete()
    await callback.answer()


# ── Broadcast ──────────────────────────────────────────────────────────────


@router.callback_query(AdminCallback.filter(F.action == "broadcast"))
async def broadcast_entry(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    """Open the broadcast composer: ask the admin to type the message text."""
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return

    await state.set_state(BroadcastStates.waiting_for_message)
    await state.update_data(admin_lang=lang)

    body = "\n\n".join([
        t("admin.broadcast.title", lang),
        t("admin.broadcast.prompt", lang),
        t("admin.broadcast.text_only_note", lang),
    ])
    await callback.message.edit_text(body, reply_markup=get_broadcast_prompt_keyboard(lang))
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message, F.text)
async def broadcast_receive_text(
    message: Message,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    """Accept the broadcast text and render a preview with confirm / cancel."""
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    state_data = await state.get_data()
    lang: str = state_data.get("admin_lang") or await _get_lang(settings_service, message.from_user.id)
    await state.update_data(broadcast_text=message.text)

    preview = "\n\n".join([
        t("admin.broadcast.preview_header", lang),
        message.text,
        "─" * 21,
        t("admin.broadcast.preview_note", lang),
    ])
    await message.answer(preview, reply_markup=get_broadcast_confirm_keyboard(lang))


@router.message(BroadcastStates.waiting_for_message)
async def broadcast_invalid_content(
    message: Message,
    settings_service: SettingsService,
) -> None:
    """Reject non-text content (photos, stickers, …) while composing a broadcast."""
    if not _is_admin(message.from_user.id):
        return
    lang = await _get_lang(settings_service, message.from_user.id)
    await message.answer(t("admin.broadcast.text_only_error", lang))


@router.callback_query(BroadcastCallback.filter(F.action == "confirm"))
async def broadcast_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    broadcast_service: BroadcastService,
    settings_service: SettingsService,
    bot: Bot,
) -> None:
    """Admin confirmed: clear FSM, schedule background broadcast, show status."""
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return

    state_data = await state.get_data()
    broadcast_text: str | None = state_data.get("broadcast_text")
    lang = state_data.get("admin_lang") or lang

    if not broadcast_text:
        await callback.answer(t("admin.broadcast.no_text", lang), show_alert=True)
        await state.clear()
        return

    admin_id = callback.from_user.id
    await state.clear()

    total = await broadcast_service.start_broadcast(bot, broadcast_text, admin_id, lang=lang)

    body = "\n\n".join([
        t("admin.broadcast.started_title", lang),
        t("admin.broadcast.started_count", lang, total=str(total)),
        t("admin.broadcast.started_note", lang),
    ])
    await callback.message.edit_text(body)
    await callback.answer(t("admin.broadcast.answer_started", lang))


@router.callback_query(BroadcastCallback.filter(F.action == "cancel"))
async def broadcast_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    analytics_service: AnalyticsService,
    settings_service: SettingsService,
) -> None:
    """Admin cancelled at any step — clear FSM and return to the admin overview."""
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback, lang)
        return

    await state.clear()
    overview = await analytics_service.overview()
    await callback.message.edit_text(
        format_admin_overview(overview, lang),
        reply_markup=get_admin_menu_keyboard(lang),
    )
    await callback.answer(t("admin.broadcast.cancelled", lang))
