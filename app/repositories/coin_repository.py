"""Data-access layer for coin wallets and coin transactions.

All writes go through `CoinService`; this repository only exposes the raw
DB primitives.  No business logic lives here.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.models.coin_transaction import CoinTransaction
from app.database.models.coin_wallet import CoinWallet
from app.database.models.user import User


class CoinRepository:
    """Async repository for `coin_wallets` and `coin_transactions`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Wallet ─────────────────────────────────────────────────────────────

    async def get_wallet_by_user_id(self, user_id: int) -> CoinWallet | None:
        result = await self._session.execute(
            select(CoinWallet).where(CoinWallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_wallet_by_referral_code(self, code: str) -> CoinWallet | None:
        result = await self._session.execute(
            select(CoinWallet).where(CoinWallet.referral_code == code)
        )
        return result.scalar_one_or_none()

    async def create_wallet(self, *, user_id: int, referral_code: str) -> CoinWallet:
        wallet = CoinWallet(user_id=user_id, referral_code=referral_code)
        self._session.add(wallet)
        await self._session.flush()
        await self._session.refresh(wallet)
        return wallet

    async def update_wallet_balance(
        self,
        wallet_id: int,
        *,
        new_balance: int,
        earned_delta: int = 0,
        spent_delta: int = 0,
    ) -> None:
        """Atomically set the new balance and update lifetime counters."""
        wallet = await self._session.get(CoinWallet, wallet_id)
        if wallet is None:
            return
        wallet.coin_balance = new_balance
        if earned_delta > 0:
            wallet.lifetime_earned += earned_delta
        if spent_delta > 0:
            wallet.lifetime_spent += spent_delta
        await self._session.flush()

    # ── Transactions ───────────────────────────────────────────────────────

    async def create_transaction(
        self,
        *,
        wallet_id: int,
        amount: int,
        tx_type: str,
        description: str,
        ref_telegram_id: int | None = None,
    ) -> CoinTransaction:
        tx = CoinTransaction(
            wallet_id=wallet_id,
            amount=amount,
            tx_type=tx_type,
            description=description,
            ref_telegram_id=ref_telegram_id,
        )
        self._session.add(tx)
        await self._session.flush()
        await self._session.refresh(tx)
        return tx

    async def get_transactions(
        self, wallet_id: int, *, limit: int = 20
    ) -> Sequence[CoinTransaction]:
        result = await self._session.execute(
            select(CoinTransaction)
            .where(CoinTransaction.wallet_id == wallet_id)
            .order_by(CoinTransaction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # ── Leaderboard ────────────────────────────────────────────────────────

    async def get_top_wallets_by_balance(
        self, *, limit: int = 10
    ) -> Sequence[tuple[CoinWallet, User]]:
        """Return (wallet, user) pairs ordered by coin_balance desc."""
        result = await self._session.execute(
            select(CoinWallet, User)
            .join(User, User.id == CoinWallet.user_id)
            .order_by(CoinWallet.coin_balance.desc())
            .limit(limit)
        )
        return result.all()

    # ── Aggregate stats ────────────────────────────────────────────────────

    async def total_coins_in_circulation(self) -> int:
        result = await self._session.execute(
            select(func.sum(CoinWallet.coin_balance))
        )
        return result.scalar_one() or 0

    async def total_coins_ever_earned(self) -> int:
        result = await self._session.execute(
            select(func.sum(CoinWallet.lifetime_earned))
        )
        return result.scalar_one() or 0
