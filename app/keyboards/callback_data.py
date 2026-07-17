"""Typed `CallbackData` factories for every inline keyboard in the bot.

Using aiogram's `CallbackData` factory (instead of hand-rolled strings) keeps
callback payloads type-safe and gives filters like
`DashboardCallback.filter(F.action == "mnevoca")` for free.
"""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class DashboardCallback(CallbackData, prefix="dash"):
    """Payload for the main dashboard buttons."""

    action: str  # "mnevoca" | "ai_chat" | "statistics" | "settings" | "about" | "home"


class MneVocaCallback(CallbackData, prefix="mnv"):
    """Payload for the MneVoca entry/result screen buttons."""

    action: str  # "another" | "home" | "regenerate"
    mnemonic_id: int = 0  # set for "regenerate"; unused (default) for the others


class MnemonicRatingCallback(CallbackData, prefix="rate"):
    """Payload for the 👍/👎 rating buttons under a generated mnemonic (Task 5)."""

    mnemonic_id: int
    value: str  # "up" | "down"


class SettingsCallback(CallbackData, prefix="set"):
    """Payload for the settings screen buttons."""

    action: str  # "set_lang" | "toggle_notifications" | "home"
    value: str = ""


class AdminCallback(CallbackData, prefix="admin"):
    """Payload for the private admin analytics menu."""

    action: str  # "overview" | "requested" | "regenerated" | "quality" | "ai" | "growth" | "close"
