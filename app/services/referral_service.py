"""ReferralService: viral referral business logic and coin-economy integration.

Responsibilities:
- Validate and process incoming referral codes at registration time.
- Calculate escalating rewards (Friend #N earns more than Friend #1).
- Build the invite-friends page data (balance, stats, milestone).
- Provide admin panel data (top referrers, user search, coin actions).

All coin mutations go through CoinService — this service never writes
balances directly.
"""

from __future__ import annotations

import logging

from app.database.models.referral import Referral
from app.database.models.user import User
from app.repositories.referral_repository import ReferralRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository
from app.services.coin_service import (
    TX_ADMIN_ADD,
    TX_ADMIN_REMOVE,
    TX_BONUS,
    TX_REFERRAL,
    TX_WELCOME_BONUS,
    CoinService,
)

logger = logging.getLogger(__name__)


class ReferralService:
    """Orchestrates the referral flow, reward calculation, and admin reporting."""

    def __init__(
        self,
        referral_repo: ReferralRepository,
        user_repo: UserRepository,
        settings_repo: UserSettingsRepository,
        coin_service: CoinService,
        *,
        base_reward: int,
        increment: int,
        max_reward: int,
        welcome_bonus: int,
        premium_daily_cost: int,
        top_limit: int,
        bot_username: str,
    ) -> None:
        self._referral_repo = referral_repo
        self._user_repo = user_repo
        self._settings_repo = settings_repo
        self._coin_service = coin_service
        self._base_reward = base_reward
        self._increment = increment
        self._max_reward = max_reward
        self._welcome_bonus = welcome_bonus
        self._premium_daily_cost = premium_daily_cost
        self._top_limit = top_limit
        self._bot_username = bot_username

    # ── Reward formula ─────────────────────────────────────────────────────

    def calculate_reward(self, current_referral_count: int) -> int:
        """Reward for the (current_referral_count + 1)th successful referral.

        Example with base=20, increment=2, max=100:
          count=0 → 20 coins  (Friend #1)
          count=1 → 22 coins  (Friend #2)
          count=2 → 24 coins  (Friend #3)
          ...
          count=39 → 98 coins (capped at max=100 at count=40)
        """
        reward = self._base_reward + current_referral_count * self._increment
        return min(reward, self._max_reward)

    # ── Invite link ────────────────────────────────────────────────────────

    async def get_invite_link(self, user_id: int) -> str:
        code = await self._coin_service.get_referral_code(user_id)
        return f"https://t.me/{self._bot_username}?start={code}"

    # ── Registration hook ──────────────────────────────────────────────────

    async def process_referral(
        self,
        referral_code: str,
        new_user_id: int,
        new_user_telegram_id: int,
    ) -> bool:
        """Validate and award a referral when a new user registers.

        Safety guarantees:
        - Invalid code → silently ignored (returns False).
        - Self-referral → silently ignored.
        - Duplicate (already referred) → silently ignored.
        - Race conditions → DB UNIQUE constraint on `referred_id` is the
          last-resort guard; the service check is the first line of defence.

        Returns True on success, False on any guard failure.
        """
        # 1. Look up who owns this code.
        referrer_wallet = await self._coin_service.get_wallet_by_referral_code(
            referral_code
        )
        if referrer_wallet is None:
            logger.info(
                "process_referral: unknown code=%r for new_user_id=%s — ignored",
                referral_code,
                new_user_id,
            )
            return False

        referrer_user_id = referrer_wallet.user_id

        # 2. Prevent self-referral.
        if referrer_user_id == new_user_id:
            logger.warning(
                "process_referral: self-referral attempt user_id=%s — blocked",
                new_user_id,
            )
            return False

        # 3. Prevent duplicate referral (belt-and-suspenders before DB UNIQUE hits).
        existing = await self._referral_repo.get_by_referred_id(new_user_id)
        if existing is not None:
            logger.warning(
                "process_referral: user_id=%s already has a referrer — blocked",
                new_user_id,
            )
            return False

        # 4. Calculate reward based on referrer's current successful-referral count.
        referral_count = await self._referral_repo.count_referrals_by_referrer(
            referrer_user_id
        )
        reward = self.calculate_reward(referral_count)

        # 5. Persist the relationship (not yet rewarded — reward comes next).
        referral_row = await self._referral_repo.create_referral(
            referrer_id=referrer_user_id,
            referred_id=new_user_id,
            referral_code=referral_code,
            reward_amount=reward,
        )

        # 6. Award coins to referrer and mark the row as rewarded.
        await self._coin_service.add_coins(
            referrer_user_id,
            reward,
            TX_REFERRAL,
            f"Do'st #{referral_count + 1} taklif etildi (+{reward} tanga)",
            ref_telegram_id=new_user_telegram_id,
        )
        await self._referral_repo.mark_rewarded(referral_row.id, reward)

        # 7. Optional welcome bonus for the new user.
        if self._welcome_bonus > 0:
            await self._coin_service.add_coins(
                new_user_id,
                self._welcome_bonus,
                TX_WELCOME_BONUS,
                "Ro'yxatdan o'tish bonusi",
            )

        logger.info(
            "process_referral: referrer_id=%s ← referred_id=%s reward=%d",
            referrer_user_id,
            new_user_id,
            reward,
        )
        return True

    # ── Invite-friends page data ───────────────────────────────────────────

    async def get_invite_stats(self, user_id: int) -> dict:
        """All data needed to render the invite-friends page."""
        wallet = await self._coin_service.get_or_create_wallet(user_id)
        referral_count = await self._referral_repo.count_referrals_by_referrer(user_id)
        next_reward = self.calculate_reward(referral_count)
        invite_link = await self.get_invite_link(user_id)
        milestone = self._calculate_milestone(referral_count, wallet.coin_balance)

        return {
            "balance": wallet.coin_balance,
            "referral_count": referral_count,
            "next_reward": next_reward,
            "invite_link": invite_link,
            "milestone": milestone,
            "lifetime_earned": wallet.lifetime_earned,
        }

    def _calculate_milestone(
        self, referral_count: int, current_balance: int
    ) -> dict:
        """Dynamically compute a motivational milestone toward 1-day premium."""
        cost = self._premium_daily_cost
        coins_needed = max(0, cost - current_balance)

        if coins_needed == 0:
            return {
                "friends_needed": 0,
                "coins_from_referrals": 0,
                "coins_needed": 0,
                "premium_cost": cost,
                "can_afford": True,
            }

        # Project forward to find minimum additional referrals needed.
        friends_needed = 0
        projected = current_balance
        temp_count = referral_count
        while projected < cost:
            projected += self.calculate_reward(temp_count)
            temp_count += 1
            friends_needed += 1

        coins_from_referrals = projected - current_balance
        return {
            "friends_needed": friends_needed,
            "coins_from_referrals": coins_from_referrals,
            "coins_needed": coins_needed,
            "premium_cost": cost,
            "can_afford": False,
        }

    # ── Admin reporting ────────────────────────────────────────────────────

    async def get_top_referrers(self) -> list[dict]:
        """Top users by referral count, enriched with user and wallet data."""
        rows = await self._referral_repo.get_top_referrers(limit=self._top_limit)
        result = []
        for referrer_id, count in rows:
            user = await self._user_repo.get_by_id(referrer_id)
            if user is None:
                continue
            wallet = await self._coin_service.get_or_create_wallet(referrer_id)
            # Sum of all rewards paid out to this referrer
            referrals = await self._referral_repo.get_referrals_by_referrer(
                referrer_id, limit=1000
            )
            coins_earned = sum(r.reward_amount for r in referrals if r.rewarded)
            result.append(
                {
                    "user": user,
                    "referral_count": count,
                    "coins_earned": coins_earned,
                    "current_balance": wallet.coin_balance,
                }
            )
        return result

    async def get_top_coin_holders(self) -> list[dict]:
        """Top users by current coin balance."""
        pairs = await self._coin_service.get_top_holders(limit=self._top_limit)
        result = []
        for wallet, user in pairs:
            ref_count = await self._referral_repo.count_referrals_by_referrer(user.id)
            result.append(
                {
                    "user": user,
                    "wallet": wallet,
                    "referral_count": ref_count,
                }
            )
        return result

    async def get_recent_referrals(self, *, limit: int = 10) -> list[Referral]:
        return list(await self._referral_repo.get_recent_referrals(limit=limit))

    async def get_referral_overview_stats(self) -> dict:
        """Global stats for the admin referral statistics page."""
        coin_stats = await self._coin_service.global_stats()
        return {
            "total_referrals": await self._referral_repo.total_referrals(),
            "unique_referrers": await self._referral_repo.unique_referrers_count(),
            "total_coins_awarded": await self._referral_repo.total_coins_awarded_via_referral(),
            "coins_in_circulation": coin_stats["in_circulation"],
            "coins_ever_earned": coin_stats["ever_earned"],
        }

    async def get_user_admin_profile(self, telegram_id: int) -> dict | None:
        """Full admin profile for a user: wallet, referrer, invited count, premium."""
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return None

        wallet = await self._coin_service.get_or_create_wallet(user.id)
        settings_row = await self._settings_repo.get_by_user_id(user.id)
        is_premium = settings_row.is_premium if settings_row else False

        referrer = await self._referral_repo.get_referrer_for_user(user.id)
        invited_count = await self._referral_repo.count_referrals_by_referrer(user.id)
        recent_tx = await self._coin_service.get_history(user.id, limit=5)

        return {
            "user": user,
            "wallet": wallet,
            "is_premium": is_premium,
            "referrer": referrer,
            "invited_count": invited_count,
            "recent_tx": recent_tx,
        }

    # ── Admin coin actions (all delegated to CoinService) ──────────────────

    async def admin_add_coins(
        self, target_telegram_id: int, amount: int, reason: str
    ) -> bool:
        user = await self._user_repo.get_by_telegram_id(target_telegram_id)
        if user is None:
            return False
        await self._coin_service.add_coins(
            user.id, amount, TX_ADMIN_ADD, f"Admin: {reason}"
        )
        return True

    async def admin_remove_coins(
        self, target_telegram_id: int, amount: int, reason: str
    ) -> bool:
        user = await self._user_repo.get_by_telegram_id(target_telegram_id)
        if user is None:
            return False
        tx = await self._coin_service.remove_coins(
            user.id, amount, TX_ADMIN_REMOVE, f"Admin: {reason}"
        )
        return tx is not None

    async def admin_reset_coins(self, target_telegram_id: int) -> tuple[bool, int]:
        user = await self._user_repo.get_by_telegram_id(target_telegram_id)
        if user is None:
            return False, 0
        _, removed = await self._coin_service.reset_coins(user.id)
        return True, removed

    async def admin_give_bonus(
        self, target_telegram_id: int, amount: int, reason: str
    ) -> bool:
        user = await self._user_repo.get_by_telegram_id(target_telegram_id)
        if user is None:
            return False
        await self._coin_service.add_coins(
            user.id, amount, TX_BONUS, f"Bonus: {reason}"
        )
        return True
