"""Inline keyboards for the private admin analytics area."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import AdminCallback, BroadcastCallback


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Return the main navigation menu for all available reports."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Umumiy ko'rinish", callback_data=AdminCallback(action="overview"))
    builder.button(text="🔥 Eng ko'p so'ralgan", callback_data=AdminCallback(action="requested"))
    builder.button(text="🔄 Qayta yaratilgan", callback_data=AdminCallback(action="regenerated"))
    builder.button(text="⭐ Sifat reytingi", callback_data=AdminCallback(action="quality"))
    builder.button(text="🤖 AI va promptlar", callback_data=AdminCallback(action="ai"))
    builder.button(text="📈 Kutubxona o'sishi", callback_data=AdminCallback(action="growth"))
    builder.button(text="📢 Xabar tarqatish", callback_data=AdminCallback(action="broadcast"))
    builder.button(text="✖️ Yopish", callback_data=AdminCallback(action="close"))
    builder.adjust(1)
    return builder.as_markup()


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    """Provide a consistent way back to the admin overview."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Admin menyu", callback_data=AdminCallback(action="overview"))
    builder.button(text="✖️ Yopish", callback_data=AdminCallback(action="close"))
    builder.adjust(1, 1)
    return builder.as_markup()


def get_broadcast_prompt_keyboard() -> InlineKeyboardMarkup:
    """Single cancel button shown while the admin is composing the broadcast text."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data=BroadcastCallback(action="cancel"))
    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Send / Cancel buttons shown under the broadcast preview."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yuborish", callback_data=BroadcastCallback(action="confirm"))
    builder.button(text="❌ Bekor qilish", callback_data=BroadcastCallback(action="cancel"))
    builder.adjust(2)
    return builder.as_markup()
