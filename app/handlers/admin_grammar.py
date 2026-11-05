"""Admin Grammar Lessons handler.

Allows admins to add, edit, enable/disable, reorder, and delete grammar
lessons without touching code, .env (beyond GRAMMAR_CHANNEL_ID), or
restarting the bot.

Flow overview
-------------
Admin panel → 📚 Grammar Lessons (AdminGrammarCallback action="menu")
  ├── ➕ Add Lesson (forward)   → AdminGrammarStates.waiting_forward
  │     → forward message from channel → validate → ask name → ask button → save
  ├── ⌨️ Add Lesson (ID)         → AdminGrammarStates.waiting_manual_msg_id
  │     → enter message ID → validate → ask name → ask button → save
  ├── 📋 All Lessons             → paginated list with per-topic actions
  └── Per-topic keyboard:
        ✏️ Edit Name             → AdminGrammarStates.waiting_topic_name
        🔘 Edit Button Name      → AdminGrammarStates.waiting_button_name
        🔗 Edit Message ID       → AdminGrammarStates.waiting_forward (edit mode)
        🟢/🔴 Toggle             → flip is_active
        ⬆️/⬇️ Move               → swap order_index
        🗑 Delete                → AdminGrammarStates.confirm_delete

Security
--------
Every entry point calls _require_admin().  Unauthorised users receive the
standard denied response.  Channel ID always comes from settings.grammar_channel_id
— users can never inject an arbitrary channel ID.

FSM state keys (add flow)
--------------------------
  "agr_msg_id"      — validated channel message_id
  "agr_topic_id"    — GrammarTopic.id being edited (edit flows)
  "agr_edit_field"  — which field is being edited in edit flows
"""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings as _settings
from app.keyboards.admin_grammar_kb import (
    get_admin_grammar_back_keyboard,
    get_admin_grammar_cancel_keyboard,
    get_admin_grammar_confirm_delete_keyboard,
    get_admin_grammar_list_keyboard,
    get_admin_grammar_menu_keyboard,
    get_admin_grammar_topic_keyboard,
)
from app.keyboards.callback_data import AdminGrammarCallback
from app.repositories.grammar_topic_repository import GrammarTopicRepository
from app.services.settings_service import SettingsService
from app.states.bot_states import AdminGrammarStates
from app.texts.messages import t
from app.utils.slug_utils import generate_slug, make_unique_slug
from app.utils.telegram_utils import validate_channel_message as _validate_channel_message

logger = logging.getLogger(__name__)
router = Router(name="admin_grammar")

# FSM key constants
_MSG_ID    = "agr_msg_id"
_TOPIC_ID  = "agr_topic_id"
_EDIT_FIELD= "agr_edit_field"


# ── Auth helper ────────────────────────────────────────────────────────── #

def _is_admin(telegram_id: int) -> bool:
    return telegram_id in _settings.admin_id_list


async def _require_admin(
    callback: CallbackQuery | None = None,
    message: Message | None = None,
    lang: str = "uz",
) -> bool:
    """Return True if the user is an admin.  Send denial and return False otherwise."""
    uid = (callback or message).from_user.id
    if _is_admin(uid):
        return True
    if callback:
        await callback.answer(t("admin.denied_callback", lang), show_alert=True)
    elif message:
        await message.answer(t("admin.denied", lang))
    return False


async def _get_lang(
    settings_service: SettingsService, telegram_id: int
) -> str:
    try:
        return await settings_service.get_language(telegram_id)
    except Exception:
        return "uz"


# ── Grammar menu ───────────────────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action == "menu"))
async def admin_grammar_menu(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return
    await state.clear()

    total = await grammar_topic_repo.count_active()
    await callback.message.edit_text(
        t("admin.grammar.menu_title", lang, total=str(total)),
        reply_markup=get_admin_grammar_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ── List all lessons ───────────────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action == "list"))
async def admin_grammar_list(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return

    topics = await grammar_topic_repo.list_all()
    if not topics:
        await callback.message.edit_text(
            t("admin.grammar.list_empty", lang),
            reply_markup=get_admin_grammar_back_keyboard(lang),
        )
        await callback.answer()
        return

    total = len(topics)
    await callback.message.edit_text(
        t("admin.grammar.menu_title", lang, total=str(total)),
        reply_markup=get_admin_grammar_list_keyboard(topics, lang, page=callback_data.page),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Per-topic edit menu ────────────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action == "edit"))
async def admin_grammar_topic_menu(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return

    topic = await grammar_topic_repo.get_by_id(callback_data.topic_id)
    if topic is None:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return

    btn = topic.button_name or topic.title
    status = "🟢" if topic.is_active else "🔴"
    card = t(
        "admin.grammar.topic_card", lang,
        id=str(topic.id),
        status=status,
        title=topic.title,
        button_name=btn,
        message_id=str(topic.channel_message_id),
        order=str(topic.order_index),
    )
    await callback.message.edit_text(
        card,
        reply_markup=get_admin_grammar_topic_keyboard(topic, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Add lesson: forward flow ───────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action == "add_forward"))
async def admin_grammar_add_forward_start(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return

    if not _settings.grammar_channel_id:
        await callback.message.edit_text(
            t("admin.grammar.error.channel_not_configured", lang),
            reply_markup=get_admin_grammar_back_keyboard(lang),
        )
        await callback.answer()
        return

    await state.set_state(AdminGrammarStates.waiting_forward)
    await state.update_data({_TOPIC_ID: 0, _EDIT_FIELD: "new"})
    await callback.message.edit_text(
        t("admin.grammar.prompt_forward", lang),
        reply_markup=get_admin_grammar_cancel_keyboard(lang),
    )
    await callback.answer()


# ── Add lesson: manual ID flow ─────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action == "add_manual"))
async def admin_grammar_add_manual_start(
    callback: CallbackQuery,
    state: FSMContext,
    settings_service: SettingsService,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return

    if not _settings.grammar_channel_id:
        await callback.message.edit_text(
            t("admin.grammar.error.channel_not_configured", lang),
            reply_markup=get_admin_grammar_back_keyboard(lang),
        )
        await callback.answer()
        return

    await state.set_state(AdminGrammarStates.waiting_manual_msg_id)
    await state.update_data({_TOPIC_ID: 0, _EDIT_FIELD: "new"})
    await callback.message.edit_text(
        t("admin.grammar.prompt_manual_id", lang),
        reply_markup=get_admin_grammar_cancel_keyboard(lang),
    )
    await callback.answer()


# ── Message handler: forward or text in waiting_forward state ──────────── #

@router.message(AdminGrammarStates.waiting_forward)
async def admin_grammar_handle_forward(
    message: Message,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
    bot: Bot,
) -> None:
    lang = await _get_lang(settings_service, message.from_user.id)
    if not await _require_admin(message=message, lang=lang):
        return

    data = await state.get_data()
    expected_channel = _settings.grammar_channel_id
    edit_field = data.get(_EDIT_FIELD, "new")

    # --- Resolve message_id from forwarded message or text ---
    msg_id = await _extract_message_id_from_forward(message, expected_channel, lang)
    if msg_id is None:
        return  # error already sent to admin

    # If the admin forwarded a message (we have forward metadata), the
    # extraction already validated the source channel. No need to perform the
    # network existence check — accept the id as-is. Otherwise (manual numeric
    # entry) perform a copy-based validation to ensure the message exists.
    is_forwarded = bool(getattr(message, "forward_origin", None) or getattr(message, "forward_from_chat", None))
    if not is_forwarded:
        valid = await _validate_channel_message(bot, expected_channel, msg_id, dest_chat_id=message.chat.id)
        if not valid:
            await message.answer(t("admin.grammar.error.msg_not_found", lang))
            return

    if edit_field == "new":
        # Duplicate check
        if await grammar_topic_repo.exists_message_id(msg_id):
            await message.answer(t("admin.grammar.error.duplicate_msg_id", lang))
            return
        # Proceed to topic name input
        await state.update_data({_MSG_ID: msg_id})
        await state.set_state(AdminGrammarStates.waiting_topic_name)
        await message.answer(
            t("admin.grammar.prompt_topic_name", lang),
            reply_markup=get_admin_grammar_cancel_keyboard(lang),
        )
    else:
        # Edit message_id for existing topic
        topic_id = data.get(_TOPIC_ID, 0)
        if await grammar_topic_repo.exists_message_id_excluding(msg_id, topic_id):
            await message.answer(t("admin.grammar.error.duplicate_msg_id", lang))
            return
        topic = await grammar_topic_repo.update(topic_id, channel_message_id=msg_id)
        await state.clear()
        if topic:
            await message.answer(t("admin.grammar.updated", lang, title=topic.title))
        else:
            await message.answer(t("admin.grammar.error.general", lang))


# ── Message handler: manual message ID entry ──────────────────────────── #

@router.message(AdminGrammarStates.waiting_manual_msg_id)
async def admin_grammar_handle_manual_id(
    message: Message,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
    bot: Bot,
) -> None:
    lang = await _get_lang(settings_service, message.from_user.id)
    if not await _require_admin(message=message, lang=lang):
        return

    data = await state.get_data()
    edit_field = data.get(_EDIT_FIELD, "new")
    expected_channel = _settings.grammar_channel_id

    try:
        msg_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer(t("admin.grammar.error.invalid_msg_id", lang))
        return

    valid = await _validate_channel_message(bot, expected_channel, msg_id, dest_chat_id=message.chat.id)
    if not valid:
        await message.answer(t("admin.grammar.error.msg_not_found", lang))
        return

    if edit_field == "new":
        if await grammar_topic_repo.exists_message_id(msg_id):
            await message.answer(t("admin.grammar.error.duplicate_msg_id", lang))
            return
        await state.update_data({_MSG_ID: msg_id})
        await state.set_state(AdminGrammarStates.waiting_topic_name)
        await message.answer(
            t("admin.grammar.prompt_topic_name", lang),
            reply_markup=get_admin_grammar_cancel_keyboard(lang),
        )
    else:
        topic_id = data.get(_TOPIC_ID, 0)
        if await grammar_topic_repo.exists_message_id_excluding(msg_id, topic_id):
            await message.answer(t("admin.grammar.error.duplicate_msg_id", lang))
            return
        topic = await grammar_topic_repo.update(topic_id, channel_message_id=msg_id)
        await state.clear()
        if topic:
            await message.answer(t("admin.grammar.updated", lang, title=topic.title))
        else:
            await message.answer(t("admin.grammar.error.general", lang))


# ── Message handler: topic name (add + edit) ──────────────────────────── #

@router.message(AdminGrammarStates.waiting_topic_name)
async def admin_grammar_handle_topic_name(
    message: Message,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, message.from_user.id)
    if not await _require_admin(message=message, lang=lang):
        return

    data = await state.get_data()
    title = (message.text or "").strip()
    if not title:
        await message.answer(t("admin.grammar.prompt_topic_name", lang))
        return

    edit_field = data.get(_EDIT_FIELD, "new")

    if edit_field == "new":
        await state.update_data({"agr_title": title})
        await state.set_state(AdminGrammarStates.waiting_button_name)
        await message.answer(
            t("admin.grammar.prompt_button_name", lang),
            reply_markup=get_admin_grammar_cancel_keyboard(lang),
        )
    else:
        # Editing existing topic's name
        topic_id = data.get(_TOPIC_ID, 0)
        topic = await grammar_topic_repo.update(topic_id, title=title)
        await state.clear()
        if topic:
            await message.answer(t("admin.grammar.updated", lang, title=topic.title))
        else:
            await message.answer(t("admin.grammar.error.general", lang))


# ── Message handler: button name (final step of add flow, and edit) ──── #

@router.message(AdminGrammarStates.waiting_button_name)
async def admin_grammar_handle_button_name(
    message: Message,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, message.from_user.id)
    if not await _require_admin(message=message, lang=lang):
        return

    data = await state.get_data()
    text = (message.text or "").strip()
    edit_field = data.get(_EDIT_FIELD, "new")

    if edit_field == "new":
        # /skip means use topic name as button name
        if text.lower() in ("/skip", "skip"):
            button_name = None
        else:
            button_name = text or None

        title    = data.get("agr_title", "")
        msg_id   = data.get(_MSG_ID, 0)

        # Generate unique slug
        base_slug = generate_slug(title)
        all_topics = await grammar_topic_repo.list_all()
        existing_slugs = {t.slug for t in all_topics}
        slug = make_unique_slug(base_slug, existing_slugs)

        # Assign sort order
        order_index = await grammar_topic_repo.get_next_order_index()

        topic = await grammar_topic_repo.create_full(
            slug=slug,
            title=title,
            button_name=button_name,
            channel_message_id=msg_id,
            order_index=order_index,
        )
        await state.clear()
        display_btn = button_name or title
        await message.answer(
            t(
                "admin.grammar.added", lang,
                title=topic.title,
                button_name=display_btn,
                message_id=str(topic.channel_message_id),
            )
        )
    else:
        # Editing existing topic's button name
        topic_id = data.get(_TOPIC_ID, 0)
        new_button = text if text and text.lower() not in ("/skip", "skip") else None
        topic = await grammar_topic_repo.update(topic_id, button_name=new_button)
        await state.clear()
        if topic:
            await message.answer(t("admin.grammar.updated", lang, title=topic.title))
        else:
            await message.answer(t("admin.grammar.error.general", lang))


# ── Edit field triggers ────────────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action == "edit_name"))
async def admin_grammar_edit_name(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return
    topic = await grammar_topic_repo.get_by_id(callback_data.topic_id)
    if topic is None:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return
    await state.set_state(AdminGrammarStates.waiting_topic_name)
    await state.update_data({_TOPIC_ID: callback_data.topic_id, _EDIT_FIELD: "name"})
    await callback.message.edit_text(
        t("admin.grammar.prompt_new_name", lang),
        reply_markup=get_admin_grammar_cancel_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(AdminGrammarCallback.filter(F.action == "edit_button"))
async def admin_grammar_edit_button(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return
    topic = await grammar_topic_repo.get_by_id(callback_data.topic_id)
    if topic is None:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return
    await state.set_state(AdminGrammarStates.waiting_button_name)
    await state.update_data({_TOPIC_ID: callback_data.topic_id, _EDIT_FIELD: "button"})
    await callback.message.edit_text(
        t("admin.grammar.prompt_new_button", lang),
        reply_markup=get_admin_grammar_cancel_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(AdminGrammarCallback.filter(F.action == "edit_msgid"))
async def admin_grammar_edit_msgid(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return
    if not _settings.grammar_channel_id:
        await callback.answer(
            t("admin.grammar.error.channel_not_configured", lang), show_alert=True
        )
        return
    topic = await grammar_topic_repo.get_by_id(callback_data.topic_id)
    if topic is None:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return
    await state.set_state(AdminGrammarStates.waiting_forward)
    await state.update_data({_TOPIC_ID: callback_data.topic_id, _EDIT_FIELD: "msgid"})
    await callback.message.edit_text(
        t("admin.grammar.prompt_new_msgid", lang),
        reply_markup=get_admin_grammar_cancel_keyboard(lang),
    )
    await callback.answer()


# ── Toggle active status ───────────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action == "toggle"))
async def admin_grammar_toggle(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return

    topic = await grammar_topic_repo.get_by_id(callback_data.topic_id)
    if topic is None:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return

    new_active = not topic.is_active
    await grammar_topic_repo.set_active(callback_data.topic_id, new_active)
    key = "admin.grammar.enabled" if new_active else "admin.grammar.disabled"
    await callback.answer(t(key, lang, title=topic.title))

    # Refresh the topic card
    topic.is_active = new_active  # optimistic update for display
    btn = topic.button_name or topic.title
    status = "🟢" if new_active else "🔴"
    card = t(
        "admin.grammar.topic_card", lang,
        id=str(topic.id), status=status, title=topic.title,
        button_name=btn, message_id=str(topic.channel_message_id),
        order=str(topic.order_index),
    )
    await callback.message.edit_text(
        card,
        reply_markup=get_admin_grammar_topic_keyboard(topic, lang),
        parse_mode="HTML",
    )


# ── Move up / down ─────────────────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action.in_({"move_up", "move_down"})))
async def admin_grammar_move(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return

    direction = callback_data.action   # "move_up" or "move_down"
    all_topics = await grammar_topic_repo.list_all()
    topic_ids = [t.id for t in all_topics]

    try:
        idx = topic_ids.index(callback_data.topic_id)
    except ValueError:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return

    if direction == "move_up" and idx > 0:
        swapped = await grammar_topic_repo.swap_order(
            callback_data.topic_id, topic_ids[idx - 1]
        )
    elif direction == "move_down" and idx < len(topic_ids) - 1:
        swapped = await grammar_topic_repo.swap_order(
            callback_data.topic_id, topic_ids[idx + 1]
        )
    else:
        await callback.answer()
        return

    if swapped:
        await callback.answer(t("admin.grammar.moved", lang))
    else:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return

    # Refresh list
    topics = await grammar_topic_repo.list_all()
    await callback.message.edit_text(
        t("admin.grammar.menu_title", lang, total=str(len(topics))),
        reply_markup=get_admin_grammar_list_keyboard(topics, lang),
        parse_mode="HTML",
    )


# ── Delete: confirmation ───────────────────────────────────────────────── #

@router.callback_query(AdminGrammarCallback.filter(F.action == "delete"))
async def admin_grammar_delete_prompt(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return

    topic = await grammar_topic_repo.get_by_id(callback_data.topic_id)
    if topic is None:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return

    await state.set_state(AdminGrammarStates.confirm_delete)
    await state.update_data({_TOPIC_ID: callback_data.topic_id})
    await callback.message.edit_text(
        t("admin.grammar.confirm_delete_prompt", lang, title=topic.title),
        reply_markup=get_admin_grammar_confirm_delete_keyboard(callback_data.topic_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AdminGrammarCallback.filter(F.action == "delete_confirm"))
async def admin_grammar_delete_confirm(
    callback: CallbackQuery,
    callback_data: AdminGrammarCallback,
    state: FSMContext,
    settings_service: SettingsService,
    grammar_topic_repo: GrammarTopicRepository,
) -> None:
    """Soft-delete: disable instead of hard-delete to preserve UserGrammarProgress FK."""
    lang = await _get_lang(settings_service, callback.from_user.id)
    if not await _require_admin(callback=callback, lang=lang):
        return

    topic = await grammar_topic_repo.get_by_id(callback_data.topic_id)
    if topic is None:
        await callback.answer(t("admin.grammar.error.general", lang), show_alert=True)
        return

    title = topic.title
    # Soft-delete: disable so UserGrammarProgress FK remains valid
    await grammar_topic_repo.set_active(callback_data.topic_id, False)
    await state.clear()

    await callback.message.edit_text(
        t("admin.grammar.deleted", lang, title=title),
        reply_markup=get_admin_grammar_back_keyboard(lang),
    )
    await callback.answer()


# ── Private helpers ────────────────────────────────────────────────────── #

async def _extract_message_id_from_forward(
    message: Message,
    expected_channel_id: int,
    lang: str,
) -> int | None:
    """Extract and validate message_id from a forwarded channel post.

    Returns the message_id on success, sends an error and returns None on failure.
    """
    # aiogram 3.x: forward_origin for channel posts
    origin = getattr(message, "forward_origin", None)
    if origin is not None:
        origin_type = getattr(origin, "type", None)
        chat = getattr(origin, "chat", None) or getattr(origin, "sender_chat", None)
        origin_msg_id = getattr(origin, "message_id", None)
        logger.debug("_extract_message_id_from_forward: detected forward_origin: type=%s chat=%s msg=%s",
                     origin_type, getattr(chat, "id", None), origin_msg_id)
        if origin_type == "channel" and chat is not None:
            fwd_channel_id = chat.id
            if fwd_channel_id != expected_channel_id:
                await message.answer(
                    t(
                        "admin.grammar.error.wrong_channel", lang,
                        expected=str(expected_channel_id),
                    )
                )
                logger.info(
                    "_extract_message_id_from_forward: forwarded channel id mismatch: got=%s expected=%s",
                    fwd_channel_id, expected_channel_id,
                )
                return None
            msg_id = origin_msg_id
            if msg_id:
                return int(msg_id)
            # No message_id in forward_origin — log and fallthrough to other checks
            logger.warning(
                "_extract_message_id_from_forward: forward_origin from expected channel but no message_id: origin=%s",
                origin,
            )

    # Fallback: if the message itself is from a forwarded channel post (older style)
    fwd_chat = getattr(message, "forward_from_chat", None)
    fwd_msg_id = getattr(message, "forward_from_message_id", None)
    if fwd_chat is not None:
        logger.debug("_extract_message_id_from_forward: detected forward_from_chat: chat=%s msg=%s",
                     getattr(fwd_chat, "id", None), fwd_msg_id)
        if fwd_chat.id != expected_channel_id:
            await message.answer(
                t(
                    "admin.grammar.error.wrong_channel", lang,
                    expected=str(expected_channel_id),
                )
            )
            logger.info(
                "_extract_message_id_from_forward: forward_from_chat id mismatch: got=%s expected=%s",
                fwd_chat.id, expected_channel_id,
            )
            return None
        if fwd_msg_id:
            return int(fwd_msg_id)
        logger.warning(
            "_extract_message_id_from_forward: forward_from_chat present but no forward_from_message_id: message=%s",
            message,
        )

    # If no forward info, try parsing as plain text (for edit_msgid flow)
    if message.text and message.text.strip().isdigit():
        return int(message.text.strip())

    # No usable forward metadata or numeric text — log detected state for debugging
    logger.debug(
        "_extract_message_id_from_forward: failed to extract forward info. forward_origin=%s forward_from_chat=%s forward_from_message_id=%s text=%s",
        getattr(message, "forward_origin", None), getattr(message, "forward_from_chat", None),
        getattr(message, "forward_from_message_id", None), getattr(message, "text", None),
    )

    await message.answer(
        t("admin.grammar.error.wrong_channel", lang, expected=str(expected_channel_id))
    )
    return None


# _validate_channel_message is imported from app.utils.telegram_utils above.
