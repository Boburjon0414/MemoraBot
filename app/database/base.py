"""Shared SQLAlchemy declarative base.

Every ORM model in `app.database.models` inherits from `Base`, so this is
also the single source of truth for `Base.metadata` used by both the V1
auto-create-on-startup bootstrap and by Alembic's autogenerate.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""
