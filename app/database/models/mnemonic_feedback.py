"""The `mnemonic_feedback` table: one user's 👍/👎 rating on one specific
generated mnemonic version (Task 5). Feeds the future Statistics feature.

Deliberately has no ORM `relationship()` back to `User` or `MnemonicHistory`
— those two models stay completely untouched by this addition. All access
goes through `MnemonicFeedbackRepository`'s explicit queries instead, which
is enough for what this feature needs and keeps the change fully additive.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MnemonicFeedback(Base):
    """One user's helpful/not-helpful rating for one `mnemonic_history` row.

    A user can rate a given mnemonic at most once: re-tapping 👍/👎 updates
    their existing rating instead of adding a duplicate, enforced here by a
    unique constraint on (mnemonic_history_id, user_id) and implemented in
    `MnemonicFeedbackRepository.upsert`.
    """

    __tablename__ = "mnemonic_feedback"
    __table_args__ = (
        UniqueConstraint("mnemonic_history_id", "user_id", name="uq_feedback_mnemonic_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mnemonic_history_id: Mapped[int] = mapped_column(
        ForeignKey("mnemonic_history.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return (
            f"<MnemonicFeedback mnemonic_history_id={self.mnemonic_history_id} "
            f"user_id={self.user_id} is_helpful={self.is_helpful}>"
        )
