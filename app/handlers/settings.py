"""Settings handlers: language picker and notifications toggle."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.handlers.dashboard import edit_to_dashboard
from app.keyboards.callback_data import DashboardCallback, SettingsCallback
from app.keyboards.settings_kb import get_settings_keyboard
from app.services.settings_service import SettingsService
from app.texts.messages import t

router = Router(name="settings")


@router.callback_query(DashboardCallback.filter(F.action == "settings"))
async def open_settings(callback: CallbackQuery, settings_service: SettingsService) -> None:
    lang = await settings_service.get_language(callback.from_user.id)
    settings_row = await settings_service.get_settings(callback.from_user.id)
    notifications_enabled = settings_row.notifications_enabled if settings_row else True

    await callback.message.edit_text(
        t("settings_title", lang),
        reply_markup=get_settings_keyboard(lang, notifications_enabled),
    )
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "set_lang"))
async def set_language(
    callback: CallbackQuery,
    callback_data: SettingsCallback,
    settings_service: SettingsService,
) -> None:
    new_lang = callback_data.value
    await settings_service.set_language(callback.from_user.id, new_lang)

    settings_row = await settings_service.get_settings(callback.from_user.id)
    notifications_enabled = settings_row.notifications_enabled if settings_row else True

    await callback.message.edit_text(
        t("settings_title", new_lang),
        reply_markup=get_settings_keyboard(new_lang, notifications_enabled),
    )
    await callback.answer(t("settings_language_updated", new_lang))


@router.callback_query(SettingsCallback.filter(F.action == "toggle_notifications"))
async def toggle_notifications(callback: CallbackQuery, settings_service: SettingsService) -> None:
    lang = await settings_service.get_language(callback.from_user.id)
    settings_row = await settings_service.toggle_notifications(callback.from_user.id)
    notifications_enabled = settings_row.notifications_enabled if settings_row else True

    await callback.message.edit_text(
        t("settings_title", lang),
        reply_markup=get_settings_keyboard(lang, notifications_enabled),
    )
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "home"))
async def settings_home(callback: CallbackQuery, settings_service: SettingsService) -> None:
    lang = await settings_service.get_language(callback.from_user.id)
    await edit_to_dashboard(callback, lang)
    await callback.answer()
