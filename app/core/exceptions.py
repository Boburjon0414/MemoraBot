"""Custom exception hierarchy for MemoraBot.

Handlers should never need to catch raw SQLAlchemy or aiohttp exceptions —
services translate low-level failures into one of these instead, so the
presentation layer only ever needs to know about `MemoraBotError` subclasses.
"""

from __future__ import annotations


class MemoraBotError(Exception):
    """Base class for all application-specific errors."""


class AIProviderError(MemoraBotError):
    """Raised when an AI provider fails to generate a mnemonic."""


class InvalidWordError(MemoraBotError):
    """Raised when user input does not look like a valid word or short phrase."""


class UserNotRegisteredError(MemoraBotError):
    """Raised when an operation requires a registered user but none was found."""
