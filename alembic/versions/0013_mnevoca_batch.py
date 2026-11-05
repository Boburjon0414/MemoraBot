"""Add batch_id to mnemonic_history for MneVoca batch feature

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-16

What this migration adds
------------------------
One new nullable column on `mnemonic_history`:

  batch_id  VARCHAR(36)  NULL  (indexed)
    A UUID string that groups all MnemonicHistory rows produced by a single
    multi-word MneVoca batch request.  Rows generated through the existing
    single-word flow keep batch_id = NULL — the single-word path is fully
    backward compatible.

    The index exists because the batch navigation feature queries all rows
    with a given batch_id to support Previous / Next navigation without
    re-calling Gemini.

No existing rows are affected — the new column defaults to NULL.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mnemonic_history",
        sa.Column("batch_id", sa.String(36), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_column("mnemonic_history", "batch_id")
