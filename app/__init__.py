"""MemoraBot — an AI-powered Telegram bot that helps English learners
permanently memorize vocabulary using Uzbek-sound mnemonics.

This package follows a layered, clean architecture:

    handlers      -> thin Telegram/aiogram glue, no business logic
    services      -> business logic, orchestrates repositories + AI providers
    repositories  -> async data-access layer (one per aggregate/entity)
    database      -> SQLAlchemy models, engine/session setup
    keyboards     -> inline/reply keyboard builders + callback-data factories
    states        -> aiogram FSM state groups
    middlewares   -> cross-cutting aiogram middlewares (DB session, DI)
    texts         -> localized (uz/en/ru) user-facing strings
    core          -> shared enums, exceptions
    utils         -> small, stateless helper functions
"""
