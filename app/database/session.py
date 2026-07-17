"""Async SQLAlchemy engine/session-maker setup, plus the V1 auto-bootstrap
that creates all tables on first launch without requiring a manual Alembic
migration step.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.base import Base


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create the async SQLAlchemy engine for the given database URL."""
    return create_async_engine(database_url, echo=echo, future=True)


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to `engine`.

    `expire_on_commit=False` so ORM objects (e.g. a freshly created `User`)
    remain usable after the enclosing session commits, without triggering a
    lazy-load on already-loaded attributes.
    """
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_models(engine: AsyncEngine) -> None:
    """Create all tables that don't already exist.

    This is what satisfies the V1 "auto-create the database on first launch"
    requirement. It is idempotent — safe to call on every startup, including
    against a database that already has the tables. For evolving the schema
    later (adding columns, new tables, etc.), see the Alembic setup in
    `alembic/` and the note about `alembic stamp` in the README.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
