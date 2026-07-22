"""The `coin_wallets` table: one row per user — holds coin balance and referral code.

Keeps coin economy concerns cleanly separated from the core `users` table.
The `referral_code` column doubles as the user's unique invite code so we
need only one table lookup to resolve an incoming deep-link payload.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.coin_transaction import CoinTransaction


class CoinWallet(Base):
    """A user's coin wallet: balance, lifetime counters, and referral code."""

    __tablename__ = "coin_wallets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # 8-char alphanumeric invite code; also the deep-link payload.
    referral_code: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    coin_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    transactions: Mapped[list["CoinTransaction"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<CoinWallet user_id={self.user_id} balance={self.coin_balance}"
            f" code={self.referral_code!r}>"
        )
