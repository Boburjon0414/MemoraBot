"""Read-only aggregate/reporting queries.

Deliberately a separate repository from `MnemonicRepository`: that one
handles CRUD + serving logic for individual mnemonics (SRP), this one
answers cross-cutting "how is the whole library doing" questions. Nothing
here is wired into a handler yet — this is the data layer a future Admin
Panel's Analytics Dashboard (see docs/ROADMAP.md) will call into; every
method is written and ready today because the underlying columns already
exist as of migration 0003.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.mnemonic_history import MnemonicHistory
from app.database.models.user import User


class AnalyticsRepository:
    """Aggregate, read-only queries across the whole mnemonic library."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def total_users(self) -> int:
        result = await self._session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def total_mnemonic_versions(self) -> int:
        """Total rows in `mnemonic_history` (every version of every word)."""
        result = await self._session.execute(select(func.count(MnemonicHistory.id)))
        return result.scalar_one()

    async def total_unique_words(self) -> int:
        result = await self._session.execute(select(func.count(func.distinct(MnemonicHistory.word))))
        return result.scalar_one()

    async def active_vs_deactivated_counts(self) -> dict[str, int]:
        result = await self._session.execute(
            select(MnemonicHistory.is_active, func.count(MnemonicHistory.id)).group_by(
                MnemonicHistory.is_active
            )
        )
        counts = {"active": 0, "deactivated": 0}
        for is_active, count in result.all():
            counts["active" if is_active else "deactivated"] = count
        return counts

    async def most_requested_words(self, limit: int = 10) -> Sequence[tuple[str, int]]:
        """Words with the highest total `uses`, summed across all their versions."""
        result = await self._session.execute(
            select(MnemonicHistory.word, func.sum(MnemonicHistory.uses).label("total_uses"))
            .group_by(MnemonicHistory.word)
            .order_by(func.sum(MnemonicHistory.uses).desc())
            .limit(limit)
        )
        return result.all()

    async def most_regenerated_words(self, limit: int = 10) -> Sequence[tuple[str, int]]:
        """Words whose versions get regenerated away from most often — a
        strong signal that the current knowledge base struggles with them.
        """
        result = await self._session.execute(
            select(MnemonicHistory.word, func.sum(MnemonicHistory.regenerated_count).label("total"))
            .group_by(MnemonicHistory.word)
            .order_by(func.sum(MnemonicHistory.regenerated_count).desc())
            .limit(limit)
        )
        return result.all()

    async def highest_rated_active(self, limit: int = 10) -> Sequence[MnemonicHistory]:
        result = await self._session.execute(
            select(MnemonicHistory)
            .where(MnemonicHistory.is_active.is_(True))
            .order_by(MnemonicHistory.average_rating.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def lowest_rated_active(self, limit: int = 10) -> Sequence[MnemonicHistory]:
        result = await self._session.execute(
            select(MnemonicHistory)
            .where(MnemonicHistory.is_active.is_(True))
            .order_by(MnemonicHistory.average_rating.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def ai_provider_usage(self) -> Sequence[tuple[str, int]]:
        result = await self._session.execute(
            select(MnemonicHistory.ai_provider, func.count(MnemonicHistory.id))
            .group_by(MnemonicHistory.ai_provider)
            .order_by(func.count(MnemonicHistory.id).desc())
        )
        return result.all()

    async def prompt_version_performance(self) -> Sequence[tuple[str, int, float]]:
        """(prompt_version, version_count, average_rating_across_that_version)."""
        result = await self._session.execute(
            select(
                MnemonicHistory.prompt_version,
                func.count(MnemonicHistory.id),
                func.avg(MnemonicHistory.average_rating),
            ).group_by(MnemonicHistory.prompt_version)
        )
        return result.all()

    async def average_response_time_ms(self) -> float | None:
        """Average Gemini generation latency across all fresh generations
        (cache hits have no `response_time_ms` and are excluded automatically).
        """
        result = await self._session.execute(
            select(func.avg(MnemonicHistory.response_time_ms)).where(
                MnemonicHistory.response_time_ms.is_not(None)
            )
        )
        return result.scalar_one_or_none()

    async def library_growth_by_day(self, days: int = 30) -> Sequence[tuple[str, int]]:
        """New mnemonic versions created per day, most recent `days` days."""
        result = await self._session.execute(
            select(
                func.date(MnemonicHistory.created_at).label("day"),
                func.count(MnemonicHistory.id),
            )
            .group_by(func.date(MnemonicHistory.created_at))
            .order_by(func.date(MnemonicHistory.created_at).desc())
            .limit(days)
        )
        return result.all()
