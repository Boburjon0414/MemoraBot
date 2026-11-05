"""The `learning_activities` table: an immutable, append-only event log
of every action a user takes that represents learning.

Design rationale
----------------
A single, typed event log is the correct foundation for all derivative
read-side features — streaks, statistics, achievements, weekly reports,
and adaptive difficulty — because every one of those features reduces to
the same question: "what did this user do, and when?"

Without this table, each feature would scatter its own counters into its
own column (or table), and joining them later becomes an archaeology project.
With it, any new feature's "how many times did X happen" question is a
single GROUP BY on an indexed column.

Immutability guarantee
----------------------
Rows are NEVER updated or deleted after insertion (except via CASCADE
when the parent user is deleted).  The `outcome` and `score` fields
capture everything needed at event time; there is no "update the result"
operation.  This makes the table safe as a source of truth for audit,
statistics, and streak calculations.

Forward-compatibility
---------------------
`content_source_id` is nullable and references a table (`content_sources`)
that does not yet exist.  SQLite does not enforce FK validity on nullable
columns, so this migration runs cleanly today.  The column will be wired
to a real FK constraint when `content_sources` is created in Step 5.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.mnemonic_history import MnemonicHistory
    from app.database.models.user import User
    from app.database.models.vocabulary import VocabularyEntry


class ActivityType(str, Enum):
    """Every event type that counts as a learning activity."""

    MNEMONIC_GENERATED = "mnemonic_generated"
    MNEMONIC_REVIEWED = "mnemonic_reviewed"
    VOCABULARY_SAVED = "vocabulary_saved"
    QUIZ_ANSWERED = "quiz_answered"
    QUIZ_STARTED = "quiz_started"         # Feature C
    QUESTION_SENT = "question_sent"       # Feature C
    QUESTION_CORRECT = "question_correct" # Feature C
    QUESTION_WRONG = "question_wrong"     # Feature C
    QUIZ_COMPLETED = "quiz_completed"     # Feature C
    FLASHCARD_REVIEWED = "flashcard_reviewed"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_QA = "document_qa"
    AI_CHAT_MESSAGE = "ai_chat_message"
    VOICE_CHAT_TURN = "voice_chat_turn"
    PRESENTATION_GENERATED = "presentation_generated"
    # Grammar Learning (Feature: Learn → Grammar)
    GRAMMAR_LESSON_OPENED    = "grammar_lesson_opened"
    GRAMMAR_QUESTION_CORRECT = "grammar_question_correct"
    GRAMMAR_QUESTION_WRONG   = "grammar_question_wrong"
    GRAMMAR_QUIZ_COMPLETED   = "grammar_quiz_completed"


class LearningActivity(Base):
    """One learning event for one user, captured at the moment it occurs.

    All foreign keys to entity tables (mnemonic_id, vocabulary_entry_id,
    content_source_id) are nullable because:
      - Not every activity type has an associated entity (e.g. an AI chat
        message doesn't have a mnemonic_id).
      - The referenced entity may be soft-deleted later, but the event
        record should never disappear.

    `outcome` captures binary or categorical results:
      "correct" | "wrong" | "skipped" | "saved" | "deleted" | …
    `score` captures continuous results, normalised to [0.0, 1.0]:
      quiz accuracy, flashcard confidence rating, …
    `metadata_json` is a JSON-encoded dict for anything that doesn't
    deserve a dedicated column (e.g. {"word": "ephemeral", "duration_ms": 1200}).
    """

    __tablename__ = "learning_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Who did it ─────────────────────────────────────────────────────── #
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── What they did ──────────────────────────────────────────────────── #
    activity_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # ── Optional entity references ─────────────────────────────────────── #
    mnemonic_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("mnemonic_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vocabulary_entry_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("vocabulary_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    # content_source_id will reference content_sources (Step 5).
    # Stored as a plain Integer for now; the FK constraint is added
    # in migration 0007 when that table is created.
    content_source_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ── Result data ────────────────────────────────────────────────────── #
    outcome: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        # e.g. "correct" | "wrong" | "skipped" | "saved"
    )
    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        # 0.0–1.0 normalised; None when not applicable
    )

    # Arbitrary extra context as a JSON-encoded dict.
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── When it happened ───────────────────────────────────────────────── #
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # ── Relationships (for ORM convenience; never eagerly loaded) ──────── #
    user: Mapped["User"] = relationship("User", back_populates="learning_activities")
    mnemonic: Mapped["MnemonicHistory | None"] = relationship(
        "MnemonicHistory",
        foreign_keys=[mnemonic_id],
    )
    vocabulary_entry: Mapped["VocabularyEntry | None"] = relationship(
        "VocabularyEntry",
        foreign_keys=[vocabulary_entry_id],
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<LearningActivity id={self.id} user_id={self.user_id} "
            f"type={self.activity_type!r} at={self.occurred_at}>"
        )
