"""ActivityService — records learning events and answers aggregate questions.

This service is the write-side and read-side interface to the
`learning_activities` event log.

Write side
----------
  `record(...)` is called by any handler or service after a learning action
  completes successfully.  It MUST be called inside a try/except in the
  calling code so that a DB failure here never causes the primary feature
  to fail.  See the handler hook pattern in mnevoca.py for the canonical
  example.

Read side
---------
  `get_streak(user_id)` computes the current and best streak from the
  calendar dates in the activity log.  Streak is defined as a run of
  consecutive calendar days (UTC) on which at least one activity occurred.
  Missing even one day resets the current streak to the length of the
  most-recent unbroken run.

  `get_summary(user_id, since)` returns a {activity_type: count} dict
  for the given user and time window.  This is the single data source
  for the statistics dashboard and weekly report — no other table is
  queried.

Streak algorithm
----------------
Given a list of distinct dates on which the user was active (sorted
ascending), we scan backwards from today:

  1. If today (UTC) is in the list, the current run is alive.
  2. If yesterday (UTC) is in the list but today isn't, the current run
     ended yesterday and we count back from there.
  3. At any point where the gap to the previous date > 1 day, the run breaks.

This is O(N) in the number of active days, and N is always small relative
to the lookback window we query.

Best streak
-----------
Computed in the same pass: we track the maximum run length seen while
scanning the full sorted date list.  Stored in the service response but
NOT persisted (yet) — when the `user_memory` table is introduced in Step 8,
best_streak will be written there after each computation so it survives
log pruning.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from app.database.models.learning_activity import ActivityType, LearningActivity
from app.repositories.activity_repository import ActivityRepository

logger = logging.getLogger(__name__)

# How far back to look for streak and summary queries in the absence of an
# explicit `since` argument.  90 days covers any realistic streak without
# full-table scans on a large history.
_DEFAULT_LOOKBACK_DAYS = 90


class ActivityService:
    """Records learning activities and answers aggregate streak/summary queries."""

    def __init__(self, activity_repo: ActivityRepository) -> None:
        self._repo = activity_repo

    # ── Write side ─────────────────────────────────────────────────────── #

    async def record(
        self,
        user_id: int,
        activity_type: ActivityType,
        *,
        mnemonic_id: int | None = None,
        vocabulary_entry_id: int | None = None,
        content_source_id: int | None = None,
        outcome: str | None = None,
        score: float | None = None,
        metadata: dict | None = None,
    ) -> LearningActivity | None:
        """Record one learning event.

        Returns the persisted row on success, or None if the insert fails.
        Failures are logged as warnings and never re-raised, so a broken
        activity log never interrupts the primary user-facing feature.

        Callers should still wrap this in try/except if they need to
        distinguish "recorded" from "not recorded" for business logic
        (e.g. first-time achievement checks), but they are not required to.
        """
        try:
            entry = await self._repo.record(
                user_id=user_id,
                activity_type=activity_type,
                mnemonic_id=mnemonic_id,
                vocabulary_entry_id=vocabulary_entry_id,
                content_source_id=content_source_id,
                outcome=outcome,
                score=score,
                metadata=metadata,
            )
            logger.debug(
                "Recorded activity user_id=%s type=%s id=%s",
                user_id,
                activity_type.value,
                entry.id,
            )
            return entry
        except Exception:
            logger.warning(
                "Failed to record activity user_id=%s type=%s — "
                "continuing without event log entry",
                user_id,
                activity_type.value,
                exc_info=True,
            )
            return None

    # ── Read side ──────────────────────────────────────────────────────── #

    async def get_streak(
        self,
        user_id: int,
        lookback_days: int = _DEFAULT_LOOKBACK_DAYS,
    ) -> tuple[int, int]:
        """Return (current_streak_days, best_streak_days).

        Both values are 0 if the user has no recorded activity in the
        lookback window.

        The algorithm is explained in the module docstring.
        """
        since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=lookback_days)
        raw_dates = await self._repo.get_active_dates(user_id=user_id, since=since)

        if not raw_dates:
            return 0, 0

        # Parse the 'YYYY-MM-DD' strings returned by SQLite's date().
        from datetime import date as date_type
        dates: list[date_type] = sorted(
            date_type.fromisoformat(d) for d in raw_dates
        )

        today = datetime.now(UTC).date()

        # ── Compute best streak (full forward pass) ─────────────────────── #
        best = 1
        run = 1
        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                run += 1
                best = max(best, run)
            else:
                run = 1

        # ── Compute current streak (backward from today or yesterday) ───── #
        # If the user was active today, the current run is still alive.
        # If the last active day was yesterday, the run ended but we count it.
        # Anything older means the current streak is 0.
        last_active = dates[-1]
        if (today - last_active).days > 1:
            # Gap of 2+ days: current streak is broken
            return 0, best

        # Walk backward from last_active, counting consecutive days.
        current = 1
        for i in range(len(dates) - 2, -1, -1):
            if (dates[i + 1] - dates[i]).days == 1:
                current += 1
            else:
                break

        return current, max(best, current)

    async def get_summary(
        self,
        user_id: int,
        since: datetime | None = None,
    ) -> dict[str, int]:
        """Return activity counts by type since `since`.

        If `since` is None, defaults to 30 days ago (enough for a monthly
        stats view without a full-table scan).

        Example return value::

            {
                "mnemonic_generated": 12,
                "vocabulary_saved": 9,
                "quiz_answered": 4,
            }

        Missing activity types are absent from the dict; callers should
        use .get(key, 0) when they need a guaranteed integer.
        """
        if since is None:
            since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
        return await self._repo.get_summary(user_id=user_id, since=since)

    async def count(
        self,
        user_id: int,
        activity_type: ActivityType,
        since: datetime | None = None,
    ) -> int:
        """Count a single activity type, optionally from `since`.

        Convenience wrapper used by the achievement engine so it doesn't
        need to call get_summary and pick one key.
        """
        return await self._repo.count_by_type(
            user_id=user_id,
            activity_type=activity_type,
            since=since,
        )
