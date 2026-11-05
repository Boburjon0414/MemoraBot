"""Grammar Learning System

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-11

What this migration adds
------------------------
Two new tables:

1. `grammar_topics`
   One row per grammar lesson topic (e.g. "Present Perfect").
   Rows are seeded by the bot owner.  Handlers always query this table
   rather than hardcoding topic lists.

   Key columns:
     - slug              URL-safe identifier ("present_perfect")
     - title             Display name shown to users
     - description       Short description injected into AI prompts
     - channel_message_id  Telegram message ID in the grammar channel
     - difficulty        CEFR level (A1 … C2, or NULL)
     - order_index       Controls display order in the topic keyboard
     - is_active         Soft-disable without deleting progress data

2. `user_grammar_progress`
   One row per (user, topic) pair.  Created on first lesson open.
   Never deleted — tracks lifetime study history.

   Key columns:
     - status            "in_progress" | "completed"
     - lessons_opened    incremented each time the lesson is viewed
     - questions_answered / questions_correct / questions_wrong
     - last_score        accuracy of most recent quiz session
     - mastery_score     composite mastery in [0.0, 1.0]
     - last_studied_at   used to answer "most recently studied topics"

   The `mastery_score` is computed deterministically by GrammarService
   — never by AI.  The status field is what drives "completed" badges.

Indexes
-------
- ix_grammar_topics_slug         (unique — for slug lookup)
- ix_grammar_topics_is_active    (for list_active() query)
- ix_ugp_user_id                 (per-user progress lookup)
- ix_ugp_topic_id                (per-topic aggregate queries)
- ix_ugp_user_last_studied       (most recently studied topics sort)
- uq_user_grammar_progress_user_topic  (prevents duplicate rows)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. grammar_topics ─────────────────────────────────────────────── #
    op.create_table(
        "grammar_topics",

        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        # ── Identity ─────────────────────────────────────────────────── #
        sa.Column("slug",        sa.String(length=64),  nullable=False),
        sa.Column("title",       sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(),             nullable=True),

        # ── Telegram channel link ─────────────────────────────────────── #
        sa.Column("channel_message_id", sa.Integer(), nullable=False, server_default="0"),

        # ── Classification ────────────────────────────────────────────── #
        sa.Column("difficulty",   sa.String(length=8), nullable=True),
        sa.Column("order_index",  sa.Integer(),        nullable=False, server_default="0"),

        # ── Lifecycle ─────────────────────────────────────────────────── #
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_index(
        "ix_grammar_topics_slug",
        "grammar_topics",
        ["slug"],
        unique=True,
    )
    op.create_index(
        "ix_grammar_topics_is_active",
        "grammar_topics",
        ["is_active"],
        unique=False,
    )

    # ── 2. user_grammar_progress ──────────────────────────────────────── #
    op.create_table(
        "user_grammar_progress",

        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        # ── Ownership ─────────────────────────────────────────────────── #
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "grammar_topic_id",
            sa.Integer(),
            sa.ForeignKey("grammar_topics.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # ── Status ────────────────────────────────────────────────────── #
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="in_progress",
        ),

        # ── Activity counters ─────────────────────────────────────────── #
        sa.Column("lessons_opened",      sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions_answered",  sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions_correct",   sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions_wrong",     sa.Integer(), nullable=False, server_default="0"),

        # ── Mastery ───────────────────────────────────────────────────── #
        sa.Column("last_score",    sa.Float(), nullable=True),
        sa.Column(
            "mastery_score",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),

        # ── Timestamps ────────────────────────────────────────────────── #
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "last_studied_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),

        # ── Constraints ───────────────────────────────────────────────── #
        sa.UniqueConstraint(
            "user_id",
            "grammar_topic_id",
            name="uq_user_grammar_progress_user_topic",
        ),
    )

    op.create_index("ix_ugp_user_id",    "user_grammar_progress", ["user_id"],           unique=False)
    op.create_index("ix_ugp_topic_id",   "user_grammar_progress", ["grammar_topic_id"],  unique=False)
    op.create_index(
        "ix_ugp_user_last_studied",
        "user_grammar_progress",
        ["user_id", "last_studied_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_ugp_user_last_studied", table_name="user_grammar_progress")
    op.drop_index("ix_ugp_topic_id",          table_name="user_grammar_progress")
    op.drop_index("ix_ugp_user_id",           table_name="user_grammar_progress")
    op.drop_table("user_grammar_progress")

    op.drop_index("ix_grammar_topics_is_active", table_name="grammar_topics")
    op.drop_index("ix_grammar_topics_slug",      table_name="grammar_topics")
    op.drop_table("grammar_topics")
