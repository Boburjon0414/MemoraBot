"""Business logic for generating, caching, and regenerating mnemonics —
the self-improving mnemonic library.

This is the orchestration point the whole architecture is built around: it
depends on the `AIProvider` abstraction (never a concrete provider) and the
`MnemonicRepository` abstraction (never raw SQL/SQLAlchemy), so either side
can change independently.

V1.2: `get_or_generate` now serves the highest-rated ACTIVE version of a
word (not just the most recent one), records every serve as a "use", times
every fresh generation, and `regenerate` tracks which specific version was
regenerated away from — deactivating it if that happens often enough.
"""

from __future__ import annotations

import logging
import time
from typing import Sequence

from app.core.exceptions import AIProviderError
from app.database.models.mnemonic_history import MnemonicHistory
from app.repositories.mnemonic_repository import MnemonicRepository
from app.services.ai.base import MnemonicProvider

logger = logging.getLogger(__name__)

_MAX_AVOID_VERSIONS = 8

# A version that's been regenerated away from this many times has
# repeatedly failed to satisfy learners even before an explicit 👎 — retire
# it so it stops being offered as "the" version for this word. A starting
# heuristic, not a scientifically tuned constant; easy to adjust as real
# usage data comes in (see docs/MNEMONIC_LIBRARY.md).
_REGENERATION_DEACTIVATION_THRESHOLD = 3


class MnemonicService:
    """Generates, serves, and manages the lifecycle of mnemonic versions."""

    def __init__(self, provider: MnemonicProvider, mnemonic_repo: MnemonicRepository) -> None:
        self._provider = provider
        self._mnemonic_repo = mnemonic_repo

    async def get_or_generate(self, *, user_id: int, word: str) -> MnemonicHistory:
        """Return the best existing version of `word` if one is active;
        otherwise generate, save, and return a brand new one.

        This is MemoraBot's mnemonic cache AND self-improving library in one
        step: the AI provider is only ever called for a word with no active
        version yet (a genuinely new word, or one whose every prior version
        was deactivated for poor quality) — never merely to get "the latest".

        Args:
            user_id: the *internal* `users.id` of the requesting user — only
                used if this turns out to be a cache miss and a new row
                needs an owner.
            word: the raw word/phrase the user typed.

        Raises:
            AIProviderError: if this is a cache miss and the AI provider fails.
        """
        cleaned_word = word.strip().lower()

        best = await self._mnemonic_repo.get_best_active_by_word(cleaned_word)
        if best is not None:
            logger.info(
                "Serving cached word=%s (mnemonic_history.id=%s, rating=%.2f)",
                cleaned_word,
                best.id,
                best.average_rating,
            )
            await self._mnemonic_repo.record_use(best.id)
            return best

        logger.info("No active version for word=%s, generating via AI", cleaned_word)
        return await self._generate_and_persist(user_id=user_id, word=cleaned_word, avoid=None)

    async def would_require_generation(self, word: str) -> bool:
        """True if looking up `word` right now would need a fresh AI call.

        A cheap peek used by the free-plan quota check (see `UsageService`)
        *before* committing to `get_or_generate`, so a user who's out of
        quota only ever gets blocked for words that would actually cost a
        generation — anything already in the library stays free regardless
        of quota.
        """
        cleaned_word = word.strip().lower()
        best = await self._mnemonic_repo.get_best_active_by_word(cleaned_word)
        return best is None

    async def regenerate(self, *, user_id: int, word: str, source_mnemonic_id: int) -> MnemonicHistory:
        """Force a brand-new mnemonic for `word`, ignoring any cached version,
        and save it as a new version ("🔄 Generate Another Mnemonic").

        Every existing version's Uzbek pronunciation is passed to the AI
        provider as context to avoid, so regeneration reliably produces
        something different. The new version becomes the one future
        `get_or_generate` calls prefer *if* it ends up rated higher — nothing
        is deleted; every prior version stays in the table.

        Args:
            source_mnemonic_id: the specific version the learner was looking
                at when they tapped regenerate. Its `regenerated_count` is
                incremented, and it's deactivated if that crosses the
                threshold — an implicit "not good enough" signal distinct
                from an explicit 👎.

        Raises:
            AIProviderError: if the AI provider fails.
        """
        cleaned_word = word.strip().lower()

        previous_versions = await self._mnemonic_repo.get_all_by_word(cleaned_word)
        avoid = [v.uzbek_pronunciation for v in previous_versions if v.uzbek_pronunciation]
        avoid = avoid[:_MAX_AVOID_VERSIONS] or None

        logger.info(
            "Regenerating word=%s (avoiding %d previous version(s))",
            cleaned_word,
            len(avoid) if avoid else 0,
        )

        await self._mnemonic_repo.increment_regenerated_count(source_mnemonic_id)
        source = await self._mnemonic_repo.get_by_id(source_mnemonic_id)
        if source is not None and source.regenerated_count >= _REGENERATION_DEACTIVATION_THRESHOLD:
            logger.info(
                "mnemonic_history.id=%s regenerated %d times, deactivating",
                source_mnemonic_id,
                source.regenerated_count,
            )
            await self._mnemonic_repo.deactivate(source_mnemonic_id)

        return await self._generate_and_persist(user_id=user_id, word=cleaned_word, avoid=avoid)

    async def get_by_id(self, mnemonic_history_id: int) -> MnemonicHistory | None:
        """Fetch a specific mnemonic version by its row id."""
        return await self._mnemonic_repo.get_by_id(mnemonic_history_id)

    async def get_history(self, user_id: int, limit: int = 10) -> Sequence[MnemonicHistory]:
        """Return a user's most recent mnemonics (newest first)."""
        return await self._mnemonic_repo.get_recent_for_user(user_id, limit=limit)

    async def _generate_and_persist(
        self, *, user_id: int, word: str, avoid: list[str] | None
    ) -> MnemonicHistory:
        """Shared, timed AI-call + save step used by both a cache miss and a regeneration."""
        started_at = time.monotonic()
        try:
            result = await self._provider.generate_mnemonic(word, avoid=avoid)
        except AIProviderError:
            logger.exception(
                "AI provider '%s' failed to generate a mnemonic for word=%s",
                self._provider.name,
                word,
            )
            raise
        response_time_ms = round((time.monotonic() - started_at) * 1000)

        entry = await self._mnemonic_repo.create(
            user_id=user_id,
            word=result.word,
            meaning=result.meaning,
            uzbek_pronunciation=result.uzbek_pronunciation,
            mnemonic_story=result.mnemonic_story,
            example_sentence=result.example_sentence,
            difficulty=result.difficulty.value,
            ai_provider=self._provider.name,
            prompt_version=self._provider.prompt_version,
            response_time_ms=response_time_ms,
        )
        logger.info(
            "Saved mnemonic id=%s for user_id=%s word=%s (%dms)",
            entry.id,
            user_id,
            word,
            response_time_ms,
        )
        return entry
