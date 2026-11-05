"""The `user_memory` table: long-term learning profile for each user.

Design rationale
----------------
`user_settings` stores UI preferences (language, notifications).
`user_memory` stores *learning* preferences and progress:
  - What the user is trying to learn (english_level, learning_goal)
  - What language they think in (native_language — for mnemonic style)
  - What words they struggle with (weak_words_json)
  - What topics they study (topic_interests_json)
  - Their active topic right now (active_topic)

These fields power the `UserContext.to_prompt_block()` string that is
injected into every AI prompt, giving all AI features (chat, RAG Q&A,
quiz generation, mnemonic style selection) access to personalised context
without each service having to query for it separately.

1:1 relationship with users
----------------------------
Every user has exactly one `user_memory` row.  Created at registration by
`UserService.register_user()` for new users; created lazily on first access
by `UserMemoryService.get_or_create()` for users registered before Step 8.

weak_words_json schema
-----------------------
A JSON-encoded list of strings, capped at 50 entries (FIFO eviction).
Words are added by the Quiz system when the user answers incorrectly.
Used by `UserContext.to_prompt_block()` as "recently struggled with".

Example: '["ephemeral", "ubiquitous", "serendipity"]'

topic_interests_json schema
----------------------------
A JSON-encoded list of strings, capped at 20 entries.
Set explicitly by the user ("I'm studying for IELTS Academic") or inferred
from their most frequently looked-up word categories.

Example: '["academic vocabulary", "IELTS", "business English"]'
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.user import User

# Maximum number of weak words to retain (FIFO eviction beyond this)
MAX_WEAK_WORDS = 50
# Maximum number of topic interests to retain
MAX_TOPIC_INTERESTS = 20


class UserMemory(Base):
    """Long-term learning profile for one user.

    All fields except user_id are nullable — a freshly-created row is
    a blank slate that fills in as the user interacts with the platform.
    This means existing users who get a memory row created lazily have
    a valid (empty) profile immediately, without needing a backfill.
    """

    __tablename__ = "user_memory"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_memory_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership (1:1 with users) ─────────────────────────────────────── #
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Learning profile ───────────────────────────────────────────────── #
    english_level: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        # CEFR level: "A1" | "A2" | "B1" | "B2" | "C1" | "C2"
        # Set by the user via /settings or inferred from quiz performance.
    )
    learning_goal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        # Free-text goal: "IELTS", "business English", "daily conversation"
        # Short enough to inject verbatim into AI prompts.
    )
    native_language: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        # BCP-47 language code: "uz", "ru", "tr", "ar", …
        # Used to select mnemonic style (Uzbek pronunciation hints, etc.).
    )
    active_topic: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        # The topic the user is currently focused on.
        # Updated when they start a new study session or upload a document.
    )

    # ── Adaptive data (JSON lists) ─────────────────────────────────────── #
    weak_words_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        # JSON list[str], max MAX_WEAK_WORDS entries, FIFO eviction.
        # Added to by QuizService when the user answers incorrectly.
    )
    topic_interests_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        # JSON list[str], max MAX_TOPIC_INTERESTS entries.
        # Set by user or inferred from activity patterns.
    )

    # ── Timestamps ────────────────────────────────────────────────────── #
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

    # ── Relationship ───────────────────────────────────────────────────── #
    user: Mapped["User"] = relationship("User", back_populates="memory")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<UserMemory id={self.id} user_id={self.user_id} "
            f"level={self.english_level!r} goal={self.learning_goal!r}>"
        )
