"""Private `/admin` analytics interface.

The handler only presents data. Query logic stays in ``AnalyticsService``;
authorization is deliberately checked on every command and callback.
"""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards.admin_kb import (
    get_admin_back_keyboard,
    get_admin_menu_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_prompt_keyboard,
)
from app.keyboards.callback_data import AdminCallback, BroadcastCallback
from app.services.analytics_service import AnalyticsService
from app.services.broadcast_service import BroadcastService
from app.states.bot_states import BroadcastStates
from app.utils.admin_formatters import (
    format_admin_overview,
    format_ai_report,
    format_growth_report,
    format_quality_report,
    format_word_ranking,
)

router = Router(name="admin")


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_list


async def _deny_callback(callback: CallbackQuery) -> None:
    await callback.answer("⛔ Bu bo'lim faqat administratorlar uchun.", show_alert=True)


@router.message(Command("admin"))
async def open_admin_panel(message: Message, analytics_service: AnalyticsService) -> None:
    """Open the protected analytics dashboard for an authorised administrator."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin panelga kirish huquqi yo'q.")
        return

    overview = await analytics_service.overview()
    await message.answer(format_admin_overview(overview), reply_markup=get_admin_menu_keyboard())


@router.callback_query(AdminCallback.filter(F.action == "overview"))
async def admin_overview(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    overview = await analytics_service.overview()
    await callback.message.edit_text(format_admin_overview(overview), reply_markup=get_admin_menu_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "requested"))
async def most_requested(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    items = await analytics_service.most_requested_words()
    text = format_word_ranking("🔥 <b>Eng ko'p so'ralgan 10 ta so'z</b>", items, "jami ko'rishlar")
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "regenerated"))
async def most_regenerated(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    items = await analytics_service.most_regenerated_words()
    text = format_word_ranking("🔄 <b>Eng ko'p qayta yaratilgan 10 ta so'z</b>", items, "qayta yaratishlar")
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "quality"))
async def quality_report(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    best = await analytics_service.highest_rated_active()
    worst = await analytics_service.lowest_rated_active()
    await callback.message.edit_text(format_quality_report(best, worst), reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "ai"))
async def ai_report(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    providers = await analytics_service.ai_provider_usage()
    prompts = await analytics_service.prompt_version_performance()
    await callback.message.edit_text(format_ai_report(providers, prompts), reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "growth"))
async def growth_report(callback: CallbackQuery, analytics_service: AnalyticsService) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    items = await analytics_service.library_growth_by_day()
    await callback.message.edit_text(format_growth_report(items), reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "close"))
async def close_admin_panel(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return
    await callback.message.delete()
    await callback.answer()


# ── Broadcast ──────────────────────────────────────────────────────────────


@router.callback_query(AdminCallback.filter(F.action == "broadcast"))
async def broadcast_entry(callback: CallbackQuery, state: FSMContext) -> None:
    """Open the broadcast composer: ask the admin to type the message text."""
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return

    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.edit_text(
        "📢 <b>Xabar tarqatish</b>\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabarni yuboring.\n\n"
        "<i>Faqat matn xabarlari qo'llab-quvvatlanadi (V1).</i>",
        reply_markup=get_broadcast_prompt_keyboard(),
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message, F.text)
async def broadcast_receive_text(message: Message, state: FSMContext) -> None:
    """Accept the broadcast text and render a preview with confirm / cancel."""
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    await state.update_data(broadcast_text=message.text)

    preview = (
        "👀 <b>Ko'rinish (Preview):</b>\n\n"
        f"{message.text}\n\n"
        "─────────────────────\n"
        "📤 Barcha ro'yxatdan o'tgan foydalanuvchilarga yuboriladi.\n"
        "Tasdiqlaysizmi?"
    )
    await message.answer(preview, reply_markup=get_broadcast_confirm_keyboard())


@router.message(BroadcastStates.waiting_for_message)
async def broadcast_invalid_content(message: Message) -> None:
    """Reject non-text content (photos, stickers, …) while composing a broadcast."""
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "❗️ Faqat matn xabarlari qo'llab-quvvatlanadi.\n"
        "Iltimos, matn ko'rinishida xabar yuboring."
    )


@router.callback_query(BroadcastCallback.filter(F.action == "confirm"))
async def broadcast_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    broadcast_service: BroadcastService,
    bot: Bot,
) -> None:
    """Admin confirmed: clear FSM, schedule background broadcast, show status."""
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return

    data = await state.get_data()
    broadcast_text: str | None = data.get("broadcast_text")

    if not broadcast_text:
        # Guard against stale / double-tap confirm with no text in state.
        await callback.answer(
            "⚠️ Xabar topilmadi. Iltimos, /admin orqali qayta urinib ko'ring.",
            show_alert=True,
        )
        await state.clear()
        return

    admin_id = callback.from_user.id
    await state.clear()

    total = await broadcast_service.start_broadcast(bot, broadcast_text, admin_id)

    await callback.message.edit_text(
        "📢 <b>Broadcast boshlandi!</b>\n\n"
        f"📊 Jami <b>{total}</b> ta foydalanuvchiga xabar yuborilmoqda.\n\n"
        "Jarayon tugagach statistika siz ga alohida xabar sifatida yuboriladi. ✅"
    )
    await callback.answer("Broadcast boshlandi!")


@router.callback_query(BroadcastCallback.filter(F.action == "cancel"))
async def broadcast_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    analytics_service: AnalyticsService,
) -> None:
    """Admin cancelled at any step — clear FSM and return to the admin overview."""
    if not _is_admin(callback.from_user.id):
        await _deny_callback(callback)
        return

    await state.clear()
    overview = await analytics_service.overview()
    await callback.message.edit_text(
        format_admin_overview(overview),
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer("Bekor qilindi.")
