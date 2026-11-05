"""Factory that instantiates the AI provider (or AI Gateway).

V1.5: Added "gateway" provider type that builds a full AIGateway with
Free/Premium key pools, load balancing, and automatic failover.

Provider selection via AI_PROVIDER in .env:
  "gateway"  → full AI Gateway (recommended for production)
  "gemini"   → single GeminiProvider (legacy, single key/model)
  "groq"     → single GroqProvider (single key/model)
  "mock"     → offline MockProvider (development/CI)

The public interface (create_ai_provider → AIProvider) is unchanged.
"""
from __future__ import annotations

import logging

from app.config import Settings
from app.services.ai.base import MnemonicProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.groq_provider import GroqProvider
from app.services.ai.gateway import AIGateway, RuntimeConfig
from app.services.ai.gateway.key_slot import GatewayKeySlot
from app.services.ai.knowledge_engine.exceptions import KnowledgeEngineError
from app.services.ai.mnemonic_prompt import validate_mnemonic_prompt
from app.services.ai.mock_provider import MockProvider

logger = logging.getLogger(__name__)


async def create_ai_provider(settings: Settings) -> MnemonicProvider:
    """Instantiate the AIProvider (or AIGateway) configured in settings.

    Falls back to MockProvider when a real provider is configured but
    cannot be initialised (missing keys, broken knowledge base, etc.),
    so the bot always remains runnable.
    """
    provider_name = settings.ai_provider.strip().lower()

    # ── Validate shared dependency: knowledge base ─────────────────────── #
    if provider_name != "mock":
        try:
            await validate_mnemonic_prompt(version=settings.mnemonic_prompt_version)
        except KnowledgeEngineError:
            logger.exception(
                "Mnemonic knowledge base (version=%s) failed validation — "
                "falling back to MockProvider.",
                settings.mnemonic_prompt_version,
            )
            return MockProvider()

    # ── Gateway mode (production) ──────────────────────────────────────── #
    if provider_name == "gateway":
        return await _create_gateway(settings)

    # ── Legacy single-provider modes ───────────────────────────────────── #
    if provider_name == "gemini":
        if not settings.gemini_api_key:
            logger.warning(
                "AI_PROVIDER=gemini but GEMINI_API_KEY is empty — "
                "falling back to MockProvider."
            )
            return MockProvider()
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            prompt_version=settings.mnemonic_prompt_version,
        )

    if provider_name == "groq":
        if not settings.groq_api_key:
            logger.warning(
                "AI_PROVIDER=groq but GROQ_API_KEY is empty — "
                "falling back to MockProvider."
            )
            return MockProvider()
        return GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            prompt_version=settings.mnemonic_prompt_version,
        )

    if provider_name == "mock":
        return MockProvider()

    logger.warning(
        "Unknown AI_PROVIDER=%r — falling back to MockProvider.", settings.ai_provider
    )
    return MockProvider()


async def _create_gateway(settings: Settings) -> MnemonicProvider:
    """Build and return a fully configured AIGateway.

    Falls back to MockProvider if no keys are configured at all.
    """
    runtime = RuntimeConfig()
    await runtime.load()

    gateway = AIGateway(
        prompt_version=settings.mnemonic_prompt_version,
        runtime_config=runtime,
    )

    # ── Register key slots ─────────────────────────────────────────────── #
    total_slots = 0

    # Gemini free keys
    for idx, key in enumerate(settings.free_gemini_key_list, start=1):
        gateway.register_slot(GatewayKeySlot(
            provider_name="gemini",
            key_index=idx,
            tier="free",
            api_key=key,
            models=settings.gemini_model_list,
            prompt_version=settings.mnemonic_prompt_version,
            request_timeout=settings.gateway_request_timeout,
        ))
        total_slots += 1

    # Gemini premium keys
    for idx, key in enumerate(settings.premium_gemini_key_list, start=1):
        gateway.register_slot(GatewayKeySlot(
            provider_name="gemini",
            key_index=idx,
            tier="premium",
            api_key=key,
            models=settings.gemini_model_list,
            prompt_version=settings.mnemonic_prompt_version,
            request_timeout=settings.gateway_request_timeout,
        ))
        total_slots += 1

    # Groq free keys
    for idx, key in enumerate(settings.free_groq_key_list, start=1):
        gateway.register_slot(GatewayKeySlot(
            provider_name="groq",
            key_index=idx,
            tier="free",
            api_key=key,
            models=settings.groq_model_list,
            prompt_version=settings.mnemonic_prompt_version,
            request_timeout=settings.gateway_request_timeout,
        ))
        total_slots += 1

    # Groq premium keys
    for idx, key in enumerate(settings.premium_groq_key_list, start=1):
        gateway.register_slot(GatewayKeySlot(
            provider_name="groq",
            key_index=idx,
            tier="premium",
            api_key=key,
            models=settings.groq_model_list,
            prompt_version=settings.mnemonic_prompt_version,
            request_timeout=settings.gateway_request_timeout,
        ))
        total_slots += 1

    # ── Safety check ───────────────────────────────────────────────────── #
    if total_slots == 0:
        logger.warning(
            "AI_PROVIDER=gateway but no API keys are configured "
            "(FREE_GEMINI_KEYS, PREMIUM_GEMINI_KEYS, FREE_GROQ_KEYS, "
            "PREMIUM_GROQ_KEYS are all empty) — falling back to MockProvider."
        )
        return MockProvider()

    logger.info(
        "AI Gateway ready: %d key slot(s) registered across "
        "providers=%s (priority: %s)",
        total_slots,
        list(runtime.enabled_providers),
        runtime.provider_priority,
    )
    return gateway
