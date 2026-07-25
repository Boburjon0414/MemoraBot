"""Middleware that builds repositories and services for the current session
and injects them into the handler's data — MemoraBot's dependency-injection
mechanism (no external DI framework needed for this project's scope).

Handlers simply declare a parameter like `user_service: UserService` and
aiogram passes the already-constructed instance in automatically.

V1.5 changes:
- When the AI provider is an AIGateway, the middleware looks up the current
  user's premium status and passes a tier-appropriate TierProxy to
  MnemonicService. Handlers remain completely unaware of which provider or
  tier is active.
- `ai_gateway` is injected into handler data so the admin AI Control panel
  can query health and perform key management. It is None when running in
  legacy single-provider mode.
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.coin_repository import CoinRepository
from app.repositories.mnemonic_feedback_repository import MnemonicFeedbackRepository
from app.repositories.mnemonic_repository import MnemonicRepository
from app.repositories.referral_repository import ReferralRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.services.ai.base import AIProvider
from app.services.ai.gateway import AIGateway
from app.services.analytics_service import AnalyticsService
from app.services.broadcast_service import BroadcastService
from app.services.coin_service import CoinService
from app.services.mnemonic_feedback_service import MnemonicFeedbackService
from app.services.mnemonic_service import MnemonicService
from app.services.referral_service import ReferralService
from app.services.settings_service import SettingsService
from app.services.usage_service import UsageService
from app.services.user_service import UserService
from app.services.vocabulary_service import VocabularyService

logger = logging.getLogger(__name__)


class ServicesMiddleware(BaseMiddleware):
    """Wires repositories → services for each update and injects the services."""

    def __init__(
        self,
        ai_provider: AIProvider,
        free_plan_daily_generations: int,
        broadcast_delay_ms: int,
        # --- Referral & Coin economy ----------------------------------------
        referral_base_reward: int,
        referral_increment: int,
        referral_max_reward: int,
        premium_daily_cost: int,
        welcome_referral_bonus: int,
        top_referrers_limit: int,
        bot_username: str,
    ) -> None:
        self._ai_provider = ai_provider
        self._is_gateway = isinstance(ai_provider, AIGateway)
        self._free_plan_daily_generations = free_plan_daily_generations
        self._broadcast_delay_ms = broadcast_delay_ms
        self._referral_base_reward = referral_base_reward
        self._referral_increment = referral_increment
        self._referral_max_reward = referral_max_reward
        self._premium_daily_cost = premium_daily_cost
        self._welcome_referral_bonus = welcome_referral_bonus
        self._top_referrers_limit = top_referrers_limit
        self._bot_username = bot_username

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session: AsyncSession = data["session"]

        # ── Repositories ─────────────────────────────────────────────── #
        user_repo = UserRepository(session)
        settings_repo = UserSettingsRepository(session)
        mnemonic_repo = MnemonicRepository(session)
        feedback_repo = MnemonicFeedbackRepository(session)
        analytics_repo = AnalyticsRepository(session)
        coin_repo = CoinRepository(session)
        referral_repo = ReferralRepository(session)
        vocabulary_repo = VocabularyRepository(session)  # V1.6

        # ── Resolve AI provider (tier-aware for gateway mode) ─────────── #
        if self._is_gateway:
            is_premium = await self._resolve_premium(
                data, user_repo, settings_repo
            )
            effective_provider = self._ai_provider.for_tier(is_premium)  # type: ignore[union-attr]
        else:
            effective_provider = self._ai_provider

        # ── Core services ─────────────────────────────────────────────── #
        data["user_service"] = UserService(user_repo, settings_repo)
        data["settings_service"] = SettingsService(user_repo, settings_repo)
        data["mnemonic_service"] = MnemonicService(effective_provider, mnemonic_repo)
        data["feedback_service"] = MnemonicFeedbackService(
            user_repo, feedback_repo, mnemonic_repo
        )
        data["usage_service"] = UsageService(
            user_repo, settings_repo, daily_limit=self._free_plan_daily_generations
        )
        data["analytics_service"] = AnalyticsService(analytics_repo)
        data["broadcast_service"] = BroadcastService(
            user_repo, delay_ms=self._broadcast_delay_ms
        )

        # ── Coin & Referral services ──────────────────────────────────── #
        coin_service = CoinService(coin_repo)
        data["coin_service"] = coin_service
        data["referral_service"] = ReferralService(
            referral_repo=referral_repo,
            user_repo=user_repo,
            settings_repo=settings_repo,
            coin_service=coin_service,
            base_reward=self._referral_base_reward,
            increment=self._referral_increment,
            max_reward=self._referral_max_reward,
            welcome_bonus=self._welcome_referral_bonus,
            premium_daily_cost=self._premium_daily_cost,
            top_limit=self._top_referrers_limit,
            bot_username=self._bot_username,
        )

        # ── Vocabulary (V1.6 — My Vocabulary) ────────────────────────── #
        data["vocabulary_service"] = VocabularyService(vocabulary_repo)

        # ── AI Gateway (admin panel access; None in legacy mode) ──────── #
        data["ai_gateway"] = (
            self._ai_provider if self._is_gateway else None
        )

        return await handler(event, data)

    @staticmethod
    async def _resolve_premium(
        data: dict[str, Any],
        user_repo: UserRepository,
        settings_repo: UserSettingsRepository,
    ) -> bool:
        """Look up the current user's premium status for gateway tier routing.

        Returns False (free tier) when:
        - The update has no associated Telegram user (channel posts, etc.)
        - The user is not yet registered in the database (first /start)
        - Any DB error occurs (safe default: free tier)
        """
        tg_user: TelegramUser | None = data.get("event_from_user")
        if tg_user is None:
            return False
        try:
            user = await user_repo.get_by_telegram_id(tg_user.id)
            if user is None:
                return False
            user_settings = await settings_repo.get_by_user_id(user.id)
            return bool(user_settings and user_settings.is_premium)
        except Exception:
            logger.exception(
                "Failed to resolve premium status for telegram_id=%s — "
                "defaulting to free tier",
                tg_user.id,
            )
            return False
