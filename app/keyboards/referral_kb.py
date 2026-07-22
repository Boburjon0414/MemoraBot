"""Inline keyboards for the referral / coin pages.

V1.5: All button labels from t() — no hardcoded strings.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import DashboardCallback, ReferralCallback
from app.texts.messages import t


def get_invite_friends_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Keyboard shown on the invite-friends page."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("referral.btn.coin_history", lang),
        callback_data=ReferralCallback(action="coin_history"),
    )
    builder.button(
        text=t("referral.btn.refresh", lang),
        callback_data=ReferralCallback(action="refresh"),
    )
    builder.button(
        text=t("referral.btn.home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    builder.adjust(1, 2)
    return builder.as_markup()


def get_coin_history_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Keyboard shown on the coin-history page."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("referral.btn.back_to_invite", lang),
        callback_data=ReferralCallback(action="invite_friends"),
    )
    builder.button(
        text=t("referral.btn.home", lang),
        callback_data=DashboardCallback(action="home"),
    )
    builder.adjust(1)
    return builder.as_markup()
