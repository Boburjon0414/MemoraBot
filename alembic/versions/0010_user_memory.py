"""User long-term learning profile

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-27

What this migration adds
------------------------
One new table: `user_memory`

One row per user (1:1 with `users`).  Stores the learning profile fields
that power personalised AI prompts:
  - english_level, learning_goal, native_language (set by user / inferred)
  - active_topic (last studied topic)
  - weak_words_json (JSON list — updated by quiz wrong answers)
  - topic_interests_json (JSON list — updated from activity patterns)

All columns are nullable so:
  1. The migration runs cleanly against existing user rows (no backfill).
  2. New rows created lazily (get_or_create) have a valid empty profile.
  3. Existing users get their row on next access — no one-time migration script.

Rollback
--------
  `alembic downgrade 0009` drops `user_memory`.
  No existing data in any other table is modified.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_memory",

        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        # ── Ownership ───────────────────────────────────────────────────── #
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),

        # ── Learning profile ────────────────────────────────────────────── #
        sa.Column("english_level", sa.String(length=8), nullable=True),
        sa.Column("learning_goal", sa.String(length=255), nullable=True),
        sa.Column("native_language", sa.String(length=8), nullable=True),
        sa.Column("active_topic", sa.String(length=255), nullable=True),

        # ── Adaptive data (JSON lists) ───────────────────────────────────── #
        sa.Column("weak_words_json", sa.Text(), nullable=True),
        sa.Column("topic_interests_json", sa.Text(), nullable=True),

        # ── Timestamps ──────────────────────────────────────────────────── #
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # user_id: primary lookup path; unique enforced by UniqueConstraint
    op.create_index("ix_user_memory_user_id", "user_memory", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_memory_user_id", table_name="user_memory")
    op.drop_table("user_memory")
