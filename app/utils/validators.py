"""Small input-validation helpers."""

from __future__ import annotations

import re

# A single word or short hyphenated/apostrophised phrase (e.g. "give up"),
# letters only, capped at a sane length.
_WORD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\-' ]{0,48}$")


def is_valid_english_word(text: str) -> bool:
    """Return True if `text` looks like a single English word or short phrase."""
    return bool(_WORD_PATTERN.match(text.strip()))
