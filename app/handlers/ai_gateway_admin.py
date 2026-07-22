"""Admin AI Gateway control panel (🤖 AI Gateway boshqaruvi).

V1.5: All hardcoded strings replaced with t(). Admin's language resolved
via settings_service and passed to all formatters/keyboards.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.config import settings
from app.keyboards.ai_gateway_admin_kb import (
    get_gateway_back_keyboard,
    get_gateway_main_keyboard,
    get_key_detail_keyboard,
    get_key_list_keyboard,
    get_provider_menu_keyboard,
)
from app.keyboards.callback_data import AIGatewayCallback
from app.services.ai.gateway import AIGateway
from app.services.settings_service import SettingsService
from app.texts.messages import t

router = Router(name="ai_gateway_admin")
logger = logging.getLogger(__name__)


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_list


async def _get_lang(settings_service: SettingsService, telegram_id: int) -> str:
    try:
        return await settings_service.get_language(telegram_id)
    except Exception:
        return "uz"


async def _deny(callback: CallbackQuery, lang: str = "uz") -> None:
    await callback.answer(t("admin.denied_callback", lang), show_alert=True)


async def _no_gateway(callback: CallbackQuery, lang: str = "uz") -> None:
    await callback.answer(t("gateway.not_active", lang), show_alert=True)


# ── Status / Overview ──────────────────────────────────────────────────────


@router.callback_query(AIGatewayCallback.filter(F.action == "status"))
async def gateway_status(
    callback: CallbackQuery,
    callback_data: AIGatewayCallback,
    settings_service: SettingsService,
    ai_gateway: AIGateway | None = None,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    if ai_gateway is None:
        await _no_gateway(callback, lang)
        return

    analytics = ai_gateway.get_gateway_analytics()
    provider_stats = ai_gateway.get_provider_stats()

    mode_str = (
        t("gateway.status.maintenance_on", lang)
        if analytics["maintenance_mode"]
        else t("gateway.status.online", lang)
    )

    lines = [
        t("gateway.status.title", lang),
        "",
        mode_str,
        "",
        t("gateway.status.analytics", lang),
        t("gateway.status.total_requests",   lang, value=str(analytics["total_requests"])),
        t("gateway.status.errors",            lang, value=str(analytics["total_errors"])),
        t("gateway.status.quota_failures",    lang, value=str(analytics["quota_failures"])),
        t("gateway.status.fallbacks",         lang, value=str(analytics["fallback_count"])),
        t("gateway.status.free_requests",     lang, value=str(analytics["free_requests"])),
        t("gateway.status.premium_requests",  lang, value=str(analytics["premium_requests"])),
        "",
        t("gateway.status.healthy_keys", lang,
          healthy=str(analytics["healthy_keys"]),
          total=str(analytics["total_keys"])),
        "",
        t("gateway.status.providers_title", lang),
    ]
    for ps in provider_stats:
        lines.append(t(
            "gateway.status.provider_entry", lang,
            status=ps["status"].split()[0],  # just the emoji
            provider=ps["provider"].title(),
            tier=ps["tier"],
            healthy=str(ps["healthy_keys"]),
            total=str(ps["total_keys"]),
            latency=str(int(ps["avg_latency_ms"])),
        ))

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=get_gateway_main_keyboard(
            maintenance_mode=analytics["maintenance_mode"], lang=lang
        ),
    )
    await callback.answer()


# ── Key Health List ────────────────────────────────────────────────────────


@router.callback_query(AIGatewayCallback.filter(F.action == "keys"))
async def gateway_keys(
    callback: CallbackQuery,
    callback_data: AIGatewayCallback,
    settings_service: SettingsService,
    ai_gateway: AIGateway | None = None,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    if ai_gateway is None:
        await _no_gateway(callback, lang)
        return

    all_health = ai_gateway.get_all_key_health()
    provider_filter = callback_data.provider
    if provider_filter:
        all_health = [h for h in all_health if h.provider_name == provider_filter]

    if not all_health:
        await callback.message.edit_text(
            t("gateway.keys.empty", lang),
            reply_markup=get_gateway_back_keyboard(lang),
        )
        await callback.answer()
        return

    pname = provider_filter.title() if provider_filter else t("gateway.keys.all", lang)
    title = t("gateway.keys.title", lang, provider_label=pname)
    health_dicts = [h.to_dict() for h in all_health]
    await callback.message.edit_text(title, reply_markup=get_key_list_keyboard(health_dicts, lang))
    await callback.answer()


# ── Key Detail ─────────────────────────────────────────────────────────────


@router.callback_query(AIGatewayCallback.filter(F.action == "key_detail"))
async def gateway_key_detail(
    callback: CallbackQuery,
    callback_data: AIGatewayCallback,
    settings_service: SettingsService,
    ai_gateway: AIGateway | None = None,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    if ai_gateway is None:
        await _no_gateway(callback, lang)
        return

    slot = ai_gateway._find_slot(callback_data.provider, callback_data.tier, callback_data.key_idx)
    if slot is None:
        await callback.answer(t("gateway.key.not_found", lang), show_alert=True)
        return

    h = slot.health.to_dict()

    if h["is_healthy"]:
        status_str = t("gateway.key.status.healthy", lang)
    elif h["is_paused"]:
        status_str = t("gateway.key.status.paused", lang)
    else:
        status_str = t("gateway.key.status.down", lang)

    lines = [
        t("gateway.key.title", lang, label=h["label"]),
        "",
        t("gateway.key.status.label", lang, value=status_str),
        t("gateway.key.enabled_label", lang, value="✅" if h["is_enabled"] else "❌"),
        t("gateway.key.paused_label",  lang, value="⏸" if h["is_paused"] else "—"),
        "",
        t("gateway.key.stats.title", lang),
        t("gateway.key.stats.total",       lang, value=str(h["requests_served"])),
        t("gateway.key.stats.success",     lang, value=str(h["success_count"])),
        t("gateway.key.stats.errors",      lang, value=str(h["failure_count"])),
        t("gateway.key.stats.consecutive", lang, value=str(h["consecutive_failures"])),
        t("gateway.key.stats.latency",     lang, value=str(h["avg_latency_ms"])),
        "",
        t("gateway.key.times.title", lang),
        t("gateway.key.times.last_success", lang, value=h["last_success"]),
        t("gateway.key.times.last_failure", lang, value=h["last_failure"]),
        t("gateway.key.times.cooldown", lang,
          value=h["cooldown_until"] or t("gateway.key.times.no_cooldown", lang)),
    ]

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=get_key_detail_keyboard(
            callback_data.provider, callback_data.tier, callback_data.key_idx,
            is_enabled=h["is_enabled"], is_paused=h["is_paused"], lang=lang,
        ),
    )
    await callback.answer()


# ── Key Management Actions ─────────────────────────────────────────────────


@router.callback_query(AIGatewayCallback.filter(F.action == "key_enable"))
async def key_enable(callback: CallbackQuery, callback_data: AIGatewayCallback,
                     settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    ok = await ai_gateway.admin_enable_key(callback_data.provider, callback_data.tier, callback_data.key_idx)
    label = f"{callback_data.provider.title()} Key #{callback_data.key_idx}"
    msg = t("gateway.action.enabled", lang, label=label) if ok else t("gateway.action.key_not_found", lang)
    await callback.answer(msg, show_alert=True)
    if ok:
        await gateway_key_detail(callback, callback_data, settings_service, ai_gateway)


@router.callback_query(AIGatewayCallback.filter(F.action == "key_disable"))
async def key_disable(callback: CallbackQuery, callback_data: AIGatewayCallback,
                      settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    ok = await ai_gateway.admin_disable_key(callback_data.provider, callback_data.tier, callback_data.key_idx)
    label = f"{callback_data.provider.title()} Key #{callback_data.key_idx}"
    msg = t("gateway.action.disabled", lang, label=label) if ok else t("gateway.action.key_not_found", lang)
    await callback.answer(msg, show_alert=True)
    if ok:
        await gateway_key_detail(callback, callback_data, settings_service, ai_gateway)


@router.callback_query(AIGatewayCallback.filter(F.action == "key_pause"))
async def key_pause(callback: CallbackQuery, callback_data: AIGatewayCallback,
                    settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    ok = await ai_gateway.admin_pause_key(callback_data.provider, callback_data.tier, callback_data.key_idx)
    label = f"{callback_data.provider.title()} Key #{callback_data.key_idx}"
    msg = t("gateway.action.paused", lang, label=label) if ok else t("gateway.action.key_not_found", lang)
    await callback.answer(msg, show_alert=True)
    if ok:
        await gateway_key_detail(callback, callback_data, settings_service, ai_gateway)


@router.callback_query(AIGatewayCallback.filter(F.action == "key_resume"))
async def key_resume(callback: CallbackQuery, callback_data: AIGatewayCallback,
                     settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    ok = await ai_gateway.admin_resume_key(callback_data.provider, callback_data.tier, callback_data.key_idx)
    label = f"{callback_data.provider.title()} Key #{callback_data.key_idx}"
    msg = t("gateway.action.resumed", lang, label=label) if ok else t("gateway.action.key_not_found", lang)
    await callback.answer(msg, show_alert=True)
    if ok:
        await gateway_key_detail(callback, callback_data, settings_service, ai_gateway)


@router.callback_query(AIGatewayCallback.filter(F.action == "key_test"))
async def key_test(callback: CallbackQuery, callback_data: AIGatewayCallback,
                   settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    await callback.answer(t("gateway.test.loading", lang))
    ok, message = await ai_gateway.admin_test_key(callback_data.provider, callback_data.tier, callback_data.key_idx)
    await callback.message.answer(f"{t('gateway.test.result', lang)}\n\n{message}")


# ── Provider Management ────────────────────────────────────────────────────


@router.callback_query(AIGatewayCallback.filter(F.action == "provider_menu"))
async def provider_menu(callback: CallbackQuery, callback_data: AIGatewayCallback,
                        settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return

    provider = callback_data.provider
    is_enabled = provider in ai_gateway._runtime.enabled_providers
    stats = [s for s in ai_gateway.get_provider_stats() if s["provider"] == provider]

    lines = [t("gateway.provider.title", lang, provider=provider.title()), ""]
    if stats:
        for s in stats:
            lines.append(t(
                "gateway.status.provider_entry", lang,
                status=s["status"].split()[0],
                provider=s["provider"].title(),
                tier=s["tier"],
                healthy=str(s["healthy_keys"]),
                total=str(s["total_keys"]),
                latency=str(int(s["avg_latency_ms"])),
            ))
    else:
        lines.append(t("gateway.provider.no_keys", lang))

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=get_provider_menu_keyboard(provider, is_enabled=is_enabled, lang=lang),
    )
    await callback.answer()


@router.callback_query(AIGatewayCallback.filter(F.action == "provider_enable"))
async def provider_enable(callback: CallbackQuery, callback_data: AIGatewayCallback,
                          settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    await ai_gateway.admin_enable_provider(callback_data.provider)
    await callback.answer(t("gateway.provider.enabled", lang, provider=callback_data.provider.title()), show_alert=True)
    await provider_menu(callback, callback_data, settings_service, ai_gateway)


@router.callback_query(AIGatewayCallback.filter(F.action == "provider_disable"))
async def provider_disable(callback: CallbackQuery, callback_data: AIGatewayCallback,
                           settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    await ai_gateway.admin_disable_provider(callback_data.provider)
    await callback.answer(t("gateway.provider.disabled", lang, provider=callback_data.provider.title()), show_alert=True)
    await provider_menu(callback, callback_data, settings_service, ai_gateway)


# ── Maintenance Mode ───────────────────────────────────────────────────────


@router.callback_query(AIGatewayCallback.filter(F.action == "maintenance_on"))
async def maintenance_on(callback: CallbackQuery, callback_data: AIGatewayCallback,
                         settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    await ai_gateway.admin_set_maintenance(True)
    await callback.answer(t("gateway.maintenance.on", lang), show_alert=True)
    await gateway_status(callback, callback_data, settings_service, ai_gateway)


@router.callback_query(AIGatewayCallback.filter(F.action == "maintenance_off"))
async def maintenance_off(callback: CallbackQuery, callback_data: AIGatewayCallback,
                          settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    await ai_gateway.admin_set_maintenance(False)
    await callback.answer(t("gateway.maintenance.off", lang), show_alert=True)
    await gateway_status(callback, callback_data, settings_service, ai_gateway)


# ── Provider Priority ──────────────────────────────────────────────────────


@router.callback_query(AIGatewayCallback.filter(F.action == "priority_gemini_first"))
async def priority_gemini_first(callback: CallbackQuery, callback_data: AIGatewayCallback,
                                settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    await ai_gateway.admin_set_priority(["gemini", "groq"])
    await callback.answer(t("gateway.priority.gemini_first", lang), show_alert=True)
    await gateway_status(callback, callback_data, settings_service, ai_gateway)


@router.callback_query(AIGatewayCallback.filter(F.action == "priority_groq_first"))
async def priority_groq_first(callback: CallbackQuery, callback_data: AIGatewayCallback,
                              settings_service: SettingsService, ai_gateway: AIGateway | None = None) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang); return
    if ai_gateway is None:
        await _no_gateway(callback, lang); return
    await ai_gateway.admin_set_priority(["groq", "gemini"])
    await callback.answer(t("gateway.priority.groq_first", lang), show_alert=True)
    await gateway_status(callback, callback_data, settings_service, ai_gateway)


# ── Back navigation ────────────────────────────────────────────────────────


@router.callback_query(AIGatewayCallback.filter(F.action == "back"))
async def gateway_back(
    callback: CallbackQuery,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    from app.keyboards.admin_kb import get_admin_menu_keyboard
    await callback.message.edit_text(
        "Admin panel:",
        reply_markup=get_admin_menu_keyboard(lang),
    )
    await callback.answer()
