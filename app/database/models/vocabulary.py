"""Personal vocabulary library entry (V1.6 — My Vocabulary).

Each row represents ONE user's personal copy of a word they have looked up.
It is deliberately separate from `mnemonic_history`, which is a shared,
cross-user AI cache.  Keeping them separate means:

  • A user can delete, favorite, or later review their entry without
    touching the shared library.
  • The shared library can be updated, deactivated, or re-rated without
    silently changing what a user is trying to memorise.

Versioning design
-----------------
The table tracks three mnemonic pointers:

    active_mnemonic_id    — what the user is learning right now (always set)
    pending_mnemonic_id   — a system-generated improvement waiting for the
                            user's approval (NULL = nothing pending)
    archived_mnemonic_id  — the previous active mnemonic that the user just
                            replaced (NULL = no prior version, or TTL expired)

The distinction between "system improvement" and "user regeneration" is made
by comparing prompt_version integers (see VocabularyService._is_system_improvement).
Manual regenerations share the same prompt_version and never set pending_mnemonic_id.

State machine (four valid states):
  ┌────────────────┬─────────────────┬──────────────────────────────────────┐
  │ pending IS NULL│ archived IS NULL │ Meaning                              │
  ├────────────────┼─────────────────┼──────────────────────────────────────┤
  │ True           │ True            │ Normal — no update, no history        │
  │ False          │ True            │ Update available, user hasn't decided │
  │ True           │ False           │ User accepted last update, archived   │
  │ False          │ False           │ IMPOSSIBLE — enforced at service layer│
  └────────────────┴─────────────────┴──────────────────────────────────────┘

Extension points for future versions (no behavioral impact today)
-----------------------------------------------------------------
    review_due_at   → Spaced Repetition scheduler (V1.7)
    review_count    → Learning statistics (V2.0)
    next_interval   → SM-2 algorithm (V1.7)

Add these columns in migration 0007; no structural redesign needed.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.mnemonic_history import MnemonicHistory
    from app.database.models.user import User


class VocabularyEntry(Base):
    """One user's personal copy of a word they have looked up.

    See module docstring for the full versioning and state-machine design.
    """

    __tablename__ = "vocabulary_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "word", name="uq_vocabulary_user_word"),
        # Future indexes for Spaced Repetition queries go here — add to 0007.
    )

    # ── Primary key ────────────────────────────────────────────────────── #
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Owner ──────────────────────────────────────────────────────────── #
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Mnemonic version pointers ──────────────────────────────────────── #
    active_mnemonic_id: Mapped[int] = mapped_column(
        ForeignKey("mnemonic_history.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalized from active_mnemonic.prompt_version for O(1) comparison.
    # Updated whenever active_mnemonic_id changes.
    active_prompt_version: Mapped[str] = mapped_column(
        String(16), nullable=False, default="v1"
    )

    # Set when a newer prompt_version mnemonic exists for this word.
    # NULL  → no system update available.
    # SET   → a better version is waiting; display ✨ indicator.
    pending_mnemonic_id: Mapped[int | None] = mapped_column(
        ForeignKey("mnemonic_history.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # Set when the user accepted a pending update (previous active version).
    # Retained for `retention_days` (default 30) to allow future rollback UI.
    # NULL  → no archived version (first entry, or TTL expired).
    archived_mnemonic_id: Mapped[int | None] = mapped_column(
        ForeignKey("mnemonic_history.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    # archive_expires_at = archived_at + configured retention; used by future
    # cleanup job.  NOT implemented today — only the data is preserved.
    archive_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)

    # ── Denormalized content ───────────────────────────────────────────── #
    # Copied from active_mnemonic at creation/update time.
    # Survives library changes (mnemonic deactivation, re-rating) intact.
    word: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)
    uzbek_pronunciation: Mapped[str] = mapped_column(Text, nullable=False)
    mnemonic_story: Mapped[str] = mapped_column(Text, nullable=False)
    example_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False)

    # ── Personal state ─────────────────────────────────────────────────── #
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────── #
    user: Mapped["User"] = relationship(back_populates="vocabulary_entries")
    active_mnemonic: Mapped["MnemonicHistory"] = relationship(
        foreign_keys=[active_mnemonic_id]
    )
    pending_mnemonic: Mapped["MnemonicHistory | None"] = relationship(
        foreign_keys=[pending_mnemonic_id]
    )
    archived_mnemonic: Mapped["MnemonicHistory | None"] = relationship(
        foreign_keys=[archived_mnemonic_id]
    )

    # ── Extension point ────────────────────────────────────────────────── #
    # V1.7 Spaced Repetition: add columns review_due_at, review_count,
    # next_interval in migration 0007.  VocabularyService.save_from_mnemonic
    # has a marked extension point where SM-2 scheduling hooks in.

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<VocabularyEntry id={self.id} user_id={self.user_id} "
            f"word={self.word!r} favorite={self.is_favorite} "
            f"pending={'yes' if self.pending_mnemonic_id else 'no'}>"
        )
