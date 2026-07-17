"""Business logic for recording and reading user feedback (ratings) on
generated mnemonics, and keeping the mnemonic library's denormalized
statistics in sync with that feedback.

Follows the same convention as `SettingsService`: every public method takes
a Telegram user id and resolves the internal user internally, so handlers
never need to reason about internal primary keys.
"""

from __future__ import annotations

import logging

from app.database.models.mnemonic_feedback import MnemonicFeedback
from app.repositories.mnemonic_feedback_repository import MnemonicFeedbackRepository
from app.repositories.mnemonic_repository import MnemonicRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# A version with at least this many net dislikes has clearly failed to help
# learners — retire it. Like the regeneration threshold in
# `MnemonicService`, this is a starting heuristic, not a tuned constant.
_DISLIKE_DEACTIVATION_THRESHOLD = 3


class MnemonicFeedbackService:
    """Records 👍/👎 ratings, keeps `mnemonic_history`'s denormalized
    likes/dislikes/average_rating in sync, and retires consistently
    disliked versions.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        feedback_repo: MnemonicFeedbackRepository,
        mnemonic_repo: MnemonicRepository,
    ) -> None:
        self._user_repo = user_repo
        self._feedback_repo = feedback_repo
        self._mnemonic_repo = mnemonic_repo

    async def rate(
        self, *, telegram_id: int, mnemonic_history_id: int, is_helpful: bool
    ) -> MnemonicFeedback | None:
        """Record (or update) `telegram_id`'s rating for a specific mnemonic,
        then update that mnemonic's denormalized stats and, if warranted,
        deactivate it.

        Returns None if `telegram_id` isn't a registered user (defensive;
        should not normally happen since rating buttons only appear after
        registration).
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return None

        previous = await self._feedback_repo.get_by_mnemonic_and_user(mnemonic_history_id, user.id)
        feedback = await self._feedback_repo.upsert(
            mnemonic_history_id=mnemonic_history_id, user_id=user.id, is_helpful=is_helpful
        )

        like_delta, dislike_delta = self._compute_deltas(previous, is_helpful)
        if like_delta or dislike_delta:
            updated = await self._mnemonic_repo.apply_feedback_delta(
                mnemonic_history_id, like_delta=like_delta, dislike_delta=dislike_delta
            )
            if updated is not None and updated.dislikes >= _DISLIKE_DEACTIVATION_THRESHOLD and (
                updated.dislikes > updated.likes
            ):
                logger.info(
                    "mnemonic_history.id=%s has %d net dislikes, deactivating",
                    mnemonic_history_id,
                    updated.dislikes - updated.likes,
                )
                await self._mnemonic_repo.deactivate(mnemonic_history_id)

        return feedback

    @staticmethod
    def _compute_deltas(previous: MnemonicFeedback | None, is_helpful: bool) -> tuple[int, int]:
        """Translate a new rating (and any prior one) into (like_delta, dislike_delta).

        Handles all three cases: first-time rating, an unchanged re-tap
        (idempotent, both deltas 0), and a flipped vote (moves one count to
        the other).
        """
        if previous is None:
            return (1, 0) if is_helpful else (0, 1)
        if previous.is_helpful == is_helpful:
            return (0, 0)
        return (1, -1) if is_helpful else (-1, 1)

    async def get_user_rating(self, *, telegram_id: int, mnemonic_history_id: int) -> bool | None:
        """Return True/False if `telegram_id` already rated this mnemonic, else None.

        Used to render the 👍/👎 buttons with the user's existing choice
        highlighted whenever a mnemonic (fresh, cached, or regenerated) is shown.
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        feedback = await self._feedback_repo.get_by_mnemonic_and_user(mnemonic_history_id, user.id)
        return feedback.is_helpful if feedback else None
