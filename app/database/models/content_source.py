"""The `content_sources` table: a user-supplied document, text block, or file
that MemoraBot has ingested and can reason over.

Design rationale
----------------
NotebookLM's core primitive is the *source*: something a user provides
that the system processes, indexes, and can then answer questions about.
Every platform feature that operates on user-supplied content (RAG Q&A,
quiz generation from a document, OCR, summarisation, flashcard generation,
presentation outlines) shares the same ingestion pipeline:

    user uploads / pastes → ContentSource row created
                          → ContentProcessor extracts text
                          → (Step 6) TextChunker splits text
                          → (Step 6) Embedder embeds chunks
                          → ContentChunk rows ready for semantic search

Having a single `content_sources` table as the anchor means:
  - Adding OCR = adding an ImageOCRProcessor (zero schema changes).
  - Adding YouTube transcripts = adding a VideoTranscriptProcessor (zero schema changes).
  - Adding RAG Q&A = querying content_chunks that reference content_sources
    (zero schema changes).

Status machine
--------------
  "pending"    — created, not yet processed (only for file-based sources)
  "processing" — a processor is running (for long-running jobs)
  "ready"      — text extracted, optionally chunked & indexed (Step 6)
  "failed"     — processing failed; error_message has details

Plain text sources skip "pending" / "processing" and go directly to "ready"
because there is nothing to extract — the text is already provided at
creation time.

File storage
------------
`raw_storage_key` is currently a relative path under `app/temp/`
(e.g. `temp/<uuid>_filename.pdf`).  When the platform moves to
object storage (S3, GCS), this column is reinterpreted as a bucket key —
no schema migration needed.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.content_chunk import ContentChunk  # Step 6
    from app.database.models.user import User


class ContentSourceType(str, Enum):
    """The origin format of a content source.

    Using a str-Enum keeps the stored value human-readable and allows
    new types to be added without a migration (stored as String(32)).
    """

    TEXT = "text"                         # plain text pasted by the user
    PDF = "pdf"                           # uploaded PDF file
    IMAGE = "image"                       # uploaded image (OCR)
    AUDIO = "audio"                       # uploaded audio (transcription)
    VIDEO_TRANSCRIPT = "video_transcript" # YouTube / video transcript
    URL = "url"                           # web URL to scrape


class ContentSourceStatus(str, Enum):
    """Processing lifecycle status of a content source."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ContentSource(Base):
    """One user-supplied document or text block, ready to be processed and indexed.

    A `ContentSource` row is created the moment the user provides input.
    It is updated in-place as the processing pipeline runs.  All derived
    data (chunks, embeddings, generated artifacts) reference this row as
    their anchor.
    """

    __tablename__ = "content_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership ──────────────────────────────────────────────────────── #
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── What the user provided ─────────────────────────────────────────── #
    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        # ContentSourceType value; stored as plain string so new types need
        # no migration.
    )
    original_filename: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        # For file uploads: original name as provided by the user.
        # None for TEXT and URL sources.
    )
    raw_storage_key: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        # Relative path under app/temp/ for now; future: S3/GCS object key.
        # None for TEXT sources (text is stored in extracted_text directly).
    )

    # ── What the system extracted ──────────────────────────────────────── #
    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        # Populated by ContentProcessor.extract_text().
        # For TEXT sources: same as the user's input (set at creation time).
        # For file sources: extracted by the processor during processing.
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        # Updated by ContentService.index_source() in Step 6.
        # 0 until chunking is complete.
    )

    # ── Processing state ───────────────────────────────────────────────── #
    status: Mapped[str] = mapped_column(
        String(32),
        default=ContentSourceStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        # Populated when status="failed".
    )

    # ── Display ────────────────────────────────────────────────────────── #
    title: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        # User-provided or auto-extracted (e.g. PDF title, URL page title).
        # Used in the "My Sources" list view.
    )

    # ── Timestamps ────────────────────────────────────────────────────── #
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        # Set when status transitions to "ready" or "failed".
    )

    # ── Relationships ──────────────────────────────────────────────────── #
    user: Mapped["User"] = relationship("User", back_populates="content_sources")
    chunks: Mapped[list["ContentChunk"]] = relationship(  # Step 6
        "ContentChunk", back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ContentSource id={self.id} user_id={self.user_id} "
            f"type={self.source_type!r} status={self.status!r} "
            f"title={self.title!r}>"
        )
