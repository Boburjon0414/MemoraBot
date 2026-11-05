"""The `grammar_topics` table: configurable repository of grammar lesson topics.

Design rationale
----------------
Grammar topics are not hardcoded in handlers.  They live in the database so
new topics can be added (or deactivated) without any Python changes.

`channel_message_id` links each topic to the specific message in the owner's
Telegram channel that contains the lesson.  When the user opens a lesson,
the bot forwards/copies that channel message — the channel is the source of
truth for lesson content, not the AI.

`order_index` controls the display order in the topic selection keyboard.

`difficulty` maps to a CEFR tier so the bot can show appropriate topics to
users at different levels.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.user_grammar_progress import UserGrammarProgress


class GrammarTopic(Base):
    """One grammar lesson topic (e.g. 'Present Perfect').

    Rows are seeded by the bot owner via admin commands or a fixture script.
    Handlers never hardcode topic lists — they always query this table.
    """

    __tablename__ = "grammar_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Identity ───────────────────────────────────────────────────────── #
    slug: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        # URL-safe identifier: "present_perfect", "past_simple", ...
        # Used in callback_data and logging.
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        # Human-readable grammar topic name: "Present Perfect"
        # Also used as fallback when button_name is not set.
    )
    button_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        # Text shown on the Telegram inline keyboard button.
        # Example: "🟢 Present Perfect"
        # Falls back to `title` if NULL.
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        # Short description injected into AI context when the user opens this topic.
        # Example: "Present Perfect: has/have + past participle. Used for past
        # actions with present relevance, life experiences, and recent events."
    )

    # ── Telegram channel link ──────────────────────────────────────────── #
    # channel_message_id is the message ID within GRAMMAR_CHANNEL_ID.
    # 0 (default) means "no channel lesson yet" — the bot will show an error.
    channel_message_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ── Classification ─────────────────────────────────────────────────── #
    difficulty: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        # CEFR level: "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | None
        # Used to filter appropriate topics for each user's level.
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        # Lower values appear first in the keyboard.
    )

    # ── Lifecycle ──────────────────────────────────────────────────────── #
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        # Inactive topics are hidden from the keyboard but not deleted.
        # Allows disabling a topic temporarily without losing progress data.
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────── #
    user_progress: Mapped[list["UserGrammarProgress"]] = relationship(
        "UserGrammarProgress",
        back_populates="topic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<GrammarTopic id={self.id} slug={self.slug!r} "
            f"title={self.title!r} active={self.is_active}>"
        )
