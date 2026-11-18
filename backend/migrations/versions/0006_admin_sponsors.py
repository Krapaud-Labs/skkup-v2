"""Add the V1-grounded Admin sponsor catalogue."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_admin_sponsors"
down_revision: str | Sequence[str] | None = "0005_admin_editorial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sponsors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("nom", sa.String(length=160), nullable=False),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("actif", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sponsors_active", "sponsors", ["actif"])


def downgrade() -> None:
    op.drop_index("ix_sponsors_active", table_name="sponsors")
    op.drop_table("sponsors")
