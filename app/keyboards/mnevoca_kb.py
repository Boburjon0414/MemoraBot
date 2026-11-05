"""Inline keyboards for the MneVoca flow (Feature 2).

V1.1 extends the result keyboard with a "🔄 Generate Another Mnemonic"
regenerate button (Task 4) and 👍/👎 rating buttons (Task 5), on top of the
existing "new word" / "home" buttons.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import MneVocaCallback, MnemonicRatingCallback
from app.texts.messages import t


def get_mnevoca_entry_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Shown while MemoraBot is waiting for the user to type a word."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_back_home", lang), callback_data=MneVocaCallback(action="home"))
    return builder.as_markup()


def get_mnevoca_result_keyboard(
    lang: str,
    mnemonic_id: int,
    user_rating: bool | None = None,
) -> InlineKeyboardMarkup:
    """Shown after a mnemonic has been generated, cached, or regenerated.

    Args:
        mnemonic_id: the `mnemonic_history.id` this screen is showing —
            threaded through the regenerate and rating callbacks so their
            handlers know exactly which row to act on.
        user_rating: True/False if the current viewer already rated this
            specific mnemonic, else None — used to show a ✅ on whichever
            button (if any) they already tapped.
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text=t("btn_regenerate", lang),
        callback_data=MneVocaCallback(action="regenerate", mnemonic_id=mnemonic_id))
    builder.button(
        text=t("btn_pronunciation", lang),
        callback_data=MneVocaCallback(action="pronunciation", mnemonic_id=mnemonic_id),
    )

    helpful_label = t("btn_helpful_selected" if user_rating is True else "btn_helpful", lang)
    not_helpful_label = t(
        "btn_not_helpful_selected" if user_rating is False else "btn_not_helpful", lang
    )
    builder.button(
        text=helpful_label,
        callback_data=MnemonicRatingCallback(mnemonic_id=mnemonic_id, value="up"),
    )
    builder.button(
        text=not_helpful_label,
        callback_data=MnemonicRatingCallback(mnemonic_id=mnemonic_id, value="down"),
    )

    builder.button(text=t("btn_another_word", lang), callback_data=MneVocaCallback(action="another"))
    builder.button(text=t("btn_back_home", lang), callback_data=MneVocaCallback(action="home"))

    builder.adjust(2, 2, 2)
    return builder.as_markup()
