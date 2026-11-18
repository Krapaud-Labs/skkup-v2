"""Add the WatchSession-independent part of Admin FraudFlag moderation."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_admin_fraud_flags"
down_revision: str | Sequence[str] | None = "0007_admin_audit_timeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fraud_flags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("statut", sa.String(length=16), server_default="OUVERTE", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("examinee_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "statut IN ('OUVERTE', 'EXAMINEE', 'IGNOREE')", name="ck_fraud_flags_status"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fraud_flags_user_status", "fraud_flags", ["user_id", "statut"])
    op.create_index("ix_fraud_flags_created", "fraud_flags", ["created_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_fraud_flags_created", table_name="fraud_flags")
    op.drop_index("ix_fraud_flags_user_status", table_name="fraud_flags")
    op.drop_table("fraud_flags")
