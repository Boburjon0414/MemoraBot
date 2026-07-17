"""Private `/admin` analytics interface.

The handler only presents data. Query logic stays in ``AnalyticsService``;
authorization is deliberately checked on every command and callback.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards.admin_kb import get_admin_back_keyboard, get_admin_menu_keyboard
from app.keyboards.callback_data import AdminCallback
from app.services.analytics_service import AnalyticsService
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


async def _deny_callback(callback: CallbackQuery) -> None:
    await callback.answer("⛔ Bu bo'lim faqat administratorlar uchun.", show_alert=True)


@router.message(Command("admin"))
async def open_admin_panel(message: Message, analytics_service: AnalyticsService) -> None:
    """Open the protected analytics dashboard for an authorised administrator."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin panelga kirish huquqi yo'q.")
        return

    overview = await analytics_service.overview()
    await message.answer(format_admin_overview(overview), reply_markup=get_admin_menu_keyboard())


@router.callback_query(AdminCallback.filter(F.action == "overview"))
async def admin_overview(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    overview = await analytics_service.overview()
    await callback.message.edit_text(format_admin_overview(overview), reply_markup=get_admin_menu_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "requested"))
async def most_requested(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    items = await analytics_service.most_requested_words()
    text = format_word_ranking("🔥 <b>Eng ko'p so'ralgan 10 ta so'z</b>", items, "jami ko'rishlar")
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "regenerated"))
async def most_regenerated(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    items = await analytics_service.most_regenerated_words()
    text = format_word_ranking("🔄 <b>Eng ko'p qayta yaratilgan 10 ta so'z</b>", items, "qayta yaratishlar")
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "quality"))
async def quality_report(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    best = await analytics_service.highest_rated_active()
    worst = await analytics_service.lowest_rated_active()
    await callback.message.edit_text(format_quality_report(best, worst), reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "ai"))
async def ai_report(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    providers = await analytics_service.ai_provider_usage()
    prompts = await analytics_service.prompt_version_performance()
    await callback.message.edit_text(format_ai_report(providers, prompts), reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "growth"))
async def growth_report(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    items = await analytics_service.library_growth_by_day()
    await callback.message.edit_text(format_growth_report(items), reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "close"))
async def close_admin_panel(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    await callback.message.delete()
    await callback.answer()
