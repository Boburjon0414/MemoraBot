"""Exceptions for the knowledge engine.

Kept in their own module since `loader.py`, `validator.py`, and
`version_manager.py` all need to raise and/or catch these, and a shared
home avoids them importing from each other just for exception classes.

All inherit from the app-wide `MemoraBotError`, so callers that only care
about "did *something* go wrong in MemoraBot" can still catch broadly,
while `GeminiProvider` specifically catches `KnowledgeEngineError` to
translate it into the existing `AIProviderError` the rest of the app
already knows how to handle gracefully.
"""

from __future__ import annotations

from app.core.exceptions import MemoraBotError


class KnowledgeEngineError(MemoraBotError):
    """Base class for all knowledge-engine errors."""


class KnowledgeVersionNotFoundError(KnowledgeEngineError):
    """The requested knowledge base version doesn't exist on disk."""


class KnowledgeFileNotFoundError(KnowledgeEngineError):
    """A required knowledge file (a component or manifest.yaml) does not exist on disk."""


class KnowledgeManifestError(KnowledgeEngineError):
    """manifest.yaml is missing required keys, isn't valid YAML, or isn't a mapping."""


class KnowledgeValidationError(KnowledgeEngineError):
    """A loaded knowledge set failed validation: empty file, duplicate section,
    duplicate/empty component list, or a version mismatch between the
    requested version and what manifest.yaml itself declares.
    """
