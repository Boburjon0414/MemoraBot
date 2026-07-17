"""'About' screen handler."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.callback_data import DashboardCallback
from app.keyboards.dashboard_kb import get_back_to_dashboard_keyboard
from app.services.settings_service import SettingsService
from app.texts.messages import t

router = Router(name="about")


@router.callback_query(DashboardCallback.filter(F.action == "about"))
async def show_about(callback: CallbackQuery, settings_service: SettingsService) -> None:
    lang = await settings_service.get_language(callback.from_user.id)
    await callback.message.edit_text(t("about_text", lang), reply_markup=get_back_to_dashboard_keyboard(lang))
    await callback.answer()
