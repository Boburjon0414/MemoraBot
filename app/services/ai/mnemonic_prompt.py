"""Mnemonic-specific prompt assembly.

This is the ONLY file in the codebase that knows the knowledge base lives
at `app/knowledge/<version>/`, or that regeneration needs an optional
"avoid repeating these" section spliced in. Everything generic — loading,
validating, assembling, versioning — lives in `knowledge_engine/` and knows
nothing about any of this.

A future feature needing its own AI prompt (chat, statistics summaries,
...) would follow this same pattern: a small adapter file next to this one,
pointing at its own knowledge base, reusing the same `PromptBuilder`.
"""

from __future__ import annotations

from pathlib import Path

from app.services.ai.knowledge_engine import KnowledgeLoader, KnowledgeVersionManager, PromptBuilder
from app.services.ai.knowledge_engine import KnowledgeValidator as _KnowledgeValidator

_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"
_DEFAULT_VERSION = "v1"
_MAX_AVOID_ITEMS_IN_PROMPT = 8

_version_manager = KnowledgeVersionManager(_KNOWLEDGE_DIR)
_builder = PromptBuilder(loader=KnowledgeLoader(_version_manager), validator=_KnowledgeValidator())


async def build_mnemonic_prompt(
    word: str,
    avoid: list[str] | None = None,
    *,
    version: str = _DEFAULT_VERSION,
) -> str:
    """Build the full prompt asking for a mnemonic for `word`.

    Args:
        word: the English word/phrase to build a mnemonic for.
        avoid: previously-used Uzbek pronunciation similarities for this
            word, if any — passed by the "🔄 Generate Another Mnemonic"
            regenerate flow. When given, `regenerate_avoid.md` is spliced in
            right before the final word/JSON request, telling the model to
            avoid repeating them.
        version: which `app/knowledge/<version>/` to build from. Callers (in
            practice, `GeminiProvider`) should pass
            `settings.mnemonic_prompt_version` here rather than relying on
            the default, so switching versions is a config change, not a
            code change.
    """
    extra: list[str] = []
    context: dict[str, str] = {"word": word}

    if avoid:
        avoid_items = "\n".join(f'- "{item}"' for item in avoid[:_MAX_AVOID_ITEMS_IN_PROMPT])
        extra.append("regenerate_avoid.md")
        context["avoid_items"] = avoid_items

    extra.append("user_prompt.md")

    return await _builder.build(version, extra=extra, **context)


async def validate_mnemonic_prompt(version: str = _DEFAULT_VERSION) -> None:
    """Eagerly validate the mnemonic knowledge base for `version`.

    Called once at startup (see `factory.create_ai_provider`) so a broken or
    misconfigured knowledge file is caught immediately with a clear log
    message, instead of surfacing as a confusing failure on someone's first
    word lookup. Reuses `build_mnemonic_prompt` itself (with throwaway
    input) rather than a separate validate-only path.

    Raises:
        app.services.ai.knowledge_engine.exceptions.KnowledgeEngineError: if
            the knowledge base is missing, empty, or otherwise invalid.
    """
    await build_mnemonic_prompt("test", version=version)


def list_available_prompt_versions() -> list[str]:
    """List every knowledge-base version available on disk.

    Exposed for a future Admin Panel "Prompt Version Information" screen.
    """
    return _version_manager.list_versions()
