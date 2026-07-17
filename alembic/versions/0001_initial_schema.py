"""Initial schema: users, user_settings, mnemonic_history

Revision ID: 0001
Revises:
Create Date: 2026-07-02

NOTE: V1 auto-creates these tables on startup via SQLAlchemy's
`metadata.create_all` (see app/database/session.py::init_models), so you do
NOT need to run `alembic upgrade head` for a fresh install. This migration
exists so Alembic's history has a correct baseline for *future* schema
changes. After your first run, stamp the database at this revision:

    alembic stamp 0001

...then any later `alembic revision --autogenerate` will produce a correct
diff instead of re-creating tables that already exist.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("preferred_language", sa.String(length=8), nullable=False, server_default="uz"),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"], unique=True)

    op.create_table(
        "mnemonic_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("word", sa.String(length=255), nullable=False),
        sa.Column("meaning", sa.Text(), nullable=False),
        sa.Column("uzbek_pronunciation", sa.Text(), nullable=False),
        sa.Column("mnemonic_story", sa.Text(), nullable=False),
        sa.Column("example_sentence", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=16), nullable=False),
        sa.Column("ai_provider", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_mnemonic_history_user_id", "mnemonic_history", ["user_id"])
    op.create_index("ix_mnemonic_history_word", "mnemonic_history", ["word"])


def downgrade() -> None:
    op.drop_index("ix_mnemonic_history_word", table_name="mnemonic_history")
    op.drop_index("ix_mnemonic_history_user_id", table_name="mnemonic_history")
    op.drop_table("mnemonic_history")

    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_table("user_settings")

    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
