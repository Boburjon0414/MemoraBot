"""Self-improving mnemonic library + CEFR difficulty + free-plan quota

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-14

Three things happen here:

1. New statistics columns on `mnemonic_history` (uses, last_used_at, likes,
   dislikes, average_rating, regenerated_count, is_active, response_time_ms,
   prompt_version) so the library can serve the highest-rated active version
   of a word instead of just the most recent one.

2. `difficulty` moves from the old easy/medium/hard scale to CEFR (A1-C2),
   per app/knowledge/v1/RESPONSE_SPECIFICATION.md. Existing rows are
   reclassified rather than left inconsistent: easy->A2, medium->B1,
   hard->C1. This is a one-time best-effort remap (the old 3-bucket scale
   can't be losslessly expanded to 6 buckets) — historical rows are kept,
   not deleted, exactly as the "preserve historical data" principle requires.

3. `likes`/`dislikes`/`average_rating` are backfilled from any ratings that
   already exist in `mnemonic_feedback`, so real historical feedback isn't
   silently zeroed out by the new denormalized counters.

4. `user_settings.ai_generations_used` for the free-plan quota.

V1 still auto-creates new columns/tables on startup via `metadata.create_all`
for brand-new installs, but `metadata.create_all` does NOT alter existing
tables — an existing database (like a live bot's) needs this migration run
explicitly:

    alembic upgrade head

(or, if you've never run Alembic against this database before: `alembic
stamp 0002` first, then `alembic upgrade head`.)

This exact SQL (the ADD COLUMN + UPDATE statements below) was test-run
against a copy of a real production `memorabot.db` before this migration
was written up — see docs/MNEMONIC_LIBRARY.md for the verified before/after.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. New statistics columns on mnemonic_history ----------------------
    op.add_column(
        "mnemonic_history", sa.Column("uses", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("mnemonic_history", sa.Column("last_used_at", sa.DateTime(), nullable=True))
    op.add_column(
        "mnemonic_history", sa.Column("likes", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "mnemonic_history", sa.Column("dislikes", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "mnemonic_history",
        sa.Column("average_rating", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "mnemonic_history",
        sa.Column("regenerated_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "mnemonic_history",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("mnemonic_history", sa.Column("response_time_ms", sa.Integer(), nullable=True))
    op.add_column(
        "mnemonic_history",
        sa.Column("prompt_version", sa.String(length=16), nullable=False, server_default="v1"),
    )
    op.create_index("ix_mnemonic_history_is_active", "mnemonic_history", ["is_active"])

    # --- 2. Backfill uses/last_used_at for rows that existed before this column did
    op.execute("UPDATE mnemonic_history SET uses = 1 WHERE uses = 0")
    op.execute("UPDATE mnemonic_history SET last_used_at = created_at WHERE last_used_at IS NULL")

    # --- 3. Reclassify difficulty: easy/medium/hard -> CEFR A1-C2 -----------
    op.execute("UPDATE mnemonic_history SET difficulty = 'A2' WHERE difficulty = 'easy'")
    op.execute("UPDATE mnemonic_history SET difficulty = 'B1' WHERE difficulty = 'medium'")
    op.execute("UPDATE mnemonic_history SET difficulty = 'C1' WHERE difficulty = 'hard'")

    # --- 4. Backfill likes/dislikes/average_rating from existing feedback ---
    op.execute(
        """
        UPDATE mnemonic_history
        SET likes = COALESCE(
            (SELECT COUNT(*) FROM mnemonic_feedback
             WHERE mnemonic_feedback.mnemonic_history_id = mnemonic_history.id
               AND mnemonic_feedback.is_helpful = 1),
            0
        )
        """
    )
    op.execute(
        """
        UPDATE mnemonic_history
        SET dislikes = COALESCE(
            (SELECT COUNT(*) FROM mnemonic_feedback
             WHERE mnemonic_feedback.mnemonic_history_id = mnemonic_history.id
               AND mnemonic_feedback.is_helpful = 0),
            0
        )
        """
    )
    op.execute(
        """
        UPDATE mnemonic_history
        SET average_rating = CAST(likes - dislikes AS REAL) / MAX(1, likes + dislikes)
        """
    )

    # --- 5. Free-plan quota tracking on user_settings -----------------------
    op.add_column(
        "user_settings", sa.Column("ai_generations_used", sa.Integer(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    op.drop_column("user_settings", "ai_generations_used")

    # Difficulty reclassification is one-way (A2/B1/C1 -> easy/medium/hard
    # would lose the A1/B2/C2 distinctions if any were ever assigned by a
    # newer prompt version); left as CEFR on downgrade rather than guessing.

    op.drop_index("ix_mnemonic_history_is_active", table_name="mnemonic_history")
    op.drop_column("mnemonic_history", "prompt_version")
    op.drop_column("mnemonic_history", "response_time_ms")
    op.drop_column("mnemonic_history", "is_active")
    op.drop_column("mnemonic_history", "regenerated_count")
    op.drop_column("mnemonic_history", "average_rating")
    op.drop_column("mnemonic_history", "dislikes")
    op.drop_column("mnemonic_history", "likes")
    op.drop_column("mnemonic_history", "last_used_at")
    op.drop_column("mnemonic_history", "uses")
