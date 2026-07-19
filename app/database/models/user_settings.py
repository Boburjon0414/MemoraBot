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
    free-plan AI generation usage tracking.

    A row is created automatically the moment a user registers
    (see `UserService.register_user`), so it should always exist for any
    registered user.

    Daily quota fields (V1.3):
    - `daily_generation_count`: how many new AI generations this user has
      consumed in the current 24-hour window. Resets to 0 automatically
      at request time once 24 hours have elapsed since `last_daily_reset`.
    - `last_daily_reset`: the UTC timestamp of the most recent quota reset
      (or account creation for new users). Used to detect when 24 hours
      have passed and a reset is due.
    - `is_premium`: when True, the daily quota is completely bypassed.

    `ai_generations_used` (V1.2 legacy) is kept for historical audit
    purposes only — it is no longer read by `UsageService`.
    """

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    preferred_language: Mapped[str] = mapped_column(String(8), default="uz", nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # V1.2 legacy lifetime counter — kept for audit history, not read by UsageService.
    ai_generations_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # V1.3 daily quota fields.
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    daily_generation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_daily_reset: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="settings")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return (
            f"<UserSettings user_id={self.user_id} language={self.preferred_language!r} "
            f"is_premium={self.is_premium} daily_count={self.daily_generation_count}>"
        )
