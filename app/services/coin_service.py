"""CoinService: the single authority for all coin balance modifications.

RULE: Nothing outside this service ever writes to `coin_wallets.coin_balance`
or inserts into `coin_transactions`.  Every earn and spend flows through here
so the ledger is always consistent and auditable.

Design:
- Wallets are created lazily on first access (`get_or_create_wallet`).
- Referral codes are generated here and stored in the wallet row.
- All balance changes are atomic: transaction row + wallet update in one flush.
"""

from __future__ import annotations

import logging
import secrets
import string
from typing import Sequence

from app.database.models.coin_transaction import CoinTransaction
from app.database.models.coin_wallet import CoinWallet
from app.database.models.user import User
from app.repositories.coin_repository import CoinRepository

logger = logging.getLogger(__name__)

# Transaction type constants — shared with handlers/formatters.
TX_REFERRAL = "referral"
TX_WELCOME_BONUS = "welcome_bonus"
TX_ADMIN_ADD = "admin_add"
TX_ADMIN_REMOVE = "admin_remove"
TX_ADMIN_RESET = "admin_reset"
TX_BONUS = "bonus"
TX_PREMIUM_REDEEM = "premium_redeem"

_CODE_CHARS = string.ascii_uppercase + string.digits
_CODE_LENGTH = 8


def _generate_code() -> str:
    """Generate a random 8-char alphanumeric referral code."""
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(_CODE_LENGTH))


class CoinService:
    """Manages coin wallets, referral codes, and the transaction ledger."""

    def __init__(self, coin_repo: CoinRepository) -> None:
        self._repo = coin_repo

    # ── Wallet lifecycle ───────────────────────────────────────────────────

    async def get_or_create_wallet(self, user_id: int) -> CoinWallet:
        """Return the wallet for `user_id`, creating it if it doesn't exist yet."""
        wallet = await self._repo.get_wallet_by_user_id(user_id)
        if wallet is not None:
            return wallet

        # Generate a unique referral code (retry on collision — astronomically rare
        # with 36^8 ≈ 2.8 trillion possibilities, but we guard it properly).
        for attempt in range(10):
            code = _generate_code()
            if await self._repo.get_wallet_by_referral_code(code) is None:
                break
        else:
            raise RuntimeError(
                f"Could not generate a unique referral code for user_id={user_id} "
                "after 10 attempts."
            )

        wallet = await self._repo.create_wallet(user_id=user_id, referral_code=code)
        logger.info("Created CoinWallet for user_id=%s code=%s", user_id, code)
        return wallet

    async def get_referral_code(self, user_id: int) -> str:
        wallet = await self.get_or_create_wallet(user_id)
        return wallet.referral_code

    async def get_wallet_by_referral_code(self, code: str) -> CoinWallet | None:
        return await self._repo.get_wallet_by_referral_code(code.upper())

    # ── Balance reads ──────────────────────────────────────────────────────

    async def get_balance(self, user_id: int) -> int:
        wallet = await self.get_or_create_wallet(user_id)
        return wallet.coin_balance

    async def get_lifetime_stats(self, user_id: int) -> dict[str, int]:
        wallet = await self.get_or_create_wallet(user_id)
        return {
            "balance": wallet.coin_balance,
            "lifetime_earned": wallet.lifetime_earned,
            "lifetime_spent": wallet.lifetime_spent,
        }

    # ── Balance writes ─────────────────────────────────────────────────────

    async def add_coins(
        self,
        user_id: int,
        amount: int,
        tx_type: str,
        description: str,
        ref_telegram_id: int | None = None,
    ) -> CoinTransaction:
        """Credit `amount` coins to `user_id` and record the transaction."""
        if amount <= 0:
            raise ValueError(f"add_coins requires a positive amount, got {amount}")

        wallet = await self.get_or_create_wallet(user_id)
        new_balance = wallet.coin_balance + amount

        tx = await self._repo.create_transaction(
            wallet_id=wallet.id,
            amount=amount,
            tx_type=tx_type,
            description=description,
            ref_telegram_id=ref_telegram_id,
        )
        await self._repo.update_wallet_balance(
            wallet.id,
            new_balance=new_balance,
            earned_delta=amount,
        )
        logger.info(
            "add_coins user_id=%s amount=%d type=%s balance=%d→%d",
            user_id,
            amount,
            tx_type,
            wallet.coin_balance,
            new_balance,
        )
        return tx

    async def remove_coins(
        self,
        user_id: int,
        amount: int,
        tx_type: str,
        description: str,
    ) -> CoinTransaction | None:
        """Debit `amount` coins from `user_id`.

        Returns the transaction on success, or None if the balance is
        insufficient (caller decides how to handle).
        """
        if amount <= 0:
            raise ValueError(f"remove_coins requires a positive amount, got {amount}")

        wallet = await self.get_or_create_wallet(user_id)
        if wallet.coin_balance < amount:
            logger.warning(
                "remove_coins user_id=%s amount=%d but balance=%d — skipped",
                user_id,
                amount,
                wallet.coin_balance,
            )
            return None

        new_balance = wallet.coin_balance - amount
        tx = await self._repo.create_transaction(
            wallet_id=wallet.id,
            amount=-amount,
            tx_type=tx_type,
            description=description,
        )
        await self._repo.update_wallet_balance(
            wallet.id,
            new_balance=new_balance,
            spent_delta=amount,
        )
        logger.info(
            "remove_coins user_id=%s amount=%d type=%s balance=%d→%d",
            user_id,
            amount,
            tx_type,
            wallet.coin_balance,
            new_balance,
        )
        return tx

    async def reset_coins(self, user_id: int) -> tuple[CoinWallet, int]:
        """Zero out the balance, recording the wipe as a transaction.

        Returns (wallet_after_reset, amount_removed).
        """
        wallet = await self.get_or_create_wallet(user_id)
        old_balance = wallet.coin_balance
        if old_balance > 0:
            await self._repo.create_transaction(
                wallet_id=wallet.id,
                amount=-old_balance,
                tx_type=TX_ADMIN_RESET,
                description=f"Admin reset (talanced was {old_balance})",
            )
            await self._repo.update_wallet_balance(
                wallet.id,
                new_balance=0,
                spent_delta=old_balance,
            )
        # Re-fetch so callers see the updated state.
        wallet = await self._repo.get_wallet_by_user_id(user_id)
        return wallet, old_balance  # type: ignore[return-value]

    # ── Transaction history ────────────────────────────────────────────────

    async def get_history(
        self, user_id: int, *, limit: int = 20
    ) -> Sequence[CoinTransaction]:
        wallet = await self._repo.get_wallet_by_user_id(user_id)
        if wallet is None:
            return []
        return await self._repo.get_transactions(wallet.id, limit=limit)

    # ── Leaderboard ────────────────────────────────────────────────────────

    async def get_top_holders(
        self, *, limit: int = 10
    ) -> Sequence[tuple[CoinWallet, User]]:
        return await self._repo.get_top_wallets_by_balance(limit=limit)

    # ── Global stats ───────────────────────────────────────────────────────

    async def global_stats(self) -> dict[str, int]:
        return {
            "in_circulation": await self._repo.total_coins_in_circulation(),
            "ever_earned": await self._repo.total_coins_ever_earned(),
        }
