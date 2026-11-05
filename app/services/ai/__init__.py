"""AI provider abstraction: the swappable mnemonic-generation backend.

    MnemonicProvider  -> abstract interface for mnemonic generation (app.services.ai.base)
    AIProvider        -> backward-compatibility alias for MnemonicProvider
    AIRouter          -> generic AI call interface (app.services.ai.router)
    AIRequest         -> structured AI request value object
    AIResponse        -> structured AI response value object
    MockAIRouter      -> offline AIRouter for tests
    MnemonicResult    -> structured output contract (app.services.ai.schemas)
    GeminiProvider    -> concrete implementation backed by Google Gemini
    GroqProvider      -> concrete implementation backed by Groq
    MockProvider      -> concrete offline implementation for dev/testing
    AIGateway         -> production gateway with pooling & failover
    create_ai_provider -> factory that picks a provider based on Settings
"""

from app.services.ai.base import AIProvider, MnemonicProvider
from app.services.ai.router import AIRequest, AIResponse, AIRouter, MockAIRouter
from app.services.ai.factory import create_ai_provider
from app.services.ai.gateway import AIGateway, RuntimeConfig, TierProxy
from app.services.ai.schemas import MnemonicResult

__all__ = [
    "MnemonicProvider",
    "AIProvider",  # backward-compatibility alias
    "AIRouter",
    "AIRequest",
    "AIResponse",
    "MockAIRouter",
    "AIGateway",
    "TierProxy",
    "RuntimeConfig",
    "MnemonicResult",
    "create_ai_provider",
]
