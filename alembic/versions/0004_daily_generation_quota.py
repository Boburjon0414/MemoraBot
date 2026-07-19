"""Daily generation quota: rolling 24-hour reset for free users

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-19

What changes and why
--------------------
The V1.2 `ai_generations_used` counter was a lifetime total — it never
reset, so free users who hit the limit of 3 were permanently blocked.

V1.3 replaces this with a proper daily (24-hour rolling) quota:

1. `user_settings.daily_generation_count` (INTEGER NOT NULL DEFAULT 0)
   Tracks how many new AI generations the user has consumed in the current
   24-hour window. Reset to 0 automatically at request time once 24 hours
   have elapsed since `last_daily_reset`. This is what `UsageService` now
   reads — NOT `ai_generations_used`.

2. `user_settings.last_daily_reset` (DATETIME NULL)
   The UTC timestamp of the most recent quota reset (or account creation
   for new users). NULL for rows created before this migration; treated as
   epoch 0 in application code, which forces a reset + seed on first use,
   so pre-existing users silently get a fresh daily window.

3. `user_settings.is_premium` (BOOLEAN NOT NULL DEFAULT 0)
   When True, `UsageService.has_quota_remaining` always returns True and
   `record_generation` is a no-op — premium users have unlimited daily
   generations. Coins, referrals, and all other settings are unaffected.

`ai_generations_used` is kept as a lifetime audit counter and is still
incremented by `increment_generation_count` in the repository. It is no
longer read by `UsageService`.

Existing installs:
- `daily_generation_count` starts at 0 for all users — their in-progress
  24-hour window is treated as starting fresh (new-day generous reset).
- `last_daily_reset` is left NULL for pre-existing rows; the application
  treats NULL as "never reset" and resets on the very next request.
- `is_premium` defaults to False — no existing user gains premium status.

Run against a live database:

    alembic upgrade head
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Daily rolling generation counter (replaces the lifetime counter for
    #    quota enforcement — the old column is kept for audit history).
    op.add_column(
        "user_settings",
        sa.Column(
            "daily_generation_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # 2. Timestamp of the last quota reset, stored as naive UTC.
    #    NULL for pre-existing rows — application treats NULL as epoch 0,
    #    triggering a silent reset + seed on the very next request.
    op.add_column(
        "user_settings",
        sa.Column("last_daily_reset", sa.DateTime(), nullable=True),
    )

    # 3. Premium flag — bypasses the daily quota entirely when True.
    op.add_column(
        "user_settings",
        sa.Column(
            "is_premium",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "is_premium")
    op.drop_column("user_settings", "last_daily_reset")
    op.drop_column("user_settings", "daily_generation_count")
