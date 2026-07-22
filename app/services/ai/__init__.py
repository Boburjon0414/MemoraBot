"""AI provider abstraction: the swappable mnemonic-generation backend.

    AIProvider        -> abstract interface (app.services.ai.base)
    MnemonicResult    -> structured output contract (app.services.ai.schemas)
    GeminiProvider    -> concrete implementation backed by Google Gemini
    GroqProvider      -> concrete implementation backed by Groq
    MockProvider      -> concrete offline implementation for dev/testing
    AIGateway         -> production gateway with pooling & failover
    create_ai_provider -> factory that picks a provider based on Settings
"""

from app.services.ai.base import AIProvider
from app.services.ai.factory import create_ai_provider
from app.services.ai.gateway import AIGateway, RuntimeConfig, TierProxy
from app.services.ai.schemas import MnemonicResult

__all__ = [
    "AIProvider",
    "AIGateway",
    "TierProxy",
    "RuntimeConfig",
    "MnemonicResult",
    "create_ai_provider",
]
