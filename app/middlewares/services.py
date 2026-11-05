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

from app.platform import PlatformContainer  # Step 4
from app.repositories.activity_repository import ActivityRepository  # Step 1
from app.repositories.feature_output_repository import FeatureOutputRepository  # Step 7
from app.repositories.content_chunk_repository import ContentChunkRepository  # Step 6
from app.repositories.user_memory_repository import UserMemoryRepository        # Step 8
from app.repositories.content_repository import ContentRepository  # Step 5
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.coin_repository import CoinRepository
from app.repositories.mnemonic_feedback_repository import MnemonicFeedbackRepository
from app.repositories.mnemonic_repository import MnemonicRepository
from app.repositories.referral_repository import ReferralRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.services.ai.base import MnemonicProvider
from app.services.ai.gateway import AIGateway
from app.services.ai.router import AIRouter
from app.services.activity_service import ActivityService  # Step 1
from app.services.analytics_service import AnalyticsService
from app.services.feature_output_service import FeatureOutputService  # Step 7
from app.services.quiz_service import QuizService                      # Feature C
from app.services.user_memory_service import UserMemoryService          # Step 8
from app.services.content.content_service import ContentService  # Step 5
from app.services.content.embedding_store import SQLiteEmbeddingStore  # Step 6
from app.services.context.context_builder import ContextBuilder   # Feature A (AI Core)
from app.services.context.memory_update_hook import MemoryUpdateHook  # Feature A (AI Core)
from app.services.context.user_context_service import UserContextService  # Step 2
from app.services.tools.base import ToolContext                    # Feature A.2
from app.services.tools.planner import AIPlanner                   # Feature A.2
from app.services.tools.response_validator import ResponseValidator # Feature A.2
from app.services.broadcast_service import BroadcastService
from app.services.coin_service import CoinService
from app.services.mnemonic_feedback_service import MnemonicFeedbackService
from app.services.mnemonic_service import MnemonicService
from app.services.referral_service import ReferralService
from app.services.settings_service import SettingsService
from app.services.usage_service import UsageService
from app.services.user_service import UserService
from app.services.pronunciation_service import PronunciationService
from app.services.vocabulary_service import VocabularyService
from app.repositories.grammar_topic_repository import GrammarTopicRepository        # Feature: Grammar
from app.repositories.user_grammar_progress_repository import UserGrammarProgressRepository  # Feature: Grammar
from app.services.grammar_service import GrammarService                              # Feature: Grammar

logger = logging.getLogger(__name__)


class ServicesMiddleware(BaseMiddleware):
    """Wires repositories → services for each update and injects the services.

    Receives application-lifetime singletons from `PlatformContainer` (Step 4)
    rather than constructing them itself.  Per-request objects (repositories,
    session-scoped services) are still built fresh in `__call__`.
    """

    def __init__(
        self,
        platform: PlatformContainer,       # Step 4: replaces bare ai_provider arg
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
        self._platform = platform
        # Read singletons once at middleware construction (startup) — cheap
        # attribute reads after PlatformContainer.initialize() has completed.
        self._ai_provider: MnemonicProvider = platform.ai_provider
        self._is_gateway: bool = platform.is_gateway_mode
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
        activity_repo = ActivityRepository(session)      # Step 1
        content_repo = ContentRepository(session)        # Step 5
        chunk_repo = ContentChunkRepository(session)     # Step 6
        feature_output_repo = FeatureOutputRepository(session)  # Step 7
        memory_repo = UserMemoryRepository(session)      # Step 8
        grammar_topic_repo = GrammarTopicRepository(session)           # Feature: Grammar
        grammar_progress_repo = UserGrammarProgressRepository(session) # Feature: Grammar

        # ── Resolve AI provider (tier-aware for gateway mode) ─────────── #
        if self._is_gateway:
            is_premium = await self._resolve_premium(
                data, user_repo, settings_repo
            )
            effective_provider = self._ai_provider.for_tier(is_premium)  # type: ignore[union-attr]
        else:
            effective_provider = self._ai_provider

        # ── Core services ─────────────────────────────────────────────── #
        data["user_service"] = UserService(
            user_repo=user_repo,
            settings_repo=settings_repo,
            memory_repo=memory_repo,                  # Step 8
        )
        data["pronunciation_service"] = PronunciationService()
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

        # ── Activity log (Step 1) ─────────────────────────────────────── #
        activity_service = ActivityService(activity_repo)
        data["activity_service"] = activity_service

        # ── Learning memory (Step 8) ──────────────────────────────────── #
        memory_service = UserMemoryService(memory_repo)
        data["user_memory_service"] = memory_service

        # ── AI Core: ContextBuilder + MemoryUpdateHook (Feature A) ────── #
        context_builder = ContextBuilder(
            activity_repo=activity_repo,
            feature_output_repo=feature_output_repo,
            vocabulary_repo=vocabulary_repo,
        )
        data["context_builder"] = context_builder
        data["memory_update_hook"] = MemoryUpdateHook(memory_service)

        # ── Tool Calling Layer (Feature A.2) ──────────────────────────── #
        tool_context = ToolContext(
            user_id=0,                              # filled per-request in handlers
            user_context=None,                      # type: ignore — filled per-request
            activity_repo=activity_repo,
            vocabulary_repo=vocabulary_repo,
            feature_output_repo=feature_output_repo,
            memory_repo=memory_repo,
            content_repo=content_repo,
            content_chunk_repo=chunk_repo,
            activity_service=activity_service,
            grammar_topic_repo=grammar_topic_repo,           # Feature: Grammar
            grammar_progress_repo=grammar_progress_repo,     # Feature: Grammar
            embedder=self._platform.embedder,
            embedding_store=SQLiteEmbeddingStore(session),
        )
        data["tool_context_template"] = tool_context   # handlers stamp user_id/user_context
        data["ai_planner"] = AIPlanner(self._platform.tool_registry)
        data["response_validator"] = ResponseValidator()

        # ── Per-request learning context (Steps 2 + 8) ───────────────── #
        # UserContextService now reads from user_memory (english_level,
        # learning_goal, weak_words, active_topic) in addition to the
        # existing settings/vocab/streak queries.
        data["user_context_service"] = UserContextService(
            settings_repo=settings_repo,
            vocabulary_repo=vocabulary_repo,
            activity_service=activity_service,
            memory_repo=memory_repo,                  # Step 8
        )

        # ── AI Gateway (admin panel access; None in legacy mode) ──────── #
        data["ai_gateway"] = (
            self._ai_provider if self._is_gateway else None
        )

        # ── AI Router (Step 3) — generic interface for all AI features ─── #
        data["ai_router"] = self._platform.ai_router

        # ── Content ingestion pipeline (Steps 5 & 6) ─────────────────── #
        embedding_store = SQLiteEmbeddingStore(session)   # Step 6
        data["content_service"] = ContentService(
            content_repo=content_repo,
            processor_registry=self._platform.content_processor_registry,
            chunk_repo=chunk_repo,                        # Step 6
            embedder=self._platform.embedder,             # Step 6
            embedding_store=embedding_store,              # Step 6
        )

        # ── Generic artifact store (Step 7) ───────────────────────────── #
        data["feature_output_service"] = FeatureOutputService(feature_output_repo)

        # ── Grammar Learning service (Feature: Learn → Grammar) ──────────── #
        grammar_service = GrammarService(
            grammar_topic_repo=grammar_topic_repo,
            grammar_progress_repo=grammar_progress_repo,
            activity_service=activity_service,
        )
        data["grammar_service"] = grammar_service
        data["grammar_topic_repo"] = grammar_topic_repo

        # ── Quiz service (Feature C) ───────────────────────────────────── #
        data["quiz_service"] = QuizService(
            ai_router=self._platform.ai_router,
            feature_output_service=FeatureOutputService(feature_output_repo),
            planner=AIPlanner(self._platform.tool_registry) if self._platform.ai_router else None,
            quiz_open_period=self._platform.settings.quiz_open_period,
            quiz_vocabulary_questions=self._platform.settings.quiz_vocabulary_questions,
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
