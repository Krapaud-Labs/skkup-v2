"""Index the bounded global Admin audit timeline."""

from collections.abc import Sequence

from alembic import op

revision: str = "0007_admin_audit_timeline"
down_revision: str | Sequence[str] | None = "0006_admin_sponsors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_admin_audit_created",
        "admin_audit_events",
        ["created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_created", table_name="admin_audit_events")
