"""Global unhandled-exception handler, registered directly on the Dispatcher
via `dp.errors.register(...)` in `app.bot` (error handlers are simplest and
most reliable when attached at the Dispatcher level rather than a sub-router).
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import ErrorEvent

from app.texts.messages import t

logger = logging.getLogger(__name__)


async def handle_unexpected_error(event: ErrorEvent, bot: Bot) -> bool:
    """Log the exception and, where possible, let the affected user know
    politely instead of leaving them with a silently-broken bot.
    """
    logger.exception("Unhandled exception while processing update", exc_info=event.exception)

    update = event.update
    chat_id: int | None = None
    if update.message is not None:
        chat_id = update.message.chat.id
    elif update.callback_query is not None and update.callback_query.message is not None:
        chat_id = update.callback_query.message.chat.id

    if chat_id is not None:
        try:
            await bot.send_message(chat_id, t("error_generic", "uz"))
        except Exception:
            logger.exception("Failed to notify chat_id=%s about the unexpected error", chat_id)

    return True
