"""Add persisted scratch outcomes, raffle participation and audited draws."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_scratch_and_raffle_draws"
down_revision: str | Sequence[str] | None = "0009_admin_raffle_configuration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("raffles", sa.Column("graine_aleatoire", sa.String(64)))
    op.add_column("raffles", sa.Column("entropie_publique", sa.String(512)))
    op.add_column("raffles", sa.Column("empreinte_participants", sa.String(64)))
    op.add_column("raffles", sa.Column("nombre_participants", sa.Integer()))
    op.add_column("raffles", sa.Column("resultat_publie_at", sa.DateTime(timezone=True)))
    for table in ("scratch_card_grants", "reward_tickets"):
        op.add_column(table, sa.Column("prepared_at", sa.DateTime(timezone=True)))
        op.add_column(table, sa.Column("scratched_at", sa.DateTime(timezone=True)))
        op.add_column(table, sa.Column("outcome_type", sa.String(32)))
        op.add_column(table, sa.Column("outcome_points", sa.Integer()))
        op.add_column(table, sa.Column("outcome_tickets", sa.Integer()))

    with op.batch_alter_table("points_transactions") as batch:
        batch.drop_constraint("ck_points_transaction_type", type_="check")
        batch.create_check_constraint(
            "ck_points_transaction_type",
            "type IN ('VISITE_QUOTIDIENNE', 'WATCH_TIME', 'CARTE_A_GRATTER', "
            "'AJUSTEMENT_ADMIN', 'SHOP_PURCHASE', 'RAFFLE_ENTRY')",
        )

    op.create_table(
        "raffle_tickets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("raffle_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["raffle_id"], ["raffles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("raffle_id", "user_id", name="uq_raffle_ticket_user_raffle"),
    )
    op.create_index(
        "ix_raffle_tickets_raffle_created", "raffle_tickets", ["raffle_id", "created_at", "id"]
    )
    op.create_table(
        "raffle_winners",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("raffle_id", sa.String(36), nullable=False),
        sa.Column("raffle_ticket_id", sa.String(36), nullable=False),
        sa.Column("lot_id", sa.String(36), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["raffle_id"], ["raffles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raffle_ticket_id"], ["raffle_tickets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["lot_id"], ["raffle_lots.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("raffle_ticket_id", name="uq_raffle_winner_ticket"),
        sa.UniqueConstraint("raffle_id", "rank", name="uq_raffle_winner_rank"),
    )
    op.create_index("ix_raffle_winners_raffle", "raffle_winners", ["raffle_id", "rank"])
    op.create_table(
        "raffle_draw_audits",
        sa.Column("raffle_id", sa.String(36), primary_key=True),
        sa.Column("result_hash", sa.String(64), nullable=False),
        sa.Column("seed_commitment", sa.String(64), nullable=False),
        sa.Column("participants_hash", sa.String(64), nullable=False),
        sa.Column("algorithm", sa.String(64), nullable=False),
        sa.Column("executed_by_id", sa.String(36), nullable=False),
        sa.Column(
            "executed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["raffle_id"], ["raffles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["executed_by_id"], ["users.id"], ondelete="RESTRICT"),
    )


def downgrade() -> None:
    op.drop_table("raffle_draw_audits")
    op.drop_index("ix_raffle_winners_raffle", table_name="raffle_winners")
    op.drop_table("raffle_winners")
    op.drop_index("ix_raffle_tickets_raffle_created", table_name="raffle_tickets")
    op.drop_table("raffle_tickets")
    with op.batch_alter_table("points_transactions") as batch:
        batch.drop_constraint("ck_points_transaction_type", type_="check")
        batch.create_check_constraint(
            "ck_points_transaction_type",
            "type IN ('VISITE_QUOTIDIENNE', 'WATCH_TIME', 'CARTE_A_GRATTER', "
            "'AJUSTEMENT_ADMIN', 'SHOP_PURCHASE')",
        )
    for table in ("reward_tickets", "scratch_card_grants"):
        for name in (
            "outcome_tickets",
            "outcome_points",
            "outcome_type",
            "scratched_at",
            "prepared_at",
        ):
            op.drop_column(table, name)
    for name in (
        "resultat_publie_at",
        "nombre_participants",
        "empreinte_participants",
        "entropie_publique",
        "graine_aleatoire",
    ):
        op.drop_column("raffles", name)
