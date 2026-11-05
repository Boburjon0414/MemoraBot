"""The `feature_outputs` table: generic storage for AI-generated artifacts.

Design rationale
----------------
Every AI feature that produces a storable result — quizzes, flashcard sets,
summaries, Q&A sessions, chat sessions, presentation outlines — shares the
same storage lifecycle:

  1. AI generates the artifact from a prompt.
  2. The artifact is persisted so the user can revisit it.
  3. The user can archive it when done.

Rather than one table per feature, `feature_outputs` provides a single
generic table.  The `output_type` column identifies the artifact type; the
`payload_json` column stores the validated, type-specific payload
(validated against the corresponding Pydantic schema in schemas.py).

Consequences
------------
  Adding Flashcards: define `FlashcardPayload` + `OutputType.FLASHCARD_SET`.
    → Zero new tables.
    → Zero new repositories.
    → Zero new migrations (except for the OutputType enum, which is stored
      as a plain String, so new values need no migration).

  "Show me all my quizzes":
    SELECT * FROM feature_outputs
    WHERE user_id = ? AND output_type = 'quiz' AND is_archived = FALSE

  "Archive this quiz":
    UPDATE feature_outputs SET is_archived = TRUE WHERE id = ?

`payload_json` vs dedicated columns
------------------------------------
Dedicated columns would be faster to query on individual fields but would
require a new column (and migration) for every new artifact field.  Since
we never need to filter on payload fields (only on user_id, output_type,
and is_archived), JSON storage is the correct trade-off here.

The Pydantic payload schemas enforce correctness at the service layer;
no raw JSON ever escapes FeatureOutputService.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.content_source import ContentSource
    from app.database.models.user import User


class OutputType(str, Enum):
    """The type of AI-generated artifact stored in a FeatureOutput row.

    Stored as a plain String(64) — new values need no migration.
    """

    QUIZ = "quiz"
    FLASHCARD_SET = "flashcard_set"
    SUMMARY = "summary"
    QA_SESSION = "qa_session"
    CHAT_SESSION = "chat_session"
    PRESENTATION_OUTLINE = "presentation_outline"


class FeatureOutput(Base):
    """One AI-generated learning artifact owned by one user.

    Every artifact produced by QuizService, FlashcardService, SummaryService,
    AIChatService, RAGService, or PresentationService is stored here.

    Lifecycle:
      is_archived=False → visible in the user's library.
      is_archived=True  → soft-deleted; hidden from normal list views but
                          kept for analytics and potential recovery.
    """

    __tablename__ = "feature_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership ──────────────────────────────────────────────────────── #
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── What kind of artifact this is ─────────────────────────────────── #
    output_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        # OutputType value; stored as plain String so new types need no migration.
    )

    # ── Optional link to the source document ──────────────────────────── #
    content_source_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("content_sources.id", ondelete="SET NULL"),
        nullable=True,
        # Set when the artifact was generated from a ContentSource (RAG Q&A,
        # quiz from document, summary, presentation).  None for artifacts
        # generated from vocabulary or free-form AI chat.
    )

    # ── Display ────────────────────────────────────────────────────────── #
    title: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        # Human-readable label shown in the user's library.
        # Auto-generated from payload content if not explicitly provided.
    )

    # ── The artifact itself ────────────────────────────────────────────── #
    payload_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        # JSON-serialised Pydantic payload model.
        # Validated on write by FeatureOutputService.save().
        # Validated on read by FeatureOutputService.load(schema=...).
    )

    # ── Lifecycle ──────────────────────────────────────────────────────── #
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        # Updated by FeatureOutputService when payload_json changes
        # (e.g. new Q&A turns appended to a QASessionPayload).
    )

    # ── Relationships ──────────────────────────────────────────────────── #
    user: Mapped["User"] = relationship("User", back_populates="feature_outputs")
    source: Mapped["ContentSource | None"] = relationship(
        "ContentSource",
        foreign_keys=[content_source_id],
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FeatureOutput id={self.id} user_id={self.user_id} "
            f"type={self.output_type!r} archived={self.is_archived} "
            f"title={self.title!r}>"
        )
