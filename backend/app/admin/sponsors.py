"""V1-grounded sponsor catalogue operations for Admin users."""

from typing import Annotated, Any
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.admin.models import Sponsor
from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent
from app.auth.routes import _require_origin
from app.db import get_db

router = APIRouter(prefix="/admin/sponsors", tags=["admin-sponsors"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def _validate_logo_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Le logo doit utiliser une URL HTTPS valide.")
    return value


class SponsorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: str = Field(min_length=1, max_length=160)
    logoUrl: str | None = None

    @field_validator("logoUrl")
    @classmethod
    def valid_logo_url(cls, value: str | None) -> str | None:
        return _validate_logo_url(value)


class SponsorUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: str | None = Field(default=None, min_length=1, max_length=160)
    logoUrl: str | None = None
    actif: StrictBool | None = None

    @field_validator("logoUrl")
    @classmethod
    def valid_logo_url(cls, value: str | None) -> str | None:
        return _validate_logo_url(value)


def _view(sponsor: Sponsor, *, include_count: bool = False) -> dict[str, Any]:
    result = {
        "id": sponsor.id,
        "nom": sponsor.nom,
        "logoUrl": sponsor.logo_url,
        "actif": sponsor.actif,
        "createdAt": sponsor.created_at,
    }
    if include_count:
        # RaffleLot does not exist in V2 until the #8 raffle model slice.
        result["_count"] = {"lots": None}
    return result


def _audit(
    db: Session,
    *,
    actor_id: str,
    action: str,
    sponsor: Sponsor,
    previous: dict[str, Any] | None = None,
) -> None:
    db.add(
        AdminAuditEvent(
            id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            entity_type="Sponsor",
            entity_id=sponsor.id,
            metadata_json={
                "previous": previous,
                "current": {
                    "nom": sponsor.nom,
                    "logoUrl": sponsor.logo_url,
                    "actif": sponsor.actif,
                },
            },
        )
    )


@router.get("")
def list_sponsors(
    request: Request,
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[dict[str, Any]]:
    require_admin(request, db)
    items = db.scalars(
        select(Sponsor)
        .order_by(Sponsor.nom.asc(), Sponsor.id.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return [_view(item, include_count=True) for item in items]


@router.post("")
def create_sponsor(payload: SponsorCreate, request: Request, db: DatabaseSession) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    sponsor = Sponsor(id=str(uuid4()), nom=payload.nom, logo_url=payload.logoUrl, actif=True)
    db.add(sponsor)
    db.flush()
    _audit(db, actor_id=actor.id, action="SPONSOR_CREATED", sponsor=sponsor)
    db.commit()
    return _view(sponsor)


@router.patch("/{sponsor_id}")
def update_sponsor(
    sponsor_id: str,
    payload: SponsorUpdate,
    request: Request,
    db: DatabaseSession,
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    sponsor = db.get(Sponsor, sponsor_id)
    if sponsor is None:
        raise HTTPException(status_code=404, detail="Sponsor introuvable.")
    changes = payload.model_dump(exclude_unset=True)
    values: dict[str, Any] = {}
    if "nom" in changes and changes["nom"] is not None:
        values["nom"] = changes["nom"]
    if "logoUrl" in changes:
        values["logo_url"] = changes["logoUrl"]
    if "actif" in changes and changes["actif"] is not None:
        values["actif"] = changes["actif"]
    if not values or all(getattr(sponsor, key) == value for key, value in values.items()):
        return _view(sponsor)

    previous = {"nom": sponsor.nom, "logoUrl": sponsor.logo_url, "actif": sponsor.actif}
    result = db.execute(
        update(Sponsor)
        .where(Sponsor.id == sponsor_id)
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="Le sponsor a changé simultanément.")
    db.expire(sponsor)
    sponsor = db.get(Sponsor, sponsor_id)
    assert sponsor is not None
    _audit(
        db,
        actor_id=actor.id,
        action="SPONSOR_UPDATED",
        sponsor=sponsor,
        previous=previous,
    )
    db.commit()
    return _view(sponsor)
