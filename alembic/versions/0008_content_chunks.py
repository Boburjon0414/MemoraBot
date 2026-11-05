"""Content chunk and embedding storage

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-27

What this migration adds
------------------------
One new table: `content_chunks`

Each row stores one text window from a ContentSource, along with its
position metadata (for citations) and its embedding vector as a
JSON-encoded float array.

The JSON approach is SQLite-compatible with no new dependencies.
The upgrade path to PostgreSQL + pgvector requires only a column type
change (`Text` → `VECTOR(n)`) and a replacement EmbeddingStore class
— no application logic changes.

Rollback
--------
  `alembic downgrade 0007` drops `content_chunks` and its index.
  ContentSource rows are unaffected; their chunk_count columns remain
  (with potentially stale counts — reset to 0 if re-indexing after rollback).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_chunks",

        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        # ── Source reference ────────────────────────────────────────────── #
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("content_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # ── Position ────────────────────────────────────────────────────── #
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),

        # ── Citation metadata ───────────────────────────────────────────── #
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),

        # ── Content ─────────────────────────────────────────────────────── #
        sa.Column("text", sa.Text(), nullable=False),

        # ── Embedding ───────────────────────────────────────────────────── #
        sa.Column("embedding_model", sa.String(length=128), nullable=True),
        sa.Column("embedding_json", sa.Text(), nullable=True),
    )

    # source_id: every search query filters on this first
    op.create_index(
        "ix_content_chunks_source_id", "content_chunks", ["source_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_content_chunks_source_id", table_name="content_chunks")
    op.drop_table("content_chunks")
