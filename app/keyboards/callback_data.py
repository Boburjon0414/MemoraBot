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

    action: str  # "overview" | "requested" | "regenerated" | "quality" | "ai" | "growth" | "broadcast" | "close"


class BroadcastCallback(CallbackData, prefix="bcast"):
    """Payload for the admin broadcast confirmation buttons."""

    action: str  # "confirm" | "cancel"


class ReferralCallback(CallbackData, prefix="ref"):
    """Payload for the user-facing referral / coin pages."""

    action: str  # "invite_friends" | "refresh" | "coin_history"


class AdminReferralCallback(CallbackData, prefix="aref"):
    """Payload for the admin referral-control area.

    `target_id` carries the Telegram user_id for user-specific actions
    (add_coins, remove_coins, reset_coins, give_bonus, view_history);
    it is 0 for list/stats actions that do not target a specific user.
    """

    action: str  # see referral_admin_kb for the full set
    target_id: int = 0  # Telegram user_id, or 0 when not applicable


class VocabularyCallback(CallbackData, prefix="voc"):
    """Payload for the My Vocabulary list screen.

    `search_query` carries the current filter so it survives pagination
    and back-navigation without storing it in FSM state.  Empty string
    means no active filter (None is not serialisable by CallbackData).
    """

    action: str       # "open" | "search" | "cancel_search" | "noop"
    page: int = 0
    search_query: str = ""  # "" = no filter; non-empty = active search


class VocabularyWordCallback(CallbackData, prefix="vocw"):
    """Payload for a single vocabulary entry detail screen and its actions.

    `page` and `search_query` are threaded through so Back buttons always
    return the user to the exact page and search context they came from.
    """

    action: str       # "detail" | "favorite" | "delete" | "delete_confirm" |
                      # "view_update" | "accept_update" | "reject_update"
    entry_id: int = 0
    page: int = 0
    search_query: str = ""  # "" = no filter; carries search context through navigation


class AIGatewayCallback(CallbackData, prefix="gw"):
    """Payload for the admin AI Gateway control panel.

    `provider` — "gemini" | "groq" | "" (empty = not applicable)
    `tier`     — "free" | "premium" | "" (empty = not applicable)
    `key_idx`  — 1-based key index; 0 = not applicable
    """

    action: str   # "status" | "keys" | "key_enable" | "key_disable" |
                  # "key_pause" | "key_resume" | "key_test" |
                  # "provider_enable" | "provider_disable" |
                  # "maintenance_on" | "maintenance_off" |
                  # "priority_gemini_first" | "priority_groq_first" | "back"
    provider: str = ""
    tier: str = ""
    key_idx: int = 0
