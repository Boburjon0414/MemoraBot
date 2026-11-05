"""Content source ingestion anchor

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-27

What this migration adds
------------------------
One new table: `content_sources`

`content_sources` is the platform anchor for every feature that operates
on user-supplied content: RAG Q&A, quiz generation from a document, OCR,
summarisation, flashcard generation, and presentation outlines.

Adding a new content format (PDF, image, audio) requires only a new
ContentProcessor class — no further schema changes.

The `content_source_id` column that was added as a plain nullable Integer
in `learning_activities` (migration 0006) now has a real FK target.
SQLite does not retroactively enforce FK constraints on existing rows, so
no data repair is needed.

Rollback
--------
  `alembic downgrade 0006` drops `content_sources` and its indexes.
  No existing data is modified in either direction.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_sources",

        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        # ── Ownership ───────────────────────────────────────────────────── #
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # ── What the user provided ──────────────────────────────────────── #
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=True),
        sa.Column("raw_storage_key", sa.String(length=512), nullable=True),

        # ── What the system extracted ───────────────────────────────────── #
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),

        # ── Processing state ────────────────────────────────────────────── #
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),

        # ── Display ─────────────────────────────────────────────────────── #
        sa.Column("title", sa.String(length=512), nullable=True),

        # ── Timestamps ──────────────────────────────────────────────────── #
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
    )

    # ── Indexes ──────────────────────────────────────────────────────────── #
    # user_id: every per-user list query filters on this.
    op.create_index(
        "ix_content_sources_user_id", "content_sources", ["user_id"]
    )
    # status: filtering by "ready" / "pending" for processing queues.
    op.create_index(
        "ix_content_sources_status", "content_sources", ["status"]
    )


def downgrade() -> None:
    op.drop_index("ix_content_sources_status", table_name="content_sources")
    op.drop_index("ix_content_sources_user_id", table_name="content_sources")
    op.drop_table("content_sources")
