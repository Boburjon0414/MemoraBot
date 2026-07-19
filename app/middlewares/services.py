"""Middleware that builds repositories and services for the current session
and injects them into the handler's data — MemoraBot's dependency-injection
mechanism (no external DI framework needed for this project's scope).

Handlers simply declare a parameter like `user_service: UserService` and
aiogram passes the already-constructed instance in automatically.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.mnemonic_feedback_repository import MnemonicFeedbackRepository
from app.repositories.mnemonic_repository import MnemonicRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository
from app.services.ai.base import AIProvider
from app.services.analytics_service import AnalyticsService
from app.services.broadcast_service import BroadcastService
from app.services.mnemonic_feedback_service import MnemonicFeedbackService
from app.services.mnemonic_service import MnemonicService
from app.services.settings_service import SettingsService
from app.services.usage_service import UsageService
from app.services.user_service import UserService


class ServicesMiddleware(BaseMiddleware):
    """Wires repositories -> services for each update and injects the services."""

    def __init__(
        self,
        ai_provider: AIProvider,
        free_plan_daily_generations: int,
        broadcast_delay_ms: int,
    ) -> None:
        self._ai_provider = ai_provider
        self._free_plan_daily_generations = free_plan_daily_generations
        self._broadcast_delay_ms = broadcast_delay_ms

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session: AsyncSession = data["session"]

        user_repo = UserRepository(session)
        settings_repo = UserSettingsRepository(session)
        mnemonic_repo = MnemonicRepository(session)
        feedback_repo = MnemonicFeedbackRepository(session)
        analytics_repo = AnalyticsRepository(session)

        data["user_service"] = UserService(user_repo, settings_repo)
        data["settings_service"] = SettingsService(user_repo, settings_repo)
        data["mnemonic_service"] = MnemonicService(self._ai_provider, mnemonic_repo)
        data["feedback_service"] = MnemonicFeedbackService(user_repo, feedback_repo, mnemonic_repo)
        data["usage_service"] = UsageService(
            user_repo, settings_repo, daily_limit=self._free_plan_daily_generations
        )
        data["analytics_service"] = AnalyticsService(analytics_repo)
        data["broadcast_service"] = BroadcastService(
            user_repo, delay_ms=self._broadcast_delay_ms
        )

        return await handler(event, data)
