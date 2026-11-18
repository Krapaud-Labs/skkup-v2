"""Add the points ledger, idempotent daily check-ins and reward tickets."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_viewer_points"
down_revision: str | Sequence[str] | None = "0002_member_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "points_transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "type IN ('VISITE_QUOTIDIENNE', 'WATCH_TIME', 'CARTE_A_GRATTER', "
            "'AJUSTEMENT_ADMIN', 'SHOP_PURCHASE')",
            name="ck_points_transaction_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_points_user_idempotency"),
    )
    op.create_index("ix_points_user_created", "points_transactions", ["user_id", "created_at"])

    op.create_table(
        "daily_checkins",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("local_day", sa.Date(), nullable=False),
        sa.Column("streak_after", sa.Integer(), nullable=False),
        sa.Column("max_streak_after", sa.Integer(), nullable=False),
        sa.Column("points_balance_after", sa.Integer(), nullable=False),
        sa.Column("scratch_card_due", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "local_day", name="uq_daily_checkins_user_day"),
    )
    op.create_index(
        "ix_daily_checkins_user_created", "daily_checkins", ["user_id", "created_at"]
    )

    op.create_table(
        "scratch_card_grants",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("daily_checkin_id", sa.String(length=36), nullable=False),
        sa.Column("streak_milestone", sa.Integer(), nullable=False),
        sa.Column("legacy_ticket_preset", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["daily_checkin_id"], ["daily_checkins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("daily_checkin_id", name="uq_scratch_grant_checkin"),
    )
    op.create_index(
        "ix_scratch_grants_user_created", "scratch_card_grants", ["user_id", "created_at"]
    )

    op.create_table(
        "reward_tickets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=24), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "category IN ('CLASSIC', 'PREMIUM')", name="ck_reward_ticket_category"
        ),
        sa.CheckConstraint(
            "source IN ('DAILY_LOGIN', 'STREAK_MILESTONE', 'SCRATCH_CARD')",
            name="ck_reward_ticket_source",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_reward_tickets_user_key"),
    )
    op.create_index(
        "ix_reward_tickets_user_available",
        "reward_tickets",
        ["user_id", "consumed_at", "category"],
    )


def downgrade() -> None:
    op.drop_index("ix_reward_tickets_user_available", table_name="reward_tickets")
    op.drop_table("reward_tickets")
    op.drop_index("ix_scratch_grants_user_created", table_name="scratch_card_grants")
    op.drop_table("scratch_card_grants")
    op.drop_index("ix_daily_checkins_user_created", table_name="daily_checkins")
    op.drop_table("daily_checkins")
    op.drop_index("ix_points_user_created", table_name="points_transactions")
    op.drop_table("points_transactions")
