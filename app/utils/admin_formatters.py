"""HTML renderers for concise, readable admin analytics reports."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from app.database.models.mnemonic_history import MnemonicHistory


def _number(value: int | float | None) -> str:
    """Render numeric values consistently, including empty aggregate results."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.1f}"
    return f"{value:,}"


def _rating(value: float) -> str:
    return f"{value:+.2f}"


def _rows(items: Sequence[tuple[str, int]], empty: str) -> str:
    if not items:
        return empty
    return "\n".join(f"{index}. <b>{word}</b> — {_number(total)}" for index, (word, total) in enumerate(items, 1))


def format_admin_overview(data: dict[str, object]) -> str:
    """Render the dashboard's headline library and performance figures."""
    return (
        "🔐 <b>Admin panel · Statistika</b>\n"
        "<i>MemoraBot kutubxonasining umumiy holati</i>\n\n"
        f"👤 Foydalanuvchilar: <b>{_number(data['total_users'])}</b>\n"
        f"📚 Noyob so'zlar: <b>{_number(data['total_unique_words'])}</b>\n"
        f"🧠 Mnemonika versiyalari: <b>{_number(data['total_mnemonic_versions'])}</b>\n\n"
        f"✅ Faol versiyalar: <b>{_number(data['active_versions'])}</b>\n"
        f"🗄 Faolsizlantirilgan: <b>{_number(data['deactivated_versions'])}</b>\n"
        f"⚡ O'rtacha AI javob vaqti: <b>{_number(data['average_response_time_ms'])} ms</b>\n\n"
        "Kerakli hisobotni pastdagi menyudan tanlang."
    )


def format_word_ranking(title: str, items: Sequence[tuple[str, int]], unit: str) -> str:
    content = _rows(items, "Hali ma'lumot yo'q.")
    return f"{title}\n\n{content}\n\n<i>Qiymatlar: {unit}</i>"


def format_quality_report(
    best: Sequence[MnemonicHistory], worst: Sequence[MnemonicHistory]
) -> str:
    def render(entries: Sequence[MnemonicHistory]) -> str:
        if not entries:
            return "Hali ma'lumot yo'q."
        return "\n".join(
            f"• <b>{item.word}</b> — {_rating(item.average_rating)} "
            f"(👍 {item.likes} / 👎 {item.dislikes}, {item.uses} ko'rish)"
            for item in entries
        )

    return (
        "⭐ <b>Sifat reytingi</b>\n\n"
        "🏆 <b>Eng yaxshi faol versiyalar</b>\n"
        f"{render(best)}\n\n"
        "⚠️ <b>E'tibor talab qiladigan faol versiyalar</b>\n"
        f"{render(worst)}\n\n"
        "<i>Reyting: (like − dislike) / jami baholar</i>"
    )


def format_ai_report(
    providers: Sequence[tuple[str, int]], prompts: Sequence[tuple[str, int, float]]) -> str:
    provider_lines = _rows(providers, "Hali ma'lumot yo'q.")
    prompt_lines = (
        "\n".join(
            f"• <b>{version}</b> — {count} versiya, o'rtacha reyting {_rating(rating or 0.0)}"
            for version, count, rating in prompts
        )
        if prompts
        else "Hali ma'lumot yo'q."
    )
    return (
        "🤖 <b>AI va promptlar samaradorligi</b>\n\n"
        "<b>Providerlar bo'yicha yaratilgan versiyalar</b>\n"
        f"{provider_lines}\n\n"
        "<b>Prompt versiyalari bo'yicha natija</b>\n"
        f"{prompt_lines}"
    )


def format_growth_report(items: Sequence[tuple[str | date | datetime, int]]) -> str:
    if not items:
        lines = "Hali ma'lumot yo'q."
    else:
        lines = "\n".join(f"• <b>{day}</b> — {count} yangi versiya" for day, count in reversed(items))
    return "📈 <b>Oxirgi 30 kun: kutubxona o'sishi</b>\n\n" + lines
