"""Persistent points ledger, daily progression and unassigned reward tickets."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import Base


class PointsTransaction(Base):
    __tablename__ = "points_transactions"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_points_user_idempotency"),
        CheckConstraint(
            "type IN ('VISITE_QUOTIDIENNE', 'WATCH_TIME', 'CARTE_A_GRATTER', "
            "'AJUSTEMENT_ADMIN', 'SHOP_PURCHASE', 'RAFFLE_ENTRY')",
            name="ck_points_transaction_type",
        ),
        Index("ix_points_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"
    __table_args__ = (
        UniqueConstraint("user_id", "local_day", name="uq_daily_checkins_user_day"),
        Index("ix_daily_checkins_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    local_day: Mapped[date] = mapped_column(Date, nullable=False)
    streak_after: Mapped[int] = mapped_column(Integer, nullable=False)
    max_streak_after: Mapped[int] = mapped_column(Integer, nullable=False)
    points_balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    scratch_card_due: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ScratchCardGrant(Base):
    """A V1 streak-card entitlement and its immutable one-time outcome."""

    __tablename__ = "scratch_card_grants"
    __table_args__ = (
        UniqueConstraint("daily_checkin_id", name="uq_scratch_grant_checkin"),
        Index("ix_scratch_grants_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    daily_checkin_id: Mapped[str] = mapped_column(
        ForeignKey("daily_checkins.id", ondelete="CASCADE"), nullable=False
    )
    streak_milestone: Mapped[int] = mapped_column(Integer, nullable=False)
    legacy_ticket_preset: Mapped[bool] = mapped_column(nullable=False, default=False)
    prepared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scratched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome_type: Mapped[str | None] = mapped_column(String(32))
    outcome_points: Mapped[int | None] = mapped_column(Integer)
    outcome_tickets: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RewardTicket(Base):
    __tablename__ = "reward_tickets"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_reward_tickets_user_key"),
        CheckConstraint("category IN ('CLASSIC', 'PREMIUM')", name="ck_reward_ticket_category"),
        CheckConstraint(
            "source IN ('DAILY_LOGIN', 'STREAK_MILESTONE', 'SCRATCH_CARD')",
            name="ck_reward_ticket_source",
        ),
        Index("ix_reward_tickets_user_available", "user_id", "consumed_at", "category"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    prepared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scratched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome_type: Mapped[str | None] = mapped_column(String(32))
    outcome_points: Mapped[int | None] = mapped_column(Integer)
    outcome_tickets: Mapped[int | None] = mapped_column(Integer)
