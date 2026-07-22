"""Data-access layer for the `referrals` table.

Provides the minimal set of queries that `ReferralService` needs.
All business-rule checks live in the service, not here.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.referral import Referral
from app.database.models.user import User


class ReferralRepository:
    """Async repository for `referrals`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_referred_id(self, referred_id: int) -> Referral | None:
        """Look up a referral row by the referred (new) user's internal id."""
        result = await self._session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return result.scalar_one_or_none()

    async def count_referrals_by_referrer(self, referrer_id: int) -> int:
        """How many successful (rewarded) referrals has this user made?"""
        result = await self._session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == referrer_id,
                Referral.rewarded.is_(True),
            )
        )
        return result.scalar_one() or 0

    async def create_referral(
        self,
        *,
        referrer_id: int,
        referred_id: int,
        referral_code: str,
        reward_amount: int,
    ) -> Referral:
        row = Referral(
            referrer_id=referrer_id,
            referred_id=referred_id,
            referral_code=referral_code,
            reward_amount=reward_amount,
            rewarded=False,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def mark_rewarded(self, referral_id: int, reward_amount: int) -> None:
        row = await self._session.get(Referral, referral_id)
        if row is not None:
            row.rewarded = True
            row.reward_amount = reward_amount
            await self._session.flush()

    # ── Admin reporting ────────────────────────────────────────────────────

    async def get_top_referrers(
        self, *, limit: int = 10
    ) -> Sequence[tuple[int, int]]:
        """Return (referrer_id, referral_count) pairs, ordered by count desc."""
        result = await self._session.execute(
            select(Referral.referrer_id, func.count(Referral.id).label("cnt"))
            .where(Referral.rewarded.is_(True))
            .group_by(Referral.referrer_id)
            .order_by(func.count(Referral.id).desc())
            .limit(limit)
        )
        return result.all()

    async def get_recent_referrals(self, *, limit: int = 10) -> Sequence[Referral]:
        """Return the most recently created referrals (with eager-loaded users)."""
        result = await self._session.execute(
            select(Referral)
            .order_by(Referral.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_referrals_by_referrer(
        self, referrer_id: int, *, limit: int = 50
    ) -> Sequence[Referral]:
        result = await self._session.execute(
            select(Referral)
            .where(Referral.referrer_id == referrer_id)
            .order_by(Referral.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def total_referrals(self) -> int:
        result = await self._session.execute(
            select(func.count(Referral.id)).where(Referral.rewarded.is_(True))
        )
        return result.scalar_one() or 0

    async def total_coins_awarded_via_referral(self) -> int:
        result = await self._session.execute(
            select(func.sum(Referral.reward_amount)).where(Referral.rewarded.is_(True))
        )
        return result.scalar_one() or 0

    async def unique_referrers_count(self) -> int:
        result = await self._session.execute(
            select(func.count(func.distinct(Referral.referrer_id))).where(
                Referral.rewarded.is_(True)
            )
        )
        return result.scalar_one() or 0

    async def get_referrer_for_user(self, referred_id: int) -> User | None:
        """Return the User who referred this user, or None."""
        result = await self._session.execute(
            select(User)
            .join(Referral, Referral.referrer_id == User.id)
            .where(Referral.referred_id == referred_id)
        )
        return result.scalar_one_or_none()
