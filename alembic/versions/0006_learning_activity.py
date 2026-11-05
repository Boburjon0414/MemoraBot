"""Learning activity event log

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-26

What this migration adds
------------------------
One new table: `learning_activities`

This is an immutable, append-only event log of every action a user
takes that represents learning (mnemonic generation, vocabulary saves,
quiz answers, AI chat messages, etc.).

It is the single source of truth for:
  - Statistics dashboard (counts by type / period)
  - Streak tracking (consecutive active calendar days)
  - Achievement engine (threshold checks: "100 words generated")
  - Weekly report (aggregate over last 7 days)
  - Adaptive difficulty (future: sequence analysis)

All foreign key columns are nullable so that:
  1. The migration runs cleanly today (content_sources table does not
     exist yet — the FK will be added in migration 0007).
  2. Referenced entities can be soft-deleted without removing the
     historical event record.

Rollback
--------
  `alembic downgrade 0005` drops `learning_activities` and its indexes.
  No existing data is modified in either direction.

Existing installs
-----------------
  Run `alembic upgrade head`.  No existing rows are touched.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_activities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        # ── Who ──────────────────────────────────────────────────────────── #
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # ── What ─────────────────────────────────────────────────────────── #
        sa.Column("activity_type", sa.String(length=64), nullable=False),

        # ── Optional entity references (all nullable) ─────────────────────── #
        sa.Column(
            "mnemonic_id",
            sa.Integer(),
            sa.ForeignKey("mnemonic_history.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "vocabulary_entry_id",
            sa.Integer(),
            sa.ForeignKey("vocabulary_entries.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # content_source_id: no FK constraint yet — content_sources table
        # is created in migration 0007.  The column exists now so that rows
        # written after Step 5 can reference sources from day one without
        # requiring a backfill.
        sa.Column("content_source_id", sa.Integer(), nullable=True),

        # ── Result data ───────────────────────────────────────────────────── #
        sa.Column("outcome", sa.String(length=32), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),

        # ── Timestamp ────────────────────────────────────────────────────── #
        sa.Column(
            "occurred_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── Indexes ──────────────────────────────────────────────────────────── #
    # user_id: all per-user queries filter on this first.
    op.create_index("ix_learning_activities_user_id", "learning_activities", ["user_id"])

    # activity_type: GROUP BY queries for summary and achievement checks.
    op.create_index(
        "ix_learning_activities_activity_type", "learning_activities", ["activity_type"]
    )

    # occurred_at: all time-windowed queries (streak, summary since X, weekly report).
    op.create_index(
        "ix_learning_activities_occurred_at", "learning_activities", ["occurred_at"]
    )

    # mnemonic_id: future "which activities referenced this mnemonic" lookups.
    op.create_index(
        "ix_learning_activities_mnemonic_id", "learning_activities", ["mnemonic_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_learning_activities_mnemonic_id", table_name="learning_activities")
    op.drop_index("ix_learning_activities_occurred_at", table_name="learning_activities")
    op.drop_index("ix_learning_activities_activity_type", table_name="learning_activities")
    op.drop_index("ix_learning_activities_user_id", table_name="learning_activities")
    op.drop_table("learning_activities")
