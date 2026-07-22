"""Inline keyboards for the private admin analytics area.

V1.5: All button labels sourced from t() — no hardcoded strings.
All builder functions accept `lang: str = "uz"`.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import AdminCallback, AIGatewayCallback, BroadcastCallback
from app.texts.messages import t


def get_admin_menu_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Return the main navigation menu for all available reports."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin.btn.overview", lang),   callback_data=AdminCallback(action="overview"))
    builder.button(text=t("admin.btn.requested", lang),  callback_data=AdminCallback(action="requested"))
    builder.button(text=t("admin.btn.regenerated", lang),callback_data=AdminCallback(action="regenerated"))
    builder.button(text=t("admin.btn.quality", lang),    callback_data=AdminCallback(action="quality"))
    builder.button(text=t("admin.btn.ai", lang),         callback_data=AdminCallback(action="ai"))
    builder.button(text=t("admin.btn.growth", lang),     callback_data=AdminCallback(action="growth"))
    builder.button(text=t("admin.btn.referral", lang),   callback_data=AdminCallback(action="referral_ctrl"))
    builder.button(text=t("admin.btn.broadcast", lang),  callback_data=AdminCallback(action="broadcast"))
    builder.button(text=t("admin.btn.gateway", lang),    callback_data=AIGatewayCallback(action="status"))
    builder.button(text=t("admin.btn.close", lang),      callback_data=AdminCallback(action="close"))
    builder.adjust(1)
    return builder.as_markup()


def get_admin_back_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Provide a consistent way back to the admin overview."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin.btn.back", lang),  callback_data=AdminCallback(action="overview"))
    builder.button(text=t("admin.btn.close", lang), callback_data=AdminCallback(action="close"))
    builder.adjust(1, 1)
    return builder.as_markup()


def get_broadcast_prompt_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Single cancel button shown while the admin is composing the broadcast text."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("admin.broadcast.btn.cancel", lang),
        callback_data=BroadcastCallback(action="cancel"),
    )
    return builder.as_markup()


def get_broadcast_confirm_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Send / Cancel buttons shown under the broadcast preview."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin.broadcast.btn.send", lang),   callback_data=BroadcastCallback(action="confirm"))
    builder.button(text=t("admin.broadcast.btn.cancel", lang), callback_data=BroadcastCallback(action="cancel"))
    builder.adjust(2)
    return builder.as_markup()
