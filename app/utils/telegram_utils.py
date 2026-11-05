"""Telegram utility helpers with no heavy bot-framework dependencies."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def validate_channel_message(bot, channel_id: int, message_id: int, dest_chat_id: int | None = None) -> bool:
    """Verify a message exists in the channel.

    Avoid forwarding to Saved Messages. If dest_chat_id is provided, attempt to
    copy the channel message to that chat and then delete the copied message
    (keeps the admin chat clean). If dest_chat_id is None, perform a lightweight
    sanity check (ensure IDs are present) and return True — callers should prefer
    using forwarded-message metadata where possible and only call this helper
    when a network check is required.

    Returns True if the message is accessible, False on any error.
    Does not import the full handlers package.
    """
    if not channel_id or not message_id:
        return False
    try:
        # If destination chat is provided, attempt a copy and then delete the copy.
        if dest_chat_id:
            copied = await bot.copy_message(
                chat_id=dest_chat_id,
                from_chat_id=channel_id,
                message_id=message_id,
            )
            # delete the copied message to avoid cluttering the admin chat
            try:
                await bot.delete_message(chat_id=dest_chat_id, message_id=copied.message_id)
            except Exception:
                # Deletion is best-effort; do not fail validation because of it
                logger.debug(
                    "validate_channel_message: failed to delete temp copied message %s in chat %s",
                    getattr(copied, "message_id", None), dest_chat_id,
                )
            return True
        # No dest_chat_id provided: perform a shallow validation (IDs present)
        # Callers should avoid relying solely on this and prefer metadata-based
        # validation when available.
        return True
    except Exception as exc:
        logger.warning(
            "validate_channel_message: channel=%s msg=%s dest_chat=%s — %s",
            channel_id, message_id, dest_chat_id, exc,
        )
        return False
