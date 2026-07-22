"""The `referrals` table: one row per successful referral relationship.

Invariants enforced at the DB level:
- `referred_id` is UNIQUE → a user can only ever have ONE referrer.
- `referrer_id != referred_id` is enforced in the service layer (self-referral guard).
- The row is written atomically with the coin award so a crash cannot
  produce orphaned rewards (see ReferralService.process_referral).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.user import User


class Referral(Base):
    """A successful referral: who invited whom, which code was used, and the reward."""

    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # UNIQUE: one user can only be referred once, by exactly one referrer.
    referred_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    referral_code: Mapped[str] = mapped_column(String(32), nullable=False)
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reward_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    referrer: Mapped["User"] = relationship(
        foreign_keys=[referrer_id],
        lazy="selectin",
    )
    referred: Mapped["User"] = relationship(
        foreign_keys=[referred_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Referral referrer={self.referrer_id} referred={self.referred_id}"
            f" reward={self.reward_amount} rewarded={self.rewarded}>"
        )
