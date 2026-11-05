"""Add button_name to grammar_topics

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-11

What this migration adds
------------------------
One new nullable column on `grammar_topics`:

  button_name  VARCHAR(255)  NULL
    Text shown on the admin-managed Telegram inline keyboard button.
    Example: "🟢 Present Perfect"
    Falls back to `title` when NULL (handled in application code).

No existing rows are affected — new column is NULL for all existing records,
and application code treats NULL the same as not set.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "grammar_topics",
        sa.Column("button_name", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("grammar_topics", "button_name")
