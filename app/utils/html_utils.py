"""HTML sanitisation utilities for Telegram messages.

Converts common Markdown patterns to Telegram-compatible HTML.
Has no external dependencies — safe to import in tests and handlers alike.
"""

from __future__ import annotations

import re

_MAX_TG_MESSAGE = 4000


def sanitise_html(raw: str) -> str:
    """Lightly sanitise AI output for Telegram HTML parse_mode.

    The AI is instructed to produce Telegram HTML, but occasionally outputs
    Markdown.  This function converts the most common patterns and truncates
    oversized messages.

    Conversions applied (in order):
      ```...```  → <code>...</code>
      `...`      → <code>...</code>
      **...**    → <b>...</b>
      __...__    → <b>...</b>
      *...*      → <i>...</i>
      _..._      → <i>...</i>
    """
    text = raw.strip()

    # Fenced code blocks (``` … ```)
    text = re.sub(r"```[a-zA-Z]*\n?(.*?)```", r"<code>\1</code>", text, flags=re.DOTALL)

    # Inline code (`…`)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold: **…** or __…__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__",     r"<b>\1</b>", text)

    # Italic: *…* or _…_
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"_(.+?)_",       r"<i>\1</i>", text)

    # Truncate to Telegram's message length limit
    if len(text) > _MAX_TG_MESSAGE:
        text = text[:_MAX_TG_MESSAGE - 1] + "…"

    return text
