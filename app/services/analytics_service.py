"""Thin service wrapper over `AnalyticsRepository`.

Not wired into any handler yet — see docs/ROADMAP.md for why the Admin
Panel UI that would display these is deferred. This exists now so that UI
can be built as a display layer over an already-complete, already-correct
data layer, rather than needing its own data-access code written later.
"""

from __future__ import annotations

from typing import Sequence

from app.database.models.mnemonic_history import MnemonicHistory
from app.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    """Read-only reporting over the whole mnemonic library."""

    def __init__(self, analytics_repo: AnalyticsRepository) -> None:
        self._repo = analytics_repo

    async def overview(self) -> dict[str, object]:
        """A single call returning the headline figures — total users, total
        unique words, total mnemonic versions, active vs. deactivated,
        average AI response time.
        """
        active_counts = await self._repo.active_vs_deactivated_counts()
        return {
            "total_users": await self._repo.total_users(),
            "total_unique_words": await self._repo.total_unique_words(),
            "total_mnemonic_versions": await self._repo.total_mnemonic_versions(),
            "active_versions": active_counts["active"],
            "deactivated_versions": active_counts["deactivated"],
            "average_response_time_ms": await self._repo.average_response_time_ms(),
        }

    async def most_requested_words(self, limit: int = 10) -> Sequence[tuple[str, int]]:
        return await self._repo.most_requested_words(limit)

    async def most_regenerated_words(self, limit: int = 10) -> Sequence[tuple[str, int]]:
        return await self._repo.most_regenerated_words(limit)

    async def highest_rated_active(self, limit: int = 10) -> Sequence[MnemonicHistory]:
        return await self._repo.highest_rated_active(limit)

    async def lowest_rated_active(self, limit: int = 10) -> Sequence[MnemonicHistory]:
        return await self._repo.lowest_rated_active(limit)

    async def ai_provider_usage(self) -> Sequence[tuple[str, int]]:
        return await self._repo.ai_provider_usage()

    async def prompt_version_performance(self) -> Sequence[tuple[str, int, float]]:
        return await self._repo.prompt_version_performance()

    async def library_growth_by_day(self, days: int = 30) -> Sequence[tuple[str, int]]:
        return await self._repo.library_growth_by_day(days)
