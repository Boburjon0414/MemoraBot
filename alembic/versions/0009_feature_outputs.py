"""Generic AI-generated artifact store

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-27

What this migration adds
------------------------
One new table: `feature_outputs`

Single table for every AI-generated learning artifact: quizzes, flashcard
sets, summaries, Q&A sessions, AI chat sessions, presentation outlines.

New artifact types are added by extending the OutputType enum (stored as
a plain String — no migration required for new values) and defining a new
Pydantic payload schema. Zero new tables, zero new migrations per feature.

Rollback
--------
  `alembic downgrade 0008` drops `feature_outputs` and its indexes.
  No existing data is modified in either direction.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_outputs",

        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        # ── Ownership ────────────────────────────────────────────────── #
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # ── Type + optional source link ───────────────────────────────── #
        sa.Column("output_type", sa.String(length=64), nullable=False),
        sa.Column(
            "content_source_id",
            sa.Integer(),
            sa.ForeignKey("content_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),

        # ── Display ───────────────────────────────────────────────────── #
        sa.Column("title", sa.String(length=512), nullable=True),

        # ── Payload ───────────────────────────────────────────────────── #
        sa.Column("payload_json", sa.Text(), nullable=False),

        # ── Lifecycle ─────────────────────────────────────────────────── #
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
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

    # user_id: all per-user list queries
    op.create_index(
        "ix_feature_outputs_user_id", "feature_outputs", ["user_id"]
    )
    # output_type: filtering "show me all my quizzes"
    op.create_index(
        "ix_feature_outputs_output_type", "feature_outputs", ["output_type"]
    )


def downgrade() -> None:
    op.drop_index("ix_feature_outputs_output_type", table_name="feature_outputs")
    op.drop_index("ix_feature_outputs_user_id", table_name="feature_outputs")
    op.drop_table("feature_outputs")
