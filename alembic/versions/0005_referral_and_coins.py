"""Referral & Coins: coin_wallets, coin_transactions, referrals

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-19

What this migration adds
------------------------
Three new tables implementing the viral referral system and coin economy:

1. `coin_wallets`  (one per user)
   - `referral_code`   — unique 8-char alphanumeric deep-link payload
   - `coin_balance`    — current spendable balance
   - `lifetime_earned` — cumulative credits (audit metric)
   - `lifetime_spent`  — cumulative debits  (audit metric)

2. `coin_transactions`  (immutable ledger, many per wallet)
   - `amount`          — positive = credit, negative = debit
   - `tx_type`         — referral | welcome_bonus | admin_add | … (open set)
   - `description`     — human-readable label for the history UI
   - `ref_telegram_id` — optional Telegram ID of the related user (e.g. who was referred)

3. `referrals`  (one per referred user — UNIQUE on referred_id)
   - `referrer_id`     — who sent the invite
   - `referred_id`     — who accepted it (UNIQUE: one referrer per user)
   - `referral_code`   — code used at registration time (audit trail)
   - `rewarded`        — False until the coin award is confirmed
   - `reward_amount`   — coins awarded to the referrer

Existing installs:
  Run `alembic upgrade head` against a live database, or rely on the
  startup `init_models()` which calls `create_all` (idempotent).
  No existing data is modified.

Rollback:
  `alembic downgrade 0004` drops all three tables cleanly.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. coin_wallets --------------------------------------------------------
    op.create_table(
        "coin_wallets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("referral_code", sa.String(length=32), nullable=False),
        sa.Column("coin_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_spent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_coin_wallets_user_id", "coin_wallets", ["user_id"], unique=True)
    op.create_index(
        "ix_coin_wallets_referral_code", "coin_wallets", ["referral_code"], unique=True
    )

    # 2. coin_transactions ---------------------------------------------------
    op.create_table(
        "coin_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "wallet_id",
            sa.Integer(),
            sa.ForeignKey("coin_wallets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("tx_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ref_telegram_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_coin_transactions_wallet_id", "coin_transactions", ["wallet_id"])
    op.create_index("ix_coin_transactions_tx_type", "coin_transactions", ["tx_type"])
    op.create_index("ix_coin_transactions_created_at", "coin_transactions", ["created_at"])

    # 3. referrals -----------------------------------------------------------
    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "referrer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "referred_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("referral_code", sa.String(length=32), nullable=False),
        sa.Column("rewarded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reward_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_referrals_referrer_id", "referrals", ["referrer_id"])
    # UNIQUE on referred_id enforces "one user can only ever be referred once".
    op.create_index("ix_referrals_referred_id", "referrals", ["referred_id"], unique=True)
    op.create_index("ix_referrals_created_at", "referrals", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_referrals_created_at", table_name="referrals")
    op.drop_index("ix_referrals_referred_id", table_name="referrals")
    op.drop_index("ix_referrals_referrer_id", table_name="referrals")
    op.drop_table("referrals")

    op.drop_index("ix_coin_transactions_created_at", table_name="coin_transactions")
    op.drop_index("ix_coin_transactions_tx_type", table_name="coin_transactions")
    op.drop_index("ix_coin_transactions_wallet_id", table_name="coin_transactions")
    op.drop_table("coin_transactions")

    op.drop_index("ix_coin_wallets_referral_code", table_name="coin_wallets")
    op.drop_index("ix_coin_wallets_user_id", table_name="coin_wallets")
    op.drop_table("coin_wallets")
