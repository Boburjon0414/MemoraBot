"""Referral & Coin handlers.

V1.5: All hardcoded strings replaced with t(). Language resolved per-user
via settings_service and threaded through to all formatters/keyboards.
Business logic is untouched.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards.callback_data import (
    AdminCallback,
    AdminReferralCallback,
    DashboardCallback,
    ReferralCallback,
)
from app.keyboards.referral_admin_kb import (
    get_coin_action_cancel_keyboard,
    get_referral_back_keyboard,
    get_referral_control_keyboard,
    get_user_action_keyboard,
)
from app.keyboards.referral_kb import get_coin_history_keyboard, get_invite_friends_keyboard
from app.services.coin_service import CoinService
from app.services.referral_service import ReferralService
from app.services.settings_service import SettingsService
from app.states.bot_states import AdminReferralStates
from app.texts.messages import t
from app.utils.referral_formatters import (
    format_coin_history_page,
    format_invite_friends_page,
    format_recent_referrals,
    format_referral_stats,
    format_top_coin_holders,
    format_top_referrers,
    format_user_admin_profile,
)

logger = logging.getLogger(__name__)
router = Router(name="referral")


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_list


async def _get_lang(settings_service: SettingsService, telegram_id: int) -> str:
    try:
        return await settings_service.get_language(telegram_id)
    except Exception:
        return "uz"


async def _deny(callback: CallbackQuery, lang: str = "uz") -> None:
    await callback.answer(t("admin.denied_callback", lang), show_alert=True)


# ── User-facing: Invite Friends ────────────────────────────────────────────


@router.callback_query(DashboardCallback.filter(F.action == "invite_friends"))
async def show_invite_friends(
    callback: CallbackQuery,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    user = await referral_service._user_repo.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(t("referral.not_registered", lang), show_alert=True)
        return
    stats = await referral_service.get_invite_stats(user.id)
    text = format_invite_friends_page(stats, lang)
    await callback.message.edit_text(text, reply_markup=get_invite_friends_keyboard(lang))
    await callback.answer()


@router.callback_query(ReferralCallback.filter(F.action == "invite_friends"))
async def show_invite_friends_refresh(
    callback: CallbackQuery,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    user = await referral_service._user_repo.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(t("referral.not_registered", lang), show_alert=True)
        return
    stats = await referral_service.get_invite_stats(user.id)
    text = format_invite_friends_page(stats, lang)
    await callback.message.edit_text(text, reply_markup=get_invite_friends_keyboard(lang))
    await callback.answer()


@router.callback_query(ReferralCallback.filter(F.action == "refresh"))
async def refresh_invite_page(
    callback: CallbackQuery,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    user = await referral_service._user_repo.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer()
        return
    stats = await referral_service.get_invite_stats(user.id)
    text = format_invite_friends_page(stats, lang)
    await callback.message.edit_text(text, reply_markup=get_invite_friends_keyboard(lang))
    await callback.answer(t("referral.refreshed", lang))


# ── User-facing: Coin History ──────────────────────────────────────────────


@router.callback_query(ReferralCallback.filter(F.action == "coin_history"))
async def show_coin_history(
    callback: CallbackQuery,
    coin_service: CoinService,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    user = await referral_service._user_repo.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer(t("referral.not_registered", lang), show_alert=True)
        return
    stats = await coin_service.get_lifetime_stats(user.id)
    txs = list(await coin_service.get_history(user.id, limit=20))
    text = format_coin_history_page(stats, txs, lang)
    await callback.message.edit_text(text, reply_markup=get_coin_history_keyboard(lang))
    await callback.answer()


# ── Admin: Referral Control entry ──────────────────────────────────────────


@router.callback_query(AdminCallback.filter(F.action == "referral_ctrl"))
async def admin_referral_control(
    callback: CallbackQuery,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    body = t("admin.referral.title", lang) + "\n\n" + t("admin.referral.subtitle", lang)
    await callback.message.edit_text(body, reply_markup=get_referral_control_keyboard(lang))
    await callback.answer()


@router.callback_query(AdminReferralCallback.filter(F.action == "back"))
async def admin_referral_back(
    callback: CallbackQuery,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    body = t("admin.referral.title", lang) + "\n\n" + t("admin.referral.subtitle", lang)
    await callback.message.edit_text(body, reply_markup=get_referral_control_keyboard(lang))
    await callback.answer()


# ── Admin: Top Referrers ───────────────────────────────────────────────────


@router.callback_query(AdminReferralCallback.filter(F.action == "top_referrers"))
async def admin_top_referrers(
    callback: CallbackQuery,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    rows = await referral_service.get_top_referrers()
    await callback.message.edit_text(
        format_top_referrers(rows, lang),
        reply_markup=get_referral_back_keyboard(lang),
    )
    await callback.answer()


# ── Admin: Top Coin Holders ────────────────────────────────────────────────


@router.callback_query(AdminReferralCallback.filter(F.action == "top_holders"))
async def admin_top_holders(
    callback: CallbackQuery,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    rows = await referral_service.get_top_coin_holders()
    await callback.message.edit_text(
        format_top_coin_holders(rows, lang),
        reply_markup=get_referral_back_keyboard(lang),
    )
    await callback.answer()


# ── Admin: Recent Referrals ────────────────────────────────────────────────


@router.callback_query(AdminReferralCallback.filter(F.action == "recent"))
async def admin_recent_referrals(
    callback: CallbackQuery,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    rows = await referral_service.get_recent_referrals(limit=10)
    await callback.message.edit_text(
        format_recent_referrals(rows, lang),
        reply_markup=get_referral_back_keyboard(lang),
    )
    await callback.answer()


# ── Admin: Referral Statistics ─────────────────────────────────────────────


@router.callback_query(AdminReferralCallback.filter(F.action == "stats"))
async def admin_referral_stats(
    callback: CallbackQuery,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    stats = await referral_service.get_referral_overview_stats()
    await callback.message.edit_text(
        format_referral_stats(stats, lang),
        reply_markup=get_referral_back_keyboard(lang),
    )
    await callback.answer()


# ── Admin: Search User ─────────────────────────────────────────────────────


@router.callback_query(AdminReferralCallback.filter(F.action == "search"))
async def admin_search_prompt(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    await state.set_state(AdminReferralStates.searching_user)
    await state.update_data(admin_lang=lang)
    body = "\n\n".join([
        t("admin.referral.search.title", lang),
        t("admin.referral.search.prompt", lang),
        t("admin.referral.search.hint", lang),
    ])
    await callback.message.edit_text(body, reply_markup=get_coin_action_cancel_keyboard(lang))
    await callback.answer()


@router.message(AdminReferralStates.searching_user)
async def admin_search_execute(
    message: Message,
    state: FSMContext,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    state_data = await state.get_data()
    lang: str = state_data.get("admin_lang") or await _get_lang(settings_service, message.from_user.id)

    query = (message.text or "").strip().lstrip("@")
    telegram_id: int | None = None
    if query.isdigit():
        telegram_id = int(query)
    else:
        user = await referral_service._user_repo.get_by_username(query)
        if user:
            telegram_id = user.telegram_id

    if telegram_id is None:
        await message.answer(
            t("admin.referral.user_not_found", lang),
            reply_markup=get_coin_action_cancel_keyboard(lang),
        )
        return

    profile = await referral_service.get_user_admin_profile(telegram_id)
    if profile is None:
        await message.answer(
            t("admin.referral.id_not_found", lang, telegram_id=str(telegram_id)),
            reply_markup=get_coin_action_cancel_keyboard(lang),
        )
        return

    await state.clear()
    await message.answer(
        format_user_admin_profile(profile, lang),
        reply_markup=get_user_action_keyboard(telegram_id, lang),
    )


# ── Admin: View Coin History for a User ───────────────────────────────────


@router.callback_query(AdminReferralCallback.filter(F.action == "view_history"))
async def admin_view_user_history(
    callback: CallbackQuery,
    callback_data: AdminReferralCallback,
    coin_service: CoinService,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return

    target_id = callback_data.target_id
    profile = await referral_service.get_user_admin_profile(target_id)
    if profile is None:
        await callback.answer(t("admin.referral.not_found_short", lang), show_alert=True)
        return

    user = profile["user"]
    stats = await coin_service.get_lifetime_stats(user.id)
    txs = list(await coin_service.get_history(user.id, limit=20))

    header = t(
        "admin.referral.coin_history_header", lang,
        name=user.full_name,
        telegram_id=str(user.telegram_id),
    )
    body = header + "\n\n" + format_coin_history_page(stats, txs, lang)
    await callback.message.edit_text(body, reply_markup=get_user_action_keyboard(target_id, lang))
    await callback.answer()


# ── Admin: Reset Coins ─────────────────────────────────────────────────────


@router.callback_query(AdminReferralCallback.filter(F.action == "reset_coins"))
async def admin_reset_coins(
    callback: CallbackQuery,
    callback_data: AdminReferralCallback,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return

    target_id = callback_data.target_id
    ok, removed = await referral_service.admin_reset_coins(target_id)
    if not ok:
        await callback.answer(t("admin.referral.not_found_short", lang), show_alert=True)
        return

    profile = await referral_service.get_user_admin_profile(target_id)
    reset_msg = t("admin.referral.reset_done", lang, amount=str(removed))
    if profile:
        body = reset_msg + "\n\n" + format_user_admin_profile(profile, lang)
        await callback.message.edit_text(body, reply_markup=get_user_action_keyboard(target_id, lang))
    await callback.answer(t("admin.referral.reset_answer", lang, amount=str(removed)))


# ── Admin: Add / Remove / Bonus coins — FSM ───────────────────────────────


@router.callback_query(
    AdminReferralCallback.filter(F.action.in_({"add_coins", "remove_coins", "give_bonus"}))
)
async def admin_coin_action_prompt(
    callback: CallbackQuery,
    callback_data: AdminReferralCallback,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return

    action_key_map = {
        "add_coins":   "admin.referral.action.add",
        "remove_coins": "admin.referral.action.remove",
        "give_bonus":  "admin.referral.action.bonus",
    }
    action_label = t(action_key_map.get(callback_data.action, ""), lang) or callback_data.action

    await state.set_state(AdminReferralStates.waiting_coin_amount)
    await state.update_data(
        coin_action=callback_data.action,
        target_telegram_id=callback_data.target_id,
        admin_lang=lang,
    )
    await callback.message.edit_text(
        t("admin.referral.coin_prompt", lang, action=action_label),
        reply_markup=get_coin_action_cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(AdminReferralStates.waiting_coin_amount, F.text)
async def admin_coin_action_execute(
    message: Message,
    state: FSMContext,
    referral_service: ReferralService,
    settings_service: SettingsService,
) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    state_data = await state.get_data()
    lang: str = state_data.get("admin_lang") or await _get_lang(settings_service, message.from_user.id)

    raw = (message.text or "").strip()
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer(
            t("admin.referral.invalid_amount", lang),
            reply_markup=get_coin_action_cancel_keyboard(lang),
        )
        return

    amount = int(raw)
    action: str = state_data.get("coin_action", "")
    target_id: int = state_data.get("target_telegram_id", 0)
    await state.clear()

    result_text = ""
    if action == "add_coins":
        await referral_service.admin_add_coins(
            target_id, amount, t("admin.referral.tx.add_reason", lang)
        )
        result_text = t("admin.referral.coin_added", lang, amount=str(amount))
    elif action == "remove_coins":
        ok = await referral_service.admin_remove_coins(
            target_id, amount, t("admin.referral.tx.remove_reason", lang)
        )
        result_text = (
            t("admin.referral.coin_removed", lang, amount=str(amount))
            if ok
            else t("admin.referral.coin_insufficient", lang)
        )
    elif action == "give_bonus":
        await referral_service.admin_give_bonus(
            target_id, amount, t("admin.referral.tx.bonus_reason", lang)
        )
        result_text = t("admin.referral.bonus_given", lang, amount=str(amount))
    else:
        result_text = t("admin.referral.unknown_action", lang)

    profile = await referral_service.get_user_admin_profile(target_id)
    if profile:
        body = result_text + "\n\n" + format_user_admin_profile(profile, lang)
        await message.answer(body, reply_markup=get_user_action_keyboard(target_id, lang))
    else:
        await message.answer(result_text)


# ── Admin: Cancel action ───────────────────────────────────────────────────


@router.callback_query(AdminReferralCallback.filter(F.action == "cancel_action"))
async def admin_cancel_action(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not _is_admin(callback.from_user.id):
        await _deny(callback, lang)
        return
    await state.clear()
    body = t("admin.referral.title", lang) + "\n\n" + t("admin.referral.subtitle", lang)
    await callback.message.edit_text(body, reply_markup=get_referral_control_keyboard(lang))
    await callback.answer(t("admin.referral.cancelled", lang))
