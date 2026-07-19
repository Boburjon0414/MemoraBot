"""Application composition root: wires config, database, AI provider,
middlewares, and handlers together, then starts long polling.

Kept intentionally free of business logic — this file's only job is to
construct objects and connect them.
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
from app.services.ai.factory import create_ai_provider

logger = logging.getLogger(__name__)


async def main() -> None:
    """Build every component and start polling Telegram for updates."""
    setup_logging(settings.log_level)
    logger.info("Starting MemoraBot...")

    engine = create_engine(settings.database_url)
    await init_models(engine)
    session_maker = create_session_maker(engine)
    logger.info("Database ready at %s", settings.database_url)

    ai_provider = await create_ai_provider(settings)
    logger.info("Using AI provider: %s", ai_provider.name)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())

    dispatcher.update.middleware(DbSessionMiddleware(session_maker))
    dispatcher.update.middleware(
        ServicesMiddleware(
            ai_provider,
            free_plan_daily_generations=settings.free_plan_daily_generations,
            broadcast_delay_ms=settings.broadcast_delay_ms,
        )
    )
    dispatcher.errors.register(handle_unexpected_error)

    dispatcher.include_router(get_root_router())

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        logger.info("MemoraBot is polling for updates.")
        await dispatcher.start_polling(bot)
    finally:
        await engine.dispose()
        await bot.session.close()
