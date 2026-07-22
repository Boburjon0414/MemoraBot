"""Inline keyboards for the admin referral-control area.

V1.5: All button labels from t() — no hardcoded strings.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import AdminCallback, AdminReferralCallback
from app.texts.messages import t


def get_referral_control_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Top-level referral control menu for admins."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin.referral.btn.top_referrers", lang), callback_data=AdminReferralCallback(action="top_referrers"))
    builder.button(text=t("admin.referral.btn.top_holders", lang),   callback_data=AdminReferralCallback(action="top_holders"))
    builder.button(text=t("admin.referral.btn.recent", lang),        callback_data=AdminReferralCallback(action="recent"))
    builder.button(text=t("admin.referral.btn.search", lang),        callback_data=AdminReferralCallback(action="search"))
    builder.button(text=t("admin.referral.btn.stats", lang),         callback_data=AdminReferralCallback(action="stats"))
    builder.button(text=t("admin.referral.btn.home", lang),          callback_data=AdminCallback(action="overview"))
    builder.adjust(1)
    return builder.as_markup()


def get_referral_back_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Back button returning to the referral control menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin.referral.btn.back", lang), callback_data=AdminReferralCallback(action="back"))
    builder.button(text=t("admin.referral.btn.home", lang), callback_data=AdminCallback(action="overview"))
    builder.adjust(1)
    return builder.as_markup()


def get_user_action_keyboard(telegram_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Action buttons shown under a user's admin profile."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin.referral.btn.add_coins", lang),    callback_data=AdminReferralCallback(action="add_coins",   target_id=telegram_id))
    builder.button(text=t("admin.referral.btn.remove_coins", lang), callback_data=AdminReferralCallback(action="remove_coins", target_id=telegram_id))
    builder.button(text=t("admin.referral.btn.reset_coins", lang),  callback_data=AdminReferralCallback(action="reset_coins",  target_id=telegram_id))
    builder.button(text=t("admin.referral.btn.bonus", lang),        callback_data=AdminReferralCallback(action="give_bonus",   target_id=telegram_id))
    builder.button(text=t("admin.referral.btn.history", lang),      callback_data=AdminReferralCallback(action="view_history", target_id=telegram_id))
    builder.button(text=t("admin.referral.btn.back", lang),         callback_data=AdminReferralCallback(action="back"))
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def get_coin_action_cancel_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Cancel button shown while waiting for a coin amount."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("admin.referral.btn.cancel_action", lang),
        callback_data=AdminReferralCallback(action="cancel_action"),
    )
    return builder.as_markup()
