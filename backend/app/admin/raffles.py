"""Admin configuration of raffles and prize lots; drawing belongs to #9."""

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any
from urllib.parse import urlsplit
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.admin.models import Announcement, Raffle, RaffleLot, Sponsor
from app.admin.rate_limit import enforce_admin_rate_limit
from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent, User
from app.auth.routes import _require_origin
from app.db import get_db

router = APIRouter(prefix="/admin/raffles", tags=["admin-raffles"])
DatabaseSession = Annotated[Session, Depends(get_db)]
RAFFLE_STATUSES = {"OUVERT", "CLOTURE", "TIRE"}
AMOUNT_PATTERN = re.compile(r"^\d{1,8}(?:\.\d{1,2})?$")
PARIS = ZoneInfo("Europe/Paris")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _validate_image_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("L'image du lot doit être une URL HTTPS valide.")
    return value


class RaffleLotInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: StrictStr = Field(min_length=1, max_length=160)
    valeurEstimee: StrictStr = Field(min_length=1, max_length=32)
    quantite: StrictInt = Field(ge=1)
    fournisseur: StrictStr = Field(min_length=1, max_length=160)
    sponsorId: StrictStr | None = Field(default=None, min_length=1, max_length=120)
    imageUrl: StrictStr | None = Field(default=None, max_length=2048)

    @field_validator("valeurEstimee")
    @classmethod
    def validate_value(cls, value: str) -> str:
        if not AMOUNT_PATTERN.fullmatch(value):
            raise ValueError(
                "La valeur estimée doit être un montant positif ou nul à deux décimales."
            )
        try:
            Decimal(value)
        except InvalidOperation as error:
            raise ValueError("La valeur estimée doit être numérique.") from error
        return value

    @field_validator("imageUrl")
    @classmethod
    def validate_image(cls, value: str | None) -> str | None:
        return _validate_image_url(value)


class RaffleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: StrictStr = Field(min_length=1, max_length=160)
    description: StrictStr = Field(min_length=1, max_length=2000)
    dateOuverture: datetime
    dateTirage: datetime
    engagementGraine: StrictStr = Field(pattern=r"^[a-fA-F0-9]{64}$")
    lots: list[RaffleLotInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_dates(self) -> "RaffleCreate":
        if _utc(self.dateTirage) <= _utc(self.dateOuverture):
            raise ValueError("La date du tirage doit être postérieure à l'ouverture.")
        return self


class RaffleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: StrictStr | None = Field(default=None, min_length=1, max_length=160)
    description: StrictStr | None = Field(default=None, min_length=1, max_length=2000)
    dateTirage: datetime | None = None
    lots: list[RaffleLotInput] | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "RaffleUpdate":
        for field_name in ("titre", "description", "dateTirage", "lots"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"Le champ {field_name} ne peut pas être nul.")
        return self


def _lot_view(lot: RaffleLot) -> dict[str, Any]:
    return {
        "id": lot.id,
        "nom": lot.nom,
        "valeurEstimee": lot.valeur_estimee,
        "quantite": lot.quantite,
        "fournisseur": lot.fournisseur,
        "sponsorId": lot.sponsor_id,
        "sponsor": (
            {"id": lot.sponsor.id, "nom": lot.sponsor.nom, "logoUrl": lot.sponsor.logo_url}
            if lot.sponsor
            else None
        ),
        "imageUrl": lot.image_url,
    }


def _raffle_view(raffle: Raffle) -> dict[str, Any]:
    return {
        "id": raffle.id,
        "titre": raffle.titre,
        "description": raffle.description,
        "dateOuverture": raffle.date_ouverture,
        "dateTirage": raffle.date_tirage,
        "statut": raffle.statut,
        "engagementGraine": raffle.engagement_graine,
        "ticketsDistribues": None,
        "gagnantsCount": None,
        "lots": [_lot_view(lot) for lot in raffle.lots],
        "drawAvailability": "not_implemented",
    }


def _lot_values(payload: RaffleLotInput, raffle_id: str) -> RaffleLot:
    return RaffleLot(
        id=str(uuid4()),
        raffle_id=raffle_id,
        sponsor_id=payload.sponsorId,
        nom=payload.nom,
        valeur_estimee=Decimal(payload.valeurEstimee),
        quantite=payload.quantite,
        fournisseur=payload.fournisseur,
        image_url=payload.imageUrl,
    )


def _require_sponsors(db: Session, lots: list[RaffleLotInput]) -> None:
    ids = {lot.sponsorId for lot in lots if lot.sponsorId}
    if not ids:
        return
    found = set(db.scalars(select(Sponsor.id).where(Sponsor.id.in_(ids))).all())
    missing = ids - found
    if missing:
        raise HTTPException(status_code=404, detail="Un sponsor de lot est introuvable.")


def _audit(
    db: Session,
    *,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict[str, Any],
) -> None:
    db.add(
        AdminAuditEvent(
            id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata,
        )
    )


def _load_raffle(db: Session, raffle_id: str, *, lock: bool = False) -> Raffle:
    statement = (
        select(Raffle)
        .options(selectinload(Raffle.lots).selectinload(RaffleLot.sponsor))
        .where(Raffle.id == raffle_id)
    )
    if lock:
        statement = statement.with_for_update()
    raffle = db.scalar(statement)
    if raffle is None:
        raise HTTPException(status_code=404, detail="Tirage introuvable.")
    return raffle


def _published_announcement(raffle: Raffle, actor_id: str) -> Announcement:
    months = (
        "janvier",
        "février",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "août",
        "septembre",
        "octobre",
        "novembre",
        "décembre",
    )

    def format_date(value: datetime) -> str:
        local = value.astimezone(PARIS)
        return f"{local.day} {months[local.month - 1]} {local.year} à {local:%H:%M}"

    opening = format_date(raffle.date_ouverture)
    draw = format_date(raffle.date_tirage)
    title = f"Nouveau tirage : {raffle.titre}"[:160]
    return Announcement(
        id=str(uuid4()),
        titre=title,
        texte=(
            f"Tirage « {raffle.titre} ». Ouverture prévue le {opening}. Tirage prévu le {draw}."
        )[:2000],
        status="DRAFT",
        actif=False,
        debut_at=raffle.date_ouverture,
        fin_at=raffle.date_tirage,
        created_by_id=actor_id,
    )


def _audit_snapshot(raffle: Raffle) -> dict[str, Any]:
    return {
        "titre": raffle.titre,
        "description": raffle.description,
        "dateOuverture": raffle.date_ouverture.isoformat(),
        "dateTirage": raffle.date_tirage.isoformat(),
        "statut": raffle.statut,
        "engagementGraine": raffle.engagement_graine,
        "lots": [
            {
                "nom": lot.nom,
                "valeurEstimee": str(lot.valeur_estimee),
                "quantite": lot.quantite,
                "fournisseur": lot.fournisseur,
                "sponsorId": lot.sponsor_id,
                "imageUrl": lot.image_url,
            }
            for lot in raffle.lots
        ],
    }


@router.get("")
def list_raffles(
    request: Request,
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, Any]:
    actor = require_admin(request, db)
    enforce_admin_rate_limit(request, actor.id)
    total = int(db.scalar(select(func.count()).select_from(Raffle)) or 0)
    raffles = db.scalars(
        select(Raffle)
        .options(selectinload(Raffle.lots).selectinload(RaffleLot.sponsor))
        .order_by(Raffle.date_tirage.desc(), Raffle.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return {
        "items": [_raffle_view(raffle) for raffle in raffles],
        "total": total,
        "page": page,
        "limit": limit,
        "availability": {"draws": "not_implemented", "tickets": "not_implemented"},
    }


@router.get("/{raffle_id}")
def get_raffle(raffle_id: str, request: Request, db: DatabaseSession) -> dict[str, Any]:
    actor = require_admin(request, db)
    enforce_admin_rate_limit(request, actor.id)
    return _raffle_view(_load_raffle(db, raffle_id))


@router.get("/{raffle_id}/history")
def raffle_history(raffle_id: str, request: Request, db: DatabaseSession) -> dict[str, Any]:
    actor = require_admin(request, db)
    enforce_admin_rate_limit(request, actor.id)
    if db.get(Raffle, raffle_id) is None:
        raise HTTPException(status_code=404, detail="Tirage introuvable.")
    rows = db.execute(
        select(
            AdminAuditEvent.id,
            AdminAuditEvent.action,
            AdminAuditEvent.actor_id,
            User.pseudo,
            AdminAuditEvent.created_at,
        )
        .join(User, User.id == AdminAuditEvent.actor_id)
        .where(AdminAuditEvent.entity_type == "Raffle", AdminAuditEvent.entity_id == raffle_id)
        .order_by(AdminAuditEvent.created_at.desc(), AdminAuditEvent.id.desc())
        .limit(100)
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "action": row.action,
                "actor": {"id": row.actor_id, "pseudo": row.pseudo},
                "createdAt": row.created_at,
            }
            for row in rows
        ],
        "draws": None,
        "availability": {"draws": "not_implemented"},
    }


@router.post("")
def create_raffle(payload: RaffleCreate, request: Request, db: DatabaseSession) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    enforce_admin_rate_limit(request, actor.id)
    _require_sponsors(db, payload.lots)
    raffle = Raffle(
        id=str(uuid4()),
        titre=payload.titre,
        description=payload.description,
        date_ouverture=_utc(payload.dateOuverture),
        date_tirage=_utc(payload.dateTirage),
        statut="OUVERT",
        engagement_graine=payload.engagementGraine.lower(),
    )
    raffle.lots = [_lot_values(lot, raffle.id) for lot in payload.lots]
    announcement = _published_announcement(raffle, actor.id)
    db.add_all([raffle, announcement])
    db.flush()
    _audit(
        db,
        actor_id=actor.id,
        action="RAFFLE_CREATED",
        entity_type="Raffle",
        entity_id=raffle.id,
        metadata={
            "titre": raffle.titre,
            "dateOuverture": raffle.date_ouverture.isoformat(),
            "dateTirage": raffle.date_tirage.isoformat(),
            "announcementId": announcement.id,
        },
    )
    previous_announcement = {
        "titre": announcement.titre,
        "texte": announcement.texte,
        "debutAt": announcement.debut_at.isoformat() if announcement.debut_at else None,
        "finAt": announcement.fin_at.isoformat() if announcement.fin_at else None,
        "status": announcement.status,
    }
    _audit(
        db,
        actor_id=actor.id,
        action="ANNOUNCEMENT_CREATED",
        entity_type="Announcement",
        entity_id=announcement.id,
        metadata={
            "titre": announcement.titre,
            "status": "DRAFT",
            "actif": False,
            "source": "RAFFLE_CREATED",
            "raffleId": raffle.id,
        },
    )
    announcement.status = "PUBLISHED"
    announcement.actif = True
    _audit(
        db,
        actor_id=actor.id,
        action="ANNOUNCEMENT_PUBLISHED",
        entity_type="Announcement",
        entity_id=announcement.id,
        metadata={
            "previous": previous_announcement,
            "current": {
                "titre": announcement.titre,
                "texte": announcement.texte,
                "debutAt": announcement.debut_at.isoformat() if announcement.debut_at else None,
                "finAt": announcement.fin_at.isoformat() if announcement.fin_at else None,
                "status": announcement.status,
            },
            "source": "RAFFLE_CREATED",
            "raffleId": raffle.id,
        },
    )
    db.commit()
    return _raffle_view(_load_raffle(db, raffle.id))


@router.patch("/{raffle_id}")
def update_raffle(
    raffle_id: str,
    payload: RaffleUpdate,
    request: Request,
    db: DatabaseSession,
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    enforce_admin_rate_limit(request, actor.id)
    current = _load_raffle(db, raffle_id, lock=True)
    if current.statut != "OUVERT":
        raise HTTPException(
            status_code=409, detail="Seuls les tirages ouverts peuvent être modifiés."
        )
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return _raffle_view(current)
    previous = _audit_snapshot(current)
    draw_at = _utc(changes["dateTirage"]) if changes.get("dateTirage") else current.date_tirage
    if draw_at <= current.date_ouverture:
        raise HTTPException(
            status_code=422,
            detail="La date du tirage doit être postérieure à l'ouverture.",
        )
    if "lots" in changes and changes["lots"] is not None:
        _require_sponsors(db, payload.lots or [])

    if "titre" in changes:
        current.titre = changes["titre"]
    if "description" in changes:
        current.description = changes["description"]
    if "dateTirage" in changes:
        current.date_tirage = draw_at
    if "lots" in changes and changes["lots"] is not None:
        db.execute(delete(RaffleLot).where(RaffleLot.raffle_id == raffle_id))
        current.lots = [_lot_values(lot, raffle_id) for lot in payload.lots or []]
    db.flush()
    db.expire(current, ["lots"])
    current = _load_raffle(db, raffle_id)
    _audit(
        db,
        actor_id=actor.id,
        action="RAFFLE_UPDATED",
        entity_type="Raffle",
        entity_id=raffle_id,
        metadata={"previous": previous, "current": _audit_snapshot(current)},
    )
    db.commit()
    db.expire_all()
    return _raffle_view(_load_raffle(db, raffle_id))
