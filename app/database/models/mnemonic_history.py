"""The `mnemonic_history` table: every mnemonic version ever generated.

This is both the user's permanent learning history AND (as of V1.2) a
self-improving library: each row accumulates usage/feedback statistics so
the system can serve the best-performing version of a word instead of just
the most recent one, and can retire poor versions without ever losing them.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.user import User


class MnemonicHistory(Base):
    """A single generated mnemonic version, permanently attached to the user
    who originally triggered its generation, plus the library statistics
    that decide whether it keeps getting served.

    `difficulty` is stored as a plain string (rather than a native/CHECK-constrained
    SQL enum) on purpose: it keeps future Alembic migrations simple if the set of
    difficulty levels ever changes (as happened once already — see migration 0003,
    which moved this table from easy/medium/hard to the CEFR scale). Validity is
    instead enforced at the API boundary by `app.core.enums.DifficultyLevel` via
    the AI provider's Pydantic schema.

    Statistics fields (added in migration 0003 — see docs/MNEMONIC_LIBRARY.md):
        uses: how many times this exact version has been served to any user
            (cache hits and the moment it's freshly generated both count).
        last_used_at: when it was last served; None until first served.
        likes / dislikes: denormalized counts kept in sync with
            `mnemonic_feedback` by `MnemonicFeedbackService`, so the
            "highest-rated" query never needs a JOIN.
        average_rating: (likes - dislikes) / max(1, likes + dislikes), in
            [-1.0, 1.0]. 0.0 for "no feedback yet" and for "evenly split" are
            deliberately the same value — both mean "no strong signal".
        regenerated_count: how many times a learner looked at THIS version
            and tapped "🔄 Generate Another Mnemonic" instead of keeping it —
            an implicit negative signal distinct from an explicit 👎.
        is_active: soft-delete flag. Consistently poor versions are
            deactivated (see `MnemonicService`/`MnemonicFeedbackService`),
            never deleted — historical data is always preserved.
        response_time_ms: how long the *original* AI generation call took.
        prompt_version: which `app/knowledge/<version>/` produced this,
            enabling future "prompt version performance" analytics.
    """

    __tablename__ = "mnemonic_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)
    uzbek_pronunciation: Mapped[str] = mapped_column(Text, nullable=False)
    mnemonic_story: Mapped[str] = mapped_column(Text, nullable=False)
    example_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False)
    ai_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # --- Self-improving library statistics (migration 0003) ----------------
    uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dislikes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    regenerated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(16), default="v1", nullable=False)

    user: Mapped["User"] = relationship(back_populates="mnemonic_history")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return (
            f"<MnemonicHistory id={self.id} word={self.word!r} user_id={self.user_id} "
            f"is_active={self.is_active} average_rating={self.average_rating}>"
        )
