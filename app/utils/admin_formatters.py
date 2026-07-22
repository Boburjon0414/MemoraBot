"""HTML renderers for concise, readable admin analytics reports.

V1.5: Every hardcoded string replaced with t() calls.
All functions accept `lang: str = "uz"` for admin-language support.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from app.database.models.mnemonic_history import MnemonicHistory
from app.texts.messages import t


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
    return "\n".join(
        f"{i}. <b>{word}</b> — {_number(total)}"
        for i, (word, total) in enumerate(items, 1)
    )


def format_admin_overview(data: dict[str, object], lang: str = "uz") -> str:
    """Render the dashboard's headline library and performance figures."""
    return "\n".join([
        t("admin.overview.title", lang),
        t("admin.overview.subtitle", lang),
        "",
        t("admin.overview.users", lang, value=_number(data["total_users"])),
        t("admin.overview.words", lang, value=_number(data["total_unique_words"])),
        t("admin.overview.mnemonics", lang, value=_number(data["total_mnemonic_versions"])),
        "",
        t("admin.overview.active", lang, value=_number(data["active_versions"])),
        t("admin.overview.deactivated", lang, value=_number(data["deactivated_versions"])),
        t("admin.overview.avg_response", lang, value=_number(data["average_response_time_ms"])),
        "",
        t("admin.overview.footer", lang),
    ])


def format_word_ranking(
    title: str,
    items: Sequence[tuple[str, int]],
    unit: str,
    lang: str = "uz",
) -> str:
    empty = t("common.no_data", lang)
    content = _rows(items, empty)
    unit_label = t("admin.word_ranking.unit_label", lang, unit=unit)
    return f"{title}\n\n{content}\n\n<i>{unit_label}</i>"


def format_quality_report(
    best: Sequence[MnemonicHistory],
    worst: Sequence[MnemonicHistory],
    lang: str = "uz",
) -> str:
    views_unit = t("admin.quality.views_unit", lang)

    def render(entries: Sequence[MnemonicHistory]) -> str:
        if not entries:
            return t("common.no_data", lang)
        return "\n".join(
            f"• <b>{item.word}</b> — {_rating(item.average_rating)} "
            f"(👍 {item.likes} / 👎 {item.dislikes}, {item.uses} {views_unit})"
            for item in entries
        )

    return "\n\n".join([
        t("admin.quality.title", lang),
        t("admin.quality.best", lang) + "\n" + render(best),
        t("admin.quality.worst", lang) + "\n" + render(worst),
        t("admin.quality.note", lang),
    ])


def format_ai_report(
    providers: Sequence[tuple[str, int]],
    prompts: Sequence[tuple[str, int, float]],
    lang: str = "uz",
) -> str:
    empty = t("common.no_data", lang)
    provider_lines = _rows(providers, empty)

    if prompts:
        prompt_lines = "\n".join(
            t("admin.ai.prompt_entry", lang,
              version=version,
              count=str(count),
              rating=_rating(rating or 0.0))
            for version, count, rating in prompts
        )
    else:
        prompt_lines = empty

    return "\n\n".join([
        t("admin.ai.title", lang),
        t("admin.ai.providers_header", lang) + "\n" + provider_lines,
        t("admin.ai.prompts_header", lang) + "\n" + prompt_lines,
    ])


def format_growth_report(
    items: Sequence[tuple[str | date | datetime, int]],
    lang: str = "uz",
) -> str:
    if not items:
        lines = t("common.no_data", lang)
    else:
        lines = "\n".join(
            t("admin.growth.entry", lang, day=str(day), count=str(count))
            for day, count in reversed(items)
        )
    return t("admin.growth.title", lang) + "\n\n" + lines
