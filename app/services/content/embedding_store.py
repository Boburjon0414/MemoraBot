"""EmbeddingStore: stores and retrieves ContentChunk embedding vectors.

Abstraction rationale
---------------------
The storage backend for embeddings is the piece most likely to change when
the platform scales.  SQLite stores vectors as JSON text and computes
cosine similarity in Python — perfect for hundreds of documents and one
developer.  PostgreSQL + pgvector runs ANN searches in C at millions of
chunks — needed when the platform has thousands of users.

`EmbeddingStore(ABC)` hides this difference.  `ContentService`, `RAGService`,
and `QuizService` call `store.upsert()` and `store.search()` and never know
which backend is active.

SQLiteEmbeddingStore — how it works
-------------------------------------
`upsert(chunk, embedding)`:
  Serialises `embedding` as JSON and writes it to `chunk.embedding_json`
  via the provided SQLAlchemy session.  Also updates `chunk.embedding_model`.

`search(query_embedding, source_ids, top_k, min_similarity)`:
  1. Loads all chunks for the given `source_ids` that have an embedding.
  2. Deserialises each `embedding_json` into a Python list.
  3. Computes cosine similarity = dot product (vectors are unit-normalised
     by the Embedder, so cosine = dot product, no magnitude division needed).
  4. Returns the top-K chunks sorted by descending similarity, filtered by
     `min_similarity`.

Scalability ceiling
--------------------
Loading all embeddings for the requested sources into Python memory:
  50,000 chunks × 128 floats (MockEmbedder) × 8 bytes ≈ 51 MB   ← safe
  50,000 chunks × 768 floats (Gemini)        × 8 bytes ≈ 307 MB  ← watch
  50,000 chunks × 1536 floats (OpenAI)       × 8 bytes ≈ 614 MB  ← limit

For a personal assistant used by one person with a few hundred documents,
this is entirely fine.  The ceiling is documented and visible; the
PgvectorEmbeddingStore (future) makes it irrelevant at scale.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models.content_chunk import ContentChunk

logger = logging.getLogger(__name__)


class EmbeddingStore(ABC):
    """Abstract interface for storing and retrieving chunk embeddings."""

    @abstractmethod
    async def upsert(
        self,
        chunk: ContentChunk,
        embedding: list[float],
        *,
        model_name: str,
    ) -> None:
        """Store `embedding` on `chunk`, updating embedding_json and embedding_model.

        Idempotent: calling it again with a new embedding overwrites the old one.
        This supports re-indexing when the embedding model changes.
        """
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        *,
        source_ids: list[int],
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> list[tuple[ContentChunk, float]]:
        """Return the top-K chunks most similar to `query_embedding`.

        Args:
            query_embedding: The embedded query vector (unit-normalised).
            source_ids:      Restrict search to chunks from these sources.
                             Passing an empty list returns no results.
            top_k:           Maximum number of results to return.
            min_similarity:  Discard results below this cosine similarity
                             threshold.  Range: [0.0, 1.0].

        Returns:
            List of (ContentChunk, similarity_score) pairs, best first.
            May be shorter than top_k if fewer qualifying chunks exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_by_source(self, source_id: int) -> int:
        """Delete all embeddings for `source_id`.  Returns the count deleted."""
        raise NotImplementedError


class SQLiteEmbeddingStore(EmbeddingStore):
    """EmbeddingStore backed by SQLite + in-Python cosine similarity.

    Stores embeddings as JSON text in ContentChunk.embedding_json.
    Computes similarity by loading all candidate embeddings into Python
    and ranking with a dot product (valid because vectors are unit-normalised).

    This implementation is deliberately simple — its only dependency is
    the existing SQLAlchemy session (no new packages required).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        chunk: ContentChunk,
        embedding: list[float],
        *,
        model_name: str,
    ) -> None:
        """Serialise `embedding` and persist it on the chunk row."""
        chunk.embedding_json = json.dumps(embedding)
        chunk.embedding_model = model_name
        await self._session.flush()

    async def search(
        self,
        query_embedding: list[float],
        *,
        source_ids: list[int],
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> list[tuple[ContentChunk, float]]:
        """Load candidate chunks and rank by cosine similarity.

        Only chunks that have an embedding (embedding_json IS NOT NULL)
        and belong to one of `source_ids` are considered.
        """
        if not source_ids:
            return []

        result = await self._session.execute(
            select(ContentChunk)
            .where(ContentChunk.source_id.in_(source_ids))
            .where(ContentChunk.embedding_json.is_not(None))
        )
        chunks = result.scalars().all()

        if not chunks:
            return []

        # Score every chunk
        scored: list[tuple[ContentChunk, float]] = []
        for chunk in chunks:
            try:
                vec = json.loads(chunk.embedding_json)  # type: ignore[arg-type]
                sim = _dot_product(query_embedding, vec)
                if sim >= min_similarity:
                    scored.append((chunk, sim))
            except (json.JSONDecodeError, TypeError, ValueError):
                logger.warning(
                    "SQLiteEmbeddingStore: malformed embedding on chunk_id=%s — skipping",
                    chunk.id,
                )

        # Sort descending by similarity, return top-K
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:top_k]

    async def delete_by_source(self, source_id: int) -> int:
        """Clear embedding_json for all chunks belonging to `source_id`.

        We set embedding_json to NULL rather than deleting the rows, because
        ContentChunkRepository.delete_by_source() handles full row deletion
        when a ContentSource is deleted.  This method is for re-indexing:
        clearing old embeddings before writing new ones.
        """
        result = await self._session.execute(
            select(ContentChunk).where(ContentChunk.source_id == source_id)
        )
        chunks = result.scalars().all()
        count = 0
        for chunk in chunks:
            chunk.embedding_json = None
            chunk.embedding_model = None
            count += 1
        if count:
            await self._session.flush()
        return count


def _dot_product(a: list[float], b: list[float]) -> float:
    """Compute the dot product of two equal-length float vectors.

    When both vectors are L2-normalised (magnitude = 1.0), the dot product
    equals the cosine similarity.  This is guaranteed by the Embedder
    contract (`embed()` always returns unit-normalised vectors).

    Returns 0.0 when the vectors have different lengths rather than raising,
    to keep the search method resilient against mixed-model chunk collections.
    """
    if len(a) != len(b):
        logger.warning(
            "_dot_product: dimension mismatch %d vs %d — returning 0.0", len(a), len(b)
        )
        return 0.0
    return sum(x * y for x, y in zip(a, b))
