"""Factory that instantiates the configured `AIProvider`.

This is where `AI_PROVIDER` in settings gets turned into a concrete object.
Adding a new provider (e.g. OpenAI) means writing one new class that
implements `AIProvider` and adding one branch here — nothing else in the
codebase changes.

V1.2: also eagerly validates the mnemonic knowledge base before handing back
a real `GeminiProvider`, so a broken/misconfigured knowledge file is caught
right at startup with a clear log message — exactly like the existing
missing-API-key check — both fall back to `MockProvider` rather than
letting the whole bot crash or silently misbehave.
"""

from __future__ import annotations

import logging

from app.config import Settings
from app.services.ai.base import AIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.knowledge_engine.exceptions import KnowledgeEngineError
from app.services.ai.mnemonic_prompt import validate_mnemonic_prompt
from app.services.ai.mock_provider import MockProvider

logger = logging.getLogger(__name__)


async def create_ai_provider(settings: Settings) -> AIProvider:
    """Instantiate the `AIProvider` configured via `settings.ai_provider`.

    Falls back to `MockProvider` when Gemini is selected but no API key is
    configured, OR when the mnemonic knowledge base fails validation, so
    MemoraBot remains fully runnable (and fails loudly-but-gracefully rather
    than silently) even with a broken `.env` or a broken knowledge file.
    """
    provider_name = settings.ai_provider.strip().lower()

    if provider_name == "gemini":
        if not settings.gemini_api_key:
            logger.warning(
                "AI_PROVIDER is 'gemini' but GEMINI_API_KEY is empty — falling back to "
                "MockProvider. Set GEMINI_API_KEY in .env to enable real generation."
            )
            return MockProvider()

        try:
            await validate_mnemonic_prompt(version=settings.mnemonic_prompt_version)
        except KnowledgeEngineError:
            logger.exception(
                "Mnemonic knowledge base (version=%s) failed validation — falling back to "
                "MockProvider. Check app/knowledge/%s/ for errors.",
                settings.mnemonic_prompt_version,
                settings.mnemonic_prompt_version,
            )
            return MockProvider()

        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            prompt_version=settings.mnemonic_prompt_version,
        )

    if provider_name == "mock":
        return MockProvider()

    logger.warning("Unknown AI_PROVIDER=%r, falling back to MockProvider.", settings.ai_provider)
    return MockProvider()
