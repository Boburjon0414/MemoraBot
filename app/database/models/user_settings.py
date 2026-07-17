"""The `user_settings` table: per-user preferences and usage tracking (1:1 with `users`)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.user import User


class UserSettings(Base):
    """Preferences for a single user: UI language, notification opt-in, and
    (as of V1.2) free-plan AI generation usage.

    A row is created automatically the moment a user registers
    (see `UserService.register_user`), so it should always exist for any
    registered user.

    `ai_generations_used` counts only genuinely new AI generations (cache
    misses) against `settings.free_plan_generation_limit` — looking up a
    word that's already in the library is always free and never touches
    this counter. See `app.services.usage_service.UsageService`.
    """

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    preferred_language: Mapped[str] = mapped_column(String(8), default="uz", nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_generations_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="settings")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return f"<UserSettings user_id={self.user_id} language={self.preferred_language!r}>"
