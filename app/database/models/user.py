"""The `users` table: registered Telegram users of MemoraBot."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.content_source import ContentSource  # Step 5
    from app.database.models.feature_output import FeatureOutput  # Step 7
    from app.database.models.learning_activity import LearningActivity
    from app.database.models.mnemonic_history import MnemonicHistory
    from app.database.models.user_memory import UserMemory           # Step 8
    from app.database.models.user_settings import UserSettings
    from app.database.models.vocabulary import VocabularyEntry  # V1.6


class User(Base):
    """A Telegram user who has completed registration (shared their contact)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    mnemonic_history: Mapped[list["MnemonicHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    vocabulary_entries: Mapped[list["VocabularyEntry"]] = relationship(  # V1.6
        back_populates="user", cascade="all, delete-orphan"
    )
    learning_activities: Mapped[list["LearningActivity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    content_sources: Mapped[list["ContentSource"]] = relationship(  # Step 5
        back_populates="user", cascade="all, delete-orphan"
    )
    feature_outputs: Mapped[list["FeatureOutput"]] = relationship(  # Step 7
        back_populates="user", cascade="all, delete-orphan"
    )
    memory: Mapped["UserMemory | None"] = relationship(             # Step 8
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return f"<User id={self.id} telegram_id={self.telegram_id} full_name={self.full_name!r}>"
