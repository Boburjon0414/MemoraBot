"""Formatting helpers that turn domain objects into user-facing HTML text."""

from __future__ import annotations

from app.database.models.mnemonic_history import MnemonicHistory
from app.texts.messages import t

_DIFFICULTY_KEYS = {
    "A1": "difficulty_a1",
    "A2": "difficulty_a2",
    "B1": "difficulty_b1",
    "B2": "difficulty_b2",
    "C1": "difficulty_c1",
    "C2": "difficulty_c2",
}


def format_mnemonic_result(entry: MnemonicHistory, lang: str = "uz") -> str:
    """Render a `MnemonicHistory` row as a modern, clearly-sectioned HTML message.

    V1.1 (Task 2): switched to the requested emoji set (📖 🇺🇿 🔊 🧠 ✍) with
    each field as its own labeled block and consistent blank-line spacing,
    instead of V1's tighter, inline meaning/pronunciation lines.
    """
    difficulty_text = t(_DIFFICULTY_KEYS.get(entry.difficulty, "difficulty_b1"), lang)
    return (
        f"📖 <b>{entry.word.capitalize()}</b>\n\n"
        f"🇺🇿 <b>{t('label_meaning', lang)}</b>\n{entry.meaning}\n\n"
        f"🔊 <b>{t('label_pronunciation', lang)}</b>\n{entry.uzbek_pronunciation}\n\n"
        f"🧠 <b>{t('label_story', lang)}</b>\n{entry.mnemonic_story}\n\n"
        f"✍ <b>{t('label_example', lang)}</b>\n<i>{entry.example_sentence}</i>\n\n"
        f"<b>{t('label_difficulty', lang)}:</b> {difficulty_text}"
    )


def format_full_name(first_name: str | None, last_name: str | None, lang: str = "uz") -> str:
    """Combine a Telegram contact's first/last name into one display name."""
    parts = [part for part in (first_name, last_name) if part]
    return " ".join(parts) if parts else t("common.default_name", lang)
