"""The `content_chunks` table: the atomic retrieval unit for RAG and semantic search.

Design rationale
----------------
A raw document (50 pages, 30,000 words) cannot be sent as-is to an AI
model — it exceeds context windows and produces diffuse, low-quality answers.
The solution is chunking + embedding:

  1. TextChunker splits the extracted text into overlapping windows of
     ~512 tokens each, respecting sentence boundaries where possible.
  2. Embedder encodes each chunk as a high-dimensional float vector that
     captures semantic meaning.
  3. At query time, the query is embedded with the same model, and
     cosine similarity is computed against all chunk embeddings to find
     the K most relevant passages.
  4. Those K passages are inserted into the AI prompt as context, giving
     the model grounded, specific information to answer from.

Each ContentChunk row stores:
  - The raw text (for insertion into AI prompts at retrieval time).
  - Its position within the source (for citation: "Page 12, section 3").
  - Its embedding as a JSON-encoded float list (SQLite-compatible storage;
    upgrade path is PostgreSQL + pgvector, hidden behind EmbeddingStore).

One ContentSource → many ContentChunks (cascade delete).

Scalability ceiling (SQLiteEmbeddingStore)
------------------------------------------
The SQLite backend loads all chunk embeddings for the requested source_ids
into Python for cosine similarity ranking.  This is O(N × D) in memory
where N = chunk count and D = embedding dimension (typically 768–1536).

Ceiling estimate:
  50,000 chunks × 1536 floats × 4 bytes ≈ 300 MB

For a personal learning assistant with hundreds of documents and thousands
of chunks this is entirely safe.  The EmbeddingStore abstraction (Step 6)
hides the backend — when the platform scales beyond this, replacing
SQLiteEmbeddingStore with a PgvectorEmbeddingStore requires zero changes
to ContentService, RAGService, or any handler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.content_source import ContentSource


class ContentChunk(Base):
    """One text segment of a `ContentSource`, with its embedding vector.

    Chunks are created in bulk by `ContentService.index_source()` and
    never modified after creation.  Deleting the parent `ContentSource`
    cascades to all its chunks.
    """

    __tablename__ = "content_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Source reference ───────────────────────────────────────────────── #
    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("content_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Position within source ─────────────────────────────────────────── #
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        # 0-based position in the source.  Used to reassemble context
        # windows and to display adjacent chunks for better coherence.
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        # Approximate token count (word-count approximation in Step 6;
        # real tokenizer can be plugged in without schema changes).
    )

    # ── Citation metadata ──────────────────────────────────────────────── #
    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        # For PDF sources: the 1-based page number this chunk starts on.
        # None for TEXT, URL, and other non-paginated sources.
    )
    section_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        # For structured documents: the heading under which this chunk falls.
        # Populated by processors that can detect headings (PDF, URL).
    )

    # ── Content ────────────────────────────────────────────────────────── #
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        # The actual text of this chunk.  Inserted verbatim into AI prompts
        # at retrieval time, so it must be clean human-readable prose.
    )

    # ── Embedding ─────────────────────────────────────────────────────── #
    embedding_model: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        # The model name used to produce this embedding, e.g. "mock",
        # "text-embedding-004", "nomic-embed-text".  Stored so that
        # mixed-model collections can be detected and re-indexed.
    )
    embedding_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        # JSON-encoded list[float].  None if the chunk has not yet been
        # embedded (index_source may chunk before embedding in two passes).
        # Example: "[0.12, -0.34, 0.87, ...]"
    )

    # ── Relationships ──────────────────────────────────────────────────── #
    source: Mapped["ContentSource"] = relationship(
        "ContentSource",
        back_populates="chunks",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ContentChunk id={self.id} source_id={self.source_id} "
            f"index={self.chunk_index} tokens={self.token_count} "
            f"embedded={'yes' if self.embedding_json else 'no'}>"
        )
