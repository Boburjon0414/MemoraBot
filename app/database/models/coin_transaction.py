"""The `coin_transactions` table: immutable ledger of every coin movement.

All credit (+) and debit (-) operations produce a row here.  `CoinService`
is the single writer — nothing else touches balances directly.

`tx_type` values (open set — new features may add more):
  referral       — referrer earned coins for a successful invite
  welcome_bonus  — new user received a sign-up bonus via referral
  admin_add      — admin manually credited coins
  admin_remove   — admin manually debited coins
  admin_reset    — admin zeroed the balance
  bonus          — admin one-off bonus grant
  premium_redeem — user spent coins to activate premium (future)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.coin_wallet import CoinWallet


class CoinTransaction(Base):
    """One ledger entry: positive = earned, negative = spent."""

    __tablename__ = "coin_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("coin_wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Positive = earned, negative = spent.  Storing the sign directly makes
    # SUM(amount) == current balance, and simple WHERE filters find earns vs spends.
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    tx_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional: Telegram user_id of the related user (e.g. who was referred).
    ref_telegram_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    wallet: Mapped["CoinWallet"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<CoinTransaction id={self.id} wallet_id={self.wallet_id}"
            f" amount={self.amount:+d} type={self.tx_type!r}>"
        )
