"""Add mnemonic_feedback table (ratings)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-02

V1 still auto-creates new tables on startup via `metadata.create_all`
(see app/database/session.py::init_models), so, like 0001, you don't have
to run this manually for the bot itself to work. It exists so `alembic
history` stays accurate. If you already ran `alembic stamp 0001` per the
0001 migration's note, bring yourself up to date with:

    alembic stamp 0002
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mnemonic_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "mnemonic_history_id",
            sa.Integer(),
            sa.ForeignKey("mnemonic_history.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_helpful", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_mnemonic_feedback_mnemonic_history_id", "mnemonic_feedback", ["mnemonic_history_id"]
    )
    op.create_index("ix_mnemonic_feedback_user_id", "mnemonic_feedback", ["user_id"])
    op.create_unique_constraint(
        "uq_feedback_mnemonic_user", "mnemonic_feedback", ["mnemonic_history_id", "user_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_feedback_mnemonic_user", "mnemonic_feedback", type_="unique")
    op.drop_index("ix_mnemonic_feedback_user_id", table_name="mnemonic_feedback")
    op.drop_index("ix_mnemonic_feedback_mnemonic_history_id", table_name="mnemonic_feedback")
    op.drop_table("mnemonic_feedback")
