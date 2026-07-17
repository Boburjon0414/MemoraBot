"""Exceptions for the prompt engine.

Kept in their own module (rather than folded into `loader.py` or
`validator.py`) because both of those modules need to raise and/or catch
these, and a shared home avoids them importing from each other just for
exception classes.

All inherit from the app-wide `MemoraBotError`, so callers that only care
about "did *something* go wrong in MemoraBot" can still catch broadly, while
`GeminiProvider` specifically catches `PromptEngineError` to translate it
into the existing `AIProviderError` the rest of the app already knows how
to handle gracefully.
"""

from __future__ import annotations

from app.core.exceptions import MemoraBotError


class PromptEngineError(MemoraBotError):
    """Base class for all prompt-engine errors."""


class PromptFileNotFoundError(PromptEngineError):
    """A required prompt file (a component or metadata.yaml) does not exist on disk."""


class PromptMetadataError(PromptEngineError):
    """metadata.yaml is missing required keys, isn't valid YAML, or isn't a mapping."""


class PromptValidationError(PromptEngineError):
    """A loaded prompt set failed validation: empty file, duplicate section,
    duplicate/empty component list, or a version mismatch between the
    requested version and what metadata.yaml itself declares.
    """
