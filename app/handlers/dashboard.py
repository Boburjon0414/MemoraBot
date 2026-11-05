"""Handlers for the dashboard itself: showing it, and the "coming soon"
stubs for AI Chat / Statistics.

`send_dashboard` / `edit_to_dashboard` are also imported by the other
handler modules (mnevoca, settings, about, fallback) whenever they need to
return the user to the home screen.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.callback_data import DashboardCallback
from app.keyboards.dashboard_kb import get_dashboard_keyboard
from app.services.settings_service import SettingsService
from app.texts.messages import t

router = Router(name="dashboard")


async def send_dashboard(message: Message, lang: str = "uz") -> None:
    """Send a brand new dashboard message."""
    await message.answer(t("dashboard_title", lang), reply_markup=get_dashboard_keyboard(lang))


async def edit_to_dashboard(callback: CallbackQuery, lang: str = "uz") -> None:
    """Edit the current callback's message in place to show the dashboard."""
    await callback.message.edit_text(t("dashboard_title", lang), reply_markup=get_dashboard_keyboard(lang))


@router.callback_query(DashboardCallback.filter(F.action == "home"))
async def on_home(callback: CallbackQuery, settings_service: SettingsService) -> None:
    lang = await settings_service.get_language(callback.from_user.id)
    await edit_to_dashboard(callback, lang)
    await callback.answer()


@router.callback_query(DashboardCallback.filter(F.action == "statistics"))
async def on_statistics(callback: CallbackQuery, settings_service: SettingsService) -> None:
    """Statistics is a defined-but-not-yet-built feature; see README for where it plugs in."""
    lang = await settings_service.get_language(callback.from_user.id)
    await callback.answer(t("coming_soon", lang), show_alert=True)
