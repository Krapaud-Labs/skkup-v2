"""Add raffle and prize-lot configuration for Admin; draw mechanics remain separate."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_admin_raffle_configuration"
down_revision: str | Sequence[str] | None = "0008_admin_fraud_flags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "raffles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("titre", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("date_ouverture", sa.DateTime(timezone=True), nullable=False),
        sa.Column("date_tirage", sa.DateTime(timezone=True), nullable=False),
        sa.Column("statut", sa.String(length=16), server_default="OUVERT", nullable=False),
        sa.Column("engagement_graine", sa.String(length=64), nullable=True),
        sa.CheckConstraint("statut IN ('OUVERT', 'CLOTURE', 'TIRE')", name="ck_raffles_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "raffle_lots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("raffle_id", sa.String(length=36), nullable=False),
        sa.Column("sponsor_id", sa.String(length=36), nullable=True),
        sa.Column("nom", sa.String(length=160), nullable=False),
        sa.Column("valeur_estimee", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantite", sa.Integer(), nullable=False),
        sa.Column("fournisseur", sa.String(length=160), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.CheckConstraint("quantite >= 1", name="ck_raffle_lots_quantity_positive"),
        sa.ForeignKeyConstraint(["raffle_id"], ["raffles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sponsor_id"], ["sponsors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raffle_lots_raffle", "raffle_lots", ["raffle_id"])
    op.create_index("ix_raffle_lots_sponsor", "raffle_lots", ["sponsor_id"])


def downgrade() -> None:
    op.drop_index("ix_raffle_lots_sponsor", table_name="raffle_lots")
    op.drop_index("ix_raffle_lots_raffle", table_name="raffle_lots")
    op.drop_table("raffle_lots")
    op.drop_table("raffles")
