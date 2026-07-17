"""The prompt engine: generic, provider-agnostic infrastructure for
assembling versioned, Markdown-authored prompts.

    PromptLoader     -> reads metadata.yaml + component files from disk (async)
    PromptValidator   -> checks a loaded set for missing/empty/duplicate/version issues
    PromptBuilder      -> orchestrates the two above, returns one final prompt string
    PromptEngineError  -> base exception; subclasses in .exceptions

Nothing in this package knows about "mnemonic", "word", "Gemini", or any
other feature/provider-specific concept — see `app/services/ai/mnemonic_prompt.py`
for the thin, feature-specific adapter that sits on top of this.
"""

from app.services.ai.prompt_engine.builder import PromptBuilder
from app.services.ai.prompt_engine.exceptions import (
    PromptEngineError,
    PromptFileNotFoundError,
    PromptMetadataError,
    PromptValidationError,
)
from app.services.ai.prompt_engine.loader import PromptLoader, PromptMetadata
from app.services.ai.prompt_engine.validator import PromptValidator

__all__ = [
    "PromptBuilder",
    "PromptLoader",
    "PromptMetadata",
    "PromptValidator",
    "PromptEngineError",
    "PromptFileNotFoundError",
    "PromptMetadataError",
    "PromptValidationError",
]
