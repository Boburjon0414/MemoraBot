"""Application composition root: wires config, database, AI provider,
middlewares, and handlers together, then starts long polling.

Kept intentionally free of business logic — this file's only job is to
construct objects and connect them.

Step 4: The bare `create_ai_provider()` call is replaced by
`PlatformContainer`, which owns every application-lifetime singleton
(AI gateway, future vector store, document processor pool, etc.).
`ServicesMiddleware` now receives `platform` instead of a raw
`ai_provider`, and reads singletons from it.  The composition root
itself becomes simpler: start → initialize → poll → shutdown.
"""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database import models  # noqa: F401  (registers all models on Base.metadata)
from app.database.session import create_engine, create_session_maker, init_models
from app.handlers import get_root_router
from app.handlers.errors import handle_unexpected_error
from app.logging_config import setup_logging
from app.middlewares.db_session import DbSessionMiddleware
from app.middlewares.services import ServicesMiddleware
from app.platform import PlatformContainer  # Step 4

logger = logging.getLogger(__name__)


async def main() -> None:
    """Build every component and start polling Telegram for updates."""
    setup_logging(settings.log_level)
    logger.info("Starting MemoraBot…")

    # ── Database ────────────────────────────────────────────────────────── #
    engine = create_engine(settings.database_url)
    await init_models(engine)
    session_maker = create_session_maker(engine)
    logger.info("Database ready at %s", settings.database_url)

    # ── Platform singletons (Step 4) ────────────────────────────────────── #
    # PlatformContainer owns every application-lifetime resource.
    # initialize() constructs them in dependency order.
    # shutdown() closes them in reverse order inside the finally block.
    platform = PlatformContainer(settings)
    await platform.initialize()

    # ── Telegram bot & dispatcher ───────────────────────────────────────── #
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())

    dispatcher.update.middleware(DbSessionMiddleware(session_maker))
    dispatcher.update.middleware(
        ServicesMiddleware(
            platform=platform,                    # Step 4: was bare ai_provider
            free_plan_daily_generations=settings.free_plan_daily_generations,
            broadcast_delay_ms=settings.broadcast_delay_ms,
            referral_base_reward=settings.referral_base_reward,
            referral_increment=settings.referral_increment,
            referral_max_reward=settings.referral_max_reward,
            premium_daily_cost=settings.premium_daily_cost,
            welcome_referral_bonus=settings.welcome_referral_bonus,
            top_referrers_limit=settings.top_referrers_limit,
            bot_username=settings.bot_username,
        )
    )
    dispatcher.errors.register(handle_unexpected_error)

    dispatcher.include_router(get_root_router())

    await bot.delete_webhook(drop_pending_updates=True)

    # ── Polling loop ────────────────────────────────────────────────────── #
    try:
        logger.info("MemoraBot is polling for updates.")
        await dispatcher.start_polling(bot)
    finally:
        # Shut down in reverse-dependency order.
        await engine.dispose()
        await bot.session.close()
        await platform.shutdown()  # closes AI Gateway + future singletons
