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

    action: str  # "another" | "home" | "regenerate"  | "pronunciation"
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


class AIChatCallback(CallbackData, prefix="chat"):
    """Payload for AI Chat session controls.

    action:
      "new"       — start a new session (clears current session)
      "end"       — end current session and return to dashboard
      "history"   — show recent sessions list (future)
    session_id:   FeatureOutput.id of the active ChatSessionPayload; 0 = no session
    """

    action: str
    session_id: int = 0


class QuizCallback(CallbackData, prefix="quiz"):
    """Payload for Quiz feature controls (Feature C).

    action:
      "start"          — begin quiz with the selected type
      "end"            — abort current quiz and return to dashboard
      "reading_begin"  — user tapped "Start Questions" after reading the passage
    quiz_type:   "vocabulary" | "grammar" | "gap_fill" | "reading" | "listening" | "mixed"
    output_id:   FeatureOutput.id of the active quiz (0 = not yet created)
    """

    action: str
    quiz_type: str = "mixed"
    output_id: int = 0



class AdminGrammarCallback(CallbackData, prefix="admgram"):
    """Payload for admin Grammar Lessons management actions.

    action:
      "menu"          — show grammar lessons admin menu
      "list"          — list all lessons
      "add_forward"   — start add-lesson flow (forward from channel)
      "add_manual"    — start add-lesson flow (manual message_id)
      "edit"          — edit a specific topic
      "edit_name"     — edit topic name
      "edit_button"   — edit button name
      "edit_msgid"    — edit message_id
      "toggle"        — enable/disable topic
      "delete"        — start delete flow
      "delete_confirm"— confirm deletion
      "move_up"       — move topic up in order
      "move_down"     — move topic down in order
    topic_id:   GrammarTopic.id (0 = not applicable)
    page:       pagination page for list view
    """

    action: str
    topic_id: int = 0
    page: int = 0


class LearnCallback(CallbackData, prefix="learn"):
    """Payload for the Learn section entry button on the dashboard."""

    action: str  # "grammar" | "home"


class GrammarCallback(CallbackData, prefix="gram"):
    """Payload for Grammar Learning feature controls.

    action:
      "topics"      — show grammar topic selection keyboard
      "open_topic"  — open a specific grammar lesson
      "ask_ai"      — enter grammar Q&A FSM for this topic
      "test"        — start a grammar quiz for this topic
    topic_id:  GrammarTopic.id (0 = not applicable, e.g. for "topics" action)
    page:      pagination page for "topics" action
    """

    action: str
    topic_id: int = 0
    page: int = 0


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
