"""The `MnemonicProvider` interface: the single seam that lets MemoraBot swap
mnemonic-generation backends (Gemini, OpenAI, a local model, ...) without
ever touching `MnemonicService` or the handlers layer.

This is the Open/Closed and Dependency-Inversion piece of the architecture:
`MnemonicService` depends only on this abstraction, never on a concrete
provider class.

Renamed from `AIProvider` → `MnemonicProvider` to make the scope of this
interface explicit: it generates mnemonics only. The generic AI call
interface (for chat, RAG, quiz generation, etc.) lives in
`app/services/ai/router.py` as `AIRouter`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.ai.schemas import MnemonicResult


class MnemonicProvider(ABC):
    """Abstract base class every mnemonic-generation provider must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this provider, persisted alongside generated entries."""
        raise NotImplementedError

    @property
    @abstractmethod
    def prompt_version(self) -> str:
        """Which knowledge-base/prompt version this provider is using,
        persisted alongside generated entries for analytics (e.g. "prompt
        version performance"). Providers that don't use a versioned
        knowledge base (like `MockProvider`) can return a fixed constant.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_mnemonic(self, word: str, avoid: list[str] | None = None) -> MnemonicResult:
        """Generate structured mnemonic data for `word`.

        Args:
            word: the English word/phrase to build a mnemonic for.
            avoid: previously-used Uzbek pronunciation similarities for this
                same word, if any (passed by the "🔄 Generate Another
                Mnemonic" regenerate flow). Implementations should steer
                away from repeating these, so regeneration produces a
                genuinely different result rather than a near-duplicate.
                `None`/empty means there's nothing to avoid yet.

        Raises:
            app.core.exceptions.AIProviderError: if generation fails for any reason
                (network failure, malformed response, timeout, etc.).
        """
        raise NotImplementedError


# Backward-compatibility alias — remove after all call sites are updated.
AIProvider = MnemonicProvider
