"""AI provider abstraction: the swappable mnemonic-generation backend.

    AIProvider        -> abstract interface (app.services.ai.base)
    MnemonicResult    -> structured output contract (app.services.ai.schemas)
    GeminiProvider    -> concrete implementation backed by Google Gemini
    MockProvider      -> concrete offline implementation for dev/testing
    create_ai_provider -> factory that picks a provider based on Settings
"""

from app.services.ai.base import AIProvider
from app.services.ai.factory import create_ai_provider
from app.services.ai.schemas import MnemonicResult

__all__ = ["AIProvider", "MnemonicResult", "create_ai_provider"]
