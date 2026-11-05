"""The `user_grammar_progress` table: tracks per-user grammar topic study history.

Design rationale
----------------
This table is the source of truth for "what grammar has this user actually
studied?".  A topic row is created here only when the user OPENS a lesson —
not when they browse the topic list.  This distinction is critical because
the upcoming General Quiz → Grammar Auto mode will ask exactly this question.

Status lifecycle
----------------
  NOT_STARTED  → created when the user opens a lesson for the first time
                 (set to IN_PROGRESS immediately; NOT_STARTED is never persisted)
  IN_PROGRESS  → the lesson was opened but mastery < MASTERY_COMPLETED_THRESHOLD
  COMPLETED    → mastery_score >= MASTERY_COMPLETED_THRESHOLD (set by GrammarService)

Mastery score
-------------
A float in [0.0, 1.0] computed deterministically by GrammarService from
accuracy + recency + attempt count.  Never set by AI — always calculated
from the counters in this row.  See GrammarService.calculate_mastery() for
the algorithm.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.grammar_topic import GrammarTopic
    from app.database.models.user import User


class GrammarProgressStatus(str, Enum):
    """Lifecycle status for a user's study of one grammar topic."""

    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"


class UserGrammarProgress(Base):
    """Progress record for one user studying one grammar topic.

    Created on first lesson open.  Never deleted (soft lifecycle via status).
    All numeric counters are updated in-place — this is mutable state, unlike
    the append-only learning_activities log.
    """

    __tablename__ = "user_grammar_progress"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "grammar_topic_id",
            name="uq_user_grammar_progress_user_topic",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership ──────────────────────────────────────────────────────── #
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grammar_topic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("grammar_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Status ─────────────────────────────────────────────────────────── #
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=GrammarProgressStatus.IN_PROGRESS.value,
        index=True,
    )

    # ── Activity counters ──────────────────────────────────────────────── #
    lessons_opened: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        # Incremented each time the user opens/re-opens this lesson.
    )
    questions_answered: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    questions_correct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    questions_wrong: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ── Mastery tracking ───────────────────────────────────────────────── #
    last_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        # Accuracy of the most recent quiz session: correct / total.
        # None = no quiz attempted yet.
    )
    mastery_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        # Composite mastery in [0.0, 1.0], calculated by GrammarService.
        # Updated after every quiz completion.
    )

    # ── Timestamps ─────────────────────────────────────────────────────── #
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        # Set when the progress row is first created (lesson first opened).
    )
    last_studied_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        # Updated every time the user opens the lesson or completes a quiz.
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────── #
    user: Mapped["User"] = relationship("User")
    topic: Mapped["GrammarTopic"] = relationship(
        "GrammarTopic",
        back_populates="user_progress",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<UserGrammarProgress id={self.id} user_id={self.user_id} "
            f"topic_id={self.grammar_topic_id} status={self.status!r} "
            f"mastery={self.mastery_score:.2f}>"
        )
