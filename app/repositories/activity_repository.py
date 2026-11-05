"""Data-access layer for the `learning_activities` table.

All queries here are read- or write-only with no business logic:
  - `record` inserts one event row (the only write operation).
  - `get_active_dates` returns the distinct calendar dates on which a user
    had any learning activity (used by ActivityService for streak calculation).
  - `get_summary` returns activity counts grouped by type within a window
    (used by StatsService for the statistics dashboard and weekly reports).
  - `count_by_type` is a convenience single-type counter used by the
    achievement engine.

Intentional design choice: dates are compared in the database using
SQLite's date functions rather than pulling all rows to Python, keeping
streak and summary queries O(result_size) instead of O(total_events).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import distinct, func, select

from app.database.models.learning_activity import ActivityType, LearningActivity
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ActivityRepository(BaseRepository[LearningActivity]):
    """Repository for inserting and querying learning activity events."""

    model = LearningActivity

    async def record(
        self,
        *,
        user_id: int,
        activity_type: ActivityType,
        mnemonic_id: int | None = None,
        vocabulary_entry_id: int | None = None,
        content_source_id: int | None = None,
        outcome: str | None = None,
        score: float | None = None,
        metadata: dict | None = None,
    ) -> LearningActivity:
        """Insert one learning event and return the persisted row.

        Never raises for caller-controlled reasons — only propagates
        genuine DB/connectivity errors.  The caller (ActivityService) is
        responsible for wrapping this in a try/except when the event must
        not interrupt the primary flow.
        """
        entry = LearningActivity(
            user_id=user_id,
            activity_type=activity_type.value,
            mnemonic_id=mnemonic_id,
            vocabulary_entry_id=vocabulary_entry_id,
            content_source_id=content_source_id,
            outcome=outcome,
            score=score,
            metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
        )
        return await self.add(entry)

    async def get_active_dates(
        self,
        user_id: int,
        since: datetime,
    ) -> Sequence[str]:
        """Return the distinct calendar dates (as 'YYYY-MM-DD' strings) on
        which `user_id` had any learning activity since `since`.

        SQLite's `date()` function extracts the calendar date from a
        DateTime value stored as a naive UTC string, which is consistent
        with how `func.now()` populates `occurred_at`.

        Used by ActivityService.get_streak() to count consecutive days
        without pulling all event rows to Python.
        """
        result = await self._session.execute(
            select(
                distinct(func.date(LearningActivity.occurred_at)).label("day")
            )
            .where(LearningActivity.user_id == user_id)
            .where(LearningActivity.occurred_at >= since)
            .order_by("day")
        )
        return result.scalars().all()

    async def get_summary(
        self,
        user_id: int,
        since: datetime,
    ) -> dict[str, int]:
        """Return activity counts grouped by `activity_type` for `user_id`
        since `since`.

        Returns a plain dict: {"mnemonic_generated": 5, "vocabulary_saved": 3, …}
        Missing activity types are absent from the dict (not set to 0).
        """
        result = await self._session.execute(
            select(
                LearningActivity.activity_type,
                func.count(LearningActivity.id).label("cnt"),
            )
            .where(LearningActivity.user_id == user_id)
            .where(LearningActivity.occurred_at >= since)
            .group_by(LearningActivity.activity_type)
        )
        return {row.activity_type: row.cnt for row in result}

    async def get_recent_by_type(
        self,
        user_id: int,
        activity_type: ActivityType,
        *,
        since: datetime,
        limit: int = 20,
    ) -> list[LearningActivity]:
        """Return recent activity rows of a specific type since `since`.

        Used by ContextBuilder to retrieve vocabulary searches, quiz answers,
        chat messages, etc. for injection into AI prompts.
        """
        result = await self._session.execute(
            select(LearningActivity)
            .where(LearningActivity.user_id == user_id)
            .where(LearningActivity.activity_type == activity_type.value)
            .where(LearningActivity.occurred_at >= since)
            .order_by(LearningActivity.occurred_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_mnemonic_words(
        self,
        user_id: int,
        since: datetime,
        limit: int = 30,
    ) -> list[str]:
        """Return words the user looked up (from metadata_json) since `since`.

        Parses the 'word' key from metadata_json on MNEMONIC_GENERATED rows.
        Returns unique words, most recent first.
        """
        rows = await self.get_recent_by_type(
            user_id, ActivityType.MNEMONIC_GENERATED, since=since, limit=limit
        )
        seen: set[str] = set()
        words: list[str] = []
        for row in rows:
            if row.metadata_json:
                try:
                    meta = json.loads(row.metadata_json)
                    word = meta.get("word", "")
                    if word and word not in seen:
                        seen.add(word)
                        words.append(word)
                except (json.JSONDecodeError, TypeError):
                    pass
        return words

    async def count_by_type(
        self,
        user_id: int,
        activity_type: ActivityType,
        since: datetime | None = None,
    ) -> int:
        """Count events of a single type, optionally bounded by `since`.

        Used by the achievement engine to evaluate trigger conditions such
        as "has generated at least 100 mnemonics".
        """
        stmt = (
            select(func.count(LearningActivity.id))
            .where(LearningActivity.user_id == user_id)
            .where(LearningActivity.activity_type == activity_type.value)
        )
        if since is not None:
            stmt = stmt.where(LearningActivity.occurred_at >= since)

        result = await self._session.execute(stmt)
        return result.scalar_one() or 0
