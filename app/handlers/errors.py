"""Global unhandled-exception handler, registered on the Dispatcher in app.bot.

V1.5: Best-effort language resolution — the error message is shown in the
user's own language where possible, falling back to English then Uzbek.
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import ErrorEvent

from app.texts.messages import t

logger = logging.getLogger(__name__)


async def handle_unexpected_error(event: ErrorEvent, bot: Bot) -> bool:
    """Log the exception and notify the affected user in their language."""
    logger.exception("Unhandled exception while processing update", exc_info=event.exception)

    update = event.update
    chat_id: int | None = None
    tg_user_id: int | None = None

    if update.message is not None:
        chat_id = update.message.chat.id
        if update.message.from_user:
            tg_user_id = update.message.from_user.id
    elif update.callback_query is not None and update.callback_query.message is not None:
        chat_id = update.callback_query.message.chat.id
        if update.callback_query.from_user:
            tg_user_id = update.callback_query.from_user.id

    if chat_id is None:
        return True

    # Best-effort language lookup — never let a lookup failure suppress the error message.
    lang = "en"   # default per spec: "fallback to English"
    if tg_user_id is not None:
        try:
            from app.services.settings_service import SettingsService  # avoid circular at module level
            # settings_service is not directly available here; use the data dict if present
            data: dict = getattr(event, "_data", {}) or {}
            svc: SettingsService | None = data.get("settings_service")
            if svc is not None:
                lang = await svc.get_language(tg_user_id)
        except Exception:
            pass  # silently ignore; we still send the error in the fallback language

    try:
        await bot.send_message(chat_id, t("error_generic", lang))
    except Exception:
        logger.exception(
            "Failed to notify chat_id=%s about the unexpected error", chat_id
        )

    return True
