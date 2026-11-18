"""Add durable Admin audit events for account status changes."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_admin_user_audit"
down_revision: str | Sequence[str] | None = "0003_viewer_points"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=160), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_audit_target_created",
        "admin_audit_events",
        ["entity_type", "entity_id", "created_at"],
    )
    op.create_index(
        "ix_admin_audit_actor_created",
        "admin_audit_events",
        ["actor_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_actor_created", table_name="admin_audit_events")
    op.drop_index("ix_admin_audit_target_created", table_name="admin_audit_events")
    op.drop_table("admin_audit_events")
