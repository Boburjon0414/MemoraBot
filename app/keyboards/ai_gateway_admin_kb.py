"""Inline keyboards for the admin AI Gateway control panel (🤖 AI Control).

V1.5: All button labels sourced from t() — no hardcoded strings.
All builder functions accept `lang: str = "uz"`.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.callback_data import AIGatewayCallback
from app.texts.messages import t


def get_gateway_main_keyboard(
    *,
    maintenance_mode: bool = False,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("gateway.btn.status", lang),   callback_data=AIGatewayCallback(action="status"))
    builder.button(text=t("gateway.btn.keys", lang),     callback_data=AIGatewayCallback(action="keys"))
    builder.button(text=t("gateway.btn.gemini", lang),   callback_data=AIGatewayCallback(action="provider_menu", provider="gemini"))
    builder.button(text=t("gateway.btn.groq", lang),     callback_data=AIGatewayCallback(action="provider_menu", provider="groq"))
    if maintenance_mode:
        builder.button(text=t("gateway.btn.maintenance_off", lang), callback_data=AIGatewayCallback(action="maintenance_off"))
    else:
        builder.button(text=t("gateway.btn.maintenance_on", lang),  callback_data=AIGatewayCallback(action="maintenance_on"))
    builder.button(text=t("gateway.btn.priority_gemini", lang), callback_data=AIGatewayCallback(action="priority_gemini_first"))
    builder.button(text=t("gateway.btn.priority_groq", lang),   callback_data=AIGatewayCallback(action="priority_groq_first"))
    builder.button(text=t("gateway.btn.back", lang),            callback_data=AIGatewayCallback(action="back"))
    builder.adjust(1)
    return builder.as_markup()


def get_provider_menu_keyboard(
    provider: str,
    *,
    is_enabled: bool = True,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    pname = provider.title()
    if is_enabled:
        builder.button(
            text=t("gateway.btn.provider_disable", lang, provider=pname),
            callback_data=AIGatewayCallback(action="provider_disable", provider=provider),
        )
    else:
        builder.button(
            text=t("gateway.btn.provider_enable", lang, provider=pname),
            callback_data=AIGatewayCallback(action="provider_enable", provider=provider),
        )
    builder.button(
        text=t("gateway.btn.provider_keys", lang, provider=pname),
        callback_data=AIGatewayCallback(action="keys", provider=provider),
    )
    builder.button(
        text=t("gateway.btn.provider_back", lang),
        callback_data=AIGatewayCallback(action="status"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_key_list_keyboard(
    key_health_list: list[dict],
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for h in key_health_list:
        status_icon = "🟢" if h["is_healthy"] else ("⏸" if h["is_paused"] else "🔴")
        entry_text = t(
            "gateway.keys.entry", lang,
            status=status_icon,
            label=h["label"],
            requests=str(h["requests_served"]),
        )
        builder.button(
            text=entry_text,
            callback_data=AIGatewayCallback(
                action="key_detail",
                provider=h["provider"],
                tier=h["tier"],
                key_idx=h["key_index"],
            ),
        )
    builder.button(
        text=t("gateway.btn.provider_back", lang),
        callback_data=AIGatewayCallback(action="status"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_key_detail_keyboard(
    provider: str,
    tier: str,
    key_idx: int,
    *,
    is_enabled: bool,
    is_paused: bool,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_enabled:
        builder.button(
            text=t("gateway.btn.key_disable", lang),
            callback_data=AIGatewayCallback(action="key_disable", provider=provider, tier=tier, key_idx=key_idx),
        )
    else:
        builder.button(
            text=t("gateway.btn.key_enable", lang),
            callback_data=AIGatewayCallback(action="key_enable", provider=provider, tier=tier, key_idx=key_idx),
        )
    if is_paused:
        builder.button(
            text=t("gateway.btn.key_resume", lang),
            callback_data=AIGatewayCallback(action="key_resume", provider=provider, tier=tier, key_idx=key_idx),
        )
    else:
        builder.button(
            text=t("gateway.btn.key_pause", lang),
            callback_data=AIGatewayCallback(action="key_pause", provider=provider, tier=tier, key_idx=key_idx),
        )
    builder.button(
        text=t("gateway.btn.key_test", lang),
        callback_data=AIGatewayCallback(action="key_test", provider=provider, tier=tier, key_idx=key_idx),
    )
    builder.button(
        text=t("gateway.btn.keys_back", lang),
        callback_data=AIGatewayCallback(action="keys"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_gateway_back_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("gateway.btn.provider_back", lang),
        callback_data=AIGatewayCallback(action="status"),
    )
    return builder.as_markup()
