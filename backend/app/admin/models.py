"""Persistence models for Admin-managed announcements and editorial content."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.models import Base


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')", name="ck_announcements_status"
        ),
        Index("ix_announcements_created", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    titre: Mapped[str] = mapped_column(String(160), nullable=False)
    texte: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    actif: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    debut_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fin_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ManagedContent(Base):
    __tablename__ = "managed_contents"
    __table_args__ = (
        CheckConstraint(
            "type IN ('LANDING', 'LEGAL', 'ANNOUNCEMENT', 'FAQ', 'MEDIA')",
            name="ck_managed_contents_type",
        ),
        CheckConstraint("locale IN ('fr', 'en')", name="ck_managed_contents_locale"),
        CheckConstraint("status IN ('DRAFT', 'PUBLISHED')", name="ck_managed_contents_status"),
        CheckConstraint("version >= 1", name="ck_managed_contents_version_positive"),
        UniqueConstraint("slug", "type", "locale", name="uq_managed_contents_slug_type_locale"),
        Index("ix_managed_contents_type_locale_status", "type", "locale", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(24), nullable=False)
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    updated_by_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ContentVersion(Base):
    __tablename__ = "content_versions"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_content_versions_version_positive"),
        CheckConstraint("status IN ('DRAFT', 'PUBLISHED')", name="ck_content_versions_status"),
        UniqueConstraint("content_id", "version", name="uq_content_versions_content_version"),
        Index("ix_content_versions_content_created", "content_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    content_id: Mapped[str] = mapped_column(
        ForeignKey("managed_contents.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_by_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Sponsor(Base):
    __tablename__ = "sponsors"
    __table_args__ = (Index("ix_sponsors_active", "actif"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nom: Mapped[str] = mapped_column(String(160), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String)
    actif: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    lots: Mapped[list["RaffleLot"]] = relationship(back_populates="sponsor")


class FraudFlag(Base):
    __tablename__ = "fraud_flags"
    __table_args__ = (
        CheckConstraint(
            "statut IN ('OUVERTE', 'EXAMINEE', 'IGNOREE')",
            name="ck_fraud_flags_status",
        ),
        Index("ix_fraud_flags_user_status", "user_id", "statut"),
        Index("ix_fraud_flags_created", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    statut: Mapped[str] = mapped_column(
        String(16), nullable=False, default="OUVERTE", server_default="OUVERTE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    examinee_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Raffle(Base):
    __tablename__ = "raffles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    titre: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    date_ouverture: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_tirage: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    statut: Mapped[str] = mapped_column(
        String(16), nullable=False, default="OUVERT", server_default="OUVERT"
    )
    engagement_graine: Mapped[str | None] = mapped_column(String(64))

    lots: Mapped[list["RaffleLot"]] = relationship(
        back_populates="raffle", cascade="all, delete-orphan", order_by="RaffleLot.id"
    )


class RaffleLot(Base):
    __tablename__ = "raffle_lots"
    __table_args__ = (
        CheckConstraint("quantite >= 1", name="ck_raffle_lots_quantity_positive"),
        Index("ix_raffle_lots_raffle", "raffle_id"),
        Index("ix_raffle_lots_sponsor", "sponsor_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    raffle_id: Mapped[str] = mapped_column(
        ForeignKey("raffles.id", ondelete="CASCADE"), nullable=False
    )
    sponsor_id: Mapped[str | None] = mapped_column(
        ForeignKey("sponsors.id", ondelete="SET NULL")
    )
    nom: Mapped[str] = mapped_column(String(160), nullable=False)
    valeur_estimee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    fournisseur: Mapped[str] = mapped_column(String(160), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048))

    raffle: Mapped[Raffle] = relationship(back_populates="lots")
    sponsor: Mapped[Sponsor | None] = relationship(back_populates="lots")
