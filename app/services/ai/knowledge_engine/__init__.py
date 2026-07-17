"""The knowledge engine: generic, provider-agnostic infrastructure for
assembling versioned, Markdown-authored prompts from `app/knowledge/`.

    KnowledgeVersionManager -> resolves/lists versions on disk
    KnowledgeLoader          -> reads manifest.yaml + component files (async)
    KnowledgeValidator        -> checks a loaded set for missing/empty/duplicate/version issues
    PromptBuilder              -> orchestrates the three above, returns one final prompt string
    KnowledgeEngineError        -> base exception; subclasses in .exceptions

Nothing in this package knows about "mnemonic", "word", "Gemini", or any
other feature/provider-specific concept — see
`app/services/ai/mnemonic_prompt.py` for the thin, feature-specific adapter
that sits on top of this.
"""

from app.services.ai.knowledge_engine.builder import PromptBuilder
from app.services.ai.knowledge_engine.exceptions import (
    KnowledgeEngineError,
    KnowledgeFileNotFoundError,
    KnowledgeManifestError,
    KnowledgeValidationError,
    KnowledgeVersionNotFoundError,
)
from app.services.ai.knowledge_engine.loader import KnowledgeLoader, KnowledgeManifest
from app.services.ai.knowledge_engine.validator import KnowledgeValidator
from app.services.ai.knowledge_engine.version_manager import KnowledgeVersionManager

__all__ = [
    "PromptBuilder",
    "KnowledgeLoader",
    "KnowledgeManifest",
    "KnowledgeValidator",
    "KnowledgeVersionManager",
    "KnowledgeEngineError",
    "KnowledgeFileNotFoundError",
    "KnowledgeManifestError",
    "KnowledgeValidationError",
    "KnowledgeVersionNotFoundError",
]
