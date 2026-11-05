"""UserContextService — assembles a `UserContext` value object for one user.

This service is the only place that knows how to gather the learner's
full profile from multiple data sources.  Everything else receives a
finished `UserContext` and never queries these sources directly for
profile data.

Query budget per request
------------------------
`build()` performs exactly three async DB calls:
  1. `settings_repo.get_by_user_id()` — 1 row, PK lookup
  2. `vocabulary_repo.count()` — one COUNT query, O(index scan)
  3. `activity_service.get_streak()` — one DATE-grouped SELECT over
     the last 90 days of learning_activities for this user

All three are against indexed columns.  Total DB time is O(1) from the
caller's perspective — there is no N+1 risk here.

Failure isolation
-----------------
Each of the three queries is wrapped independently.  If, say, the
activity log is unavailable, `build()` still returns a valid `UserContext`
with `current_streak_days=0` / `best_streak_days=0`.  A partial context
is always better than no context — the AI prompt degrades gracefully.

Step 8 additions
----------------
When `user_memory` is added, `build()` will gain a fourth query:
  4. `user_memory_repo.get_by_user_id()` — 1 row, FK lookup
That query populates `english_level`, `learning_goal`, `native_language`,
`recent_weak_words`, and `active_topic`.  All call sites of `build()` and
all consumers of `UserContext` require zero changes.
"""

from __future__ import annotations

import logging

from app.repositories.user_settings_repository import UserSettingsRepository
from app.repositories.user_memory_repository import UserMemoryRepository  # Step 8
from app.repositories.vocabulary_repository import VocabularyRepository
from app.services.activity_service import ActivityService
from app.services.context.user_context import UserContext

logger = logging.getLogger(__name__)

_DEFAULT_LANGUAGE = "uz"


class UserContextService:
    """Assembles a `UserContext` value object for one user per request.

    Injected by `ServicesMiddleware` as `data["user_context_service"]`.
    Handlers or services that need the context call `await build(user_id)`
    — typically at the entry point of an AI-powered handler so the context
    is ready for any downstream service that needs it.

    Note: `build()` takes the internal `user_id` (from `users.id`), not
    the Telegram id.  Callers that only have a Telegram id should resolve
    it via `UserService.get_by_telegram_id()` first (which is already done
    in every handler that reaches an AI feature).
    """

    def __init__(
        self,
        settings_repo: UserSettingsRepository,
        vocabulary_repo: VocabularyRepository,
        activity_service: ActivityService,
        memory_repo: UserMemoryRepository | None = None,  # Step 8
    ) -> None:
        self._settings_repo = settings_repo
        self._vocabulary_repo = vocabulary_repo
        self._activity_service = activity_service
        self._memory_repo = memory_repo  # Step 8

    async def build(self, user_id: int) -> UserContext:
        """Assemble and return an immutable `UserContext` for `user_id`.

        Never raises: all three sub-queries are independently guarded.
        Logs a warning for each failure and substitutes a safe default.

        Args:
            user_id: The internal `users.id` primary key (NOT Telegram id).

        Returns:
            A fully-constructed, frozen `UserContext`.  Fields sourced from
            `user_memory` (english_level, learning_goal, native_language,
            recent_weak_words, active_topic) are None / [] until Step 8.
        """

        # ── 1. User settings (language + premium flag) ─────────────────── #
        preferred_language = _DEFAULT_LANGUAGE
        is_premium = False
        try:
            settings = await self._settings_repo.get_by_user_id(user_id)
            if settings is not None:
                preferred_language = settings.preferred_language or _DEFAULT_LANGUAGE
                is_premium = bool(settings.is_premium)
        except Exception:
            logger.warning(
                "UserContextService: failed to fetch settings for user_id=%s — "
                "using defaults",
                user_id,
                exc_info=True,
            )

        # ── 2. Vocabulary size (count of saved words) ──────────────────── #
        vocabulary_size = 0
        try:
            vocabulary_size = await self._vocabulary_repo.count(user_id)
        except Exception:
            logger.warning(
                "UserContextService: failed to count vocabulary for user_id=%s — "
                "defaulting to 0",
                user_id,
                exc_info=True,
            )

        # ── 3. Streak data (from learning_activities) ──────────────────── #
        current_streak = 0
        best_streak = 0
        try:
            current_streak, best_streak = await self._activity_service.get_streak(user_id)
        except Exception:
            logger.warning(
                "UserContextService: failed to compute streak for user_id=%s — "
                "defaulting to 0",
                user_id,
                exc_info=True,
            )

        # ── 4. Learning profile fields (Step 8 — user_memory table) ───────── #
        english_level: str | None = None
        learning_goal: str | None = None
        native_language: str | None = None
        recent_weak_words: list[str] = []
        active_topic: str | None = None

        if self._memory_repo is not None:
            try:
                memory = await self._memory_repo.get_by_user_id(user_id)
                if memory is not None:
                    english_level = memory.english_level
                    learning_goal = memory.learning_goal
                    native_language = memory.native_language
                    active_topic = memory.active_topic
                    # Import inline to avoid circular dependency
                    from app.repositories.user_memory_repository import _load_json_list
                    raw_words = _load_json_list(memory.weak_words_json)
                    # Return most recent 10, newest first
                    recent_weak_words = list(reversed(raw_words[-10:]))
            except Exception:
                logger.warning(
                    "UserContextService: failed to fetch memory for user_id=%s — "
                    "using empty profile",
                    user_id,
                    exc_info=True,
                )

        return UserContext(
            user_id=user_id,
            preferred_language=preferred_language,
            is_premium=is_premium,
            english_level=english_level,
            learning_goal=learning_goal,
            native_language=native_language,
            vocabulary_size=vocabulary_size,
            current_streak_days=current_streak,
            best_streak_days=best_streak,
            recent_weak_words=recent_weak_words,
            active_topic=active_topic,
        )
