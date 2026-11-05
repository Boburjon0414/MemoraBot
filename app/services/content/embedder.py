"""Embedder: converts text into a dense float vector for semantic search.

Abstraction rationale
---------------------
The embedding model is one of the most likely things to change as the
platform matures: from a mock during development, to a text-generation
workaround via AIRouter, to a dedicated embedding API endpoint (Gemini
`text-embedding-004`, Groq/Nomic, OpenAI `text-embedding-3-small`).

Hiding the implementation behind `Embedder(ABC)` means `ContentService`,
`RAGService`, and `QuizService` never need to change when the embedding
backend changes — only the concrete class in `PlatformContainer` swaps.

Concrete implementations (Step 6)
-----------------------------------
  MockEmbedder
    - Returns a deterministic pseudo-random vector seeded from the text.
    - Vectors are meaningless for semantic similarity but structurally
      correct (right shape, normalised).
    - Used in development, CI, and any environment without API keys.
    - Also used as the default in PlatformContainer so the bot starts
      cleanly without embedding API configuration.

  AIRouterEmbedder (future — when proper embedding API is configured)
    - Calls the provider's embedding endpoint via AIRouter.
    - For Gemini: POST /v1beta/models/text-embedding-004:embedContent
    - For Groq: not available natively; routes to Nomic via OpenAI compat.
    - Replaced by dedicated EmbeddingProvider classes when scale requires it.

Dimension conventions
---------------------
  MockEmbedder:    128 dimensions (fast, low memory for tests)
  Gemini embed-004: 768 dimensions
  OpenAI 3-small:  1536 dimensions

EmbeddingStore stores whatever dimension the configured embedder produces.
It MUST use the same embedder at both index time and query time — mixing
dimensions will produce incorrect similarity scores with no error at the
DB level.  PlatformContainer enforces this by sharing one Embedder instance
between ContentService (indexing) and RAGService (querying).
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod


class Embedder(ABC):
    """Abstract base: convert a text string into a float embedding vector."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier stored in ContentChunk.embedding_model."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Length of the vector returned by embed()."""
        raise NotImplementedError

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embed `text` and return a unit-normalised float vector.

        The returned vector has exactly `self.dimensions` elements.
        All implementations MUST normalise to unit length (L2 norm = 1.0)
        so that cosine similarity reduces to a dot product, which is what
        SQLiteEmbeddingStore computes.

        Args:
            text: The text to embed.  Leading/trailing whitespace is ignored.

        Returns:
            A list of `self.dimensions` floats, unit-normalised.

        Raises:
            EmbeddingError: if the embedding call fails for any reason.
        """
        raise NotImplementedError

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts sequentially.

        Concrete classes that support native batching (Gemini, OpenAI)
        should override this for efficiency.  The default implementation
        calls embed() in a loop — safe but slow for large batches.
        """
        return [await self.embed(text) for text in texts]


class EmbeddingError(Exception):
    """Raised when an embedding call fails."""


class MockEmbedder(Embedder):
    """Deterministic pseudo-random embedder for development and testing.

    Produces a 128-dimensional vector seeded from the SHA-256 hash of the
    input text.  Vectors are unit-normalised so cosine similarity arithmetic
    works correctly even though the values are semantically meaningless.

    Identical inputs always produce identical vectors, which makes tests
    reproducible and cache hits detectable.

    Usage::
        embedder = MockEmbedder()
        vec = await embedder.embed("The Eiffel Tower is in Paris")
        assert len(vec) == 128
        assert abs(sum(x**2 for x in vec) - 1.0) < 1e-6  # unit norm
    """

    _DIMENSIONS = 128

    @property
    def model_name(self) -> str:
        return "mock"

    @property
    def dimensions(self) -> int:
        return self._DIMENSIONS

    async def embed(self, text: str) -> list[float]:
        """Return a deterministic unit-normalised vector for `text`."""
        text = text.strip()
        # Seed a pseudo-random sequence from the text hash.
        # Using SHA-256 gives good distribution across the vector space.
        digest = hashlib.sha256(text.encode("utf-8")).digest()

        # Generate _DIMENSIONS floats by repeating and slicing the digest.
        raw: list[float] = []
        seed = digest
        while len(raw) < self._DIMENSIONS:
            # Each byte gives a float in [-1, 1]
            for b in seed:
                raw.append((b / 127.5) - 1.0)
                if len(raw) == self._DIMENSIONS:
                    break
            # If we need more values, hash the hash
            if len(raw) < self._DIMENSIONS:
                seed = hashlib.sha256(seed).digest()

        vec = raw[: self._DIMENSIONS]

        # L2-normalise to unit length
        magnitude = math.sqrt(sum(x * x for x in vec))
        if magnitude < 1e-9:
            # Extremely unlikely with SHA-256 output, but handle it safely
            return [0.0] * self._DIMENSIONS
        return [x / magnitude for x in vec]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed — all synchronous so no performance penalty here."""
        return [await self.embed(t) for t in texts]
