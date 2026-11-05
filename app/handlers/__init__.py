"""Composes every feature router into one root router.

Registration order matters: `start` must come before `mnevoca` so that
`/start` always wins and resets FSM state even mid-flow, and `fallback`
must come last so specific handlers always get first refusal.
"""

from __future__ import annotations

from aiogram import Router

from app.handlers import (
    about, admin, admin_grammar, ai_chat, ai_gateway_admin, dashboard,
    fallback, grammar, mnevoca, pronunciation, quiz, referral, settings, start, vocabulary,
)


def get_root_router() -> Router:
    """Build and return the single router that `app.bot` includes into the Dispatcher."""
    root = Router(name="root")
    root.include_router(start.router)
    root.include_router(admin.router)
    root.include_router(ai_gateway_admin.router)
    root.include_router(referral.router)
    root.include_router(dashboard.router)
    root.include_router(ai_chat.router)             # Feature A: AI Chat
    root.include_router(quiz.router)                # Feature C: Quiz
    root.include_router(grammar.router)             # Feature: Learn → Grammar
    root.include_router(admin_grammar.router)       # Feature: Admin Grammar Lessons
    root.include_router(mnevoca.router)
    root.include_router(pronunciation.router)
    root.include_router(vocabulary.router)
    root.include_router(settings.router)
    root.include_router(about.router)
    root.include_router(fallback.router)
    return root
