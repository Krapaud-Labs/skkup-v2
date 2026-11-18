"""Admin moderation APIs for persisted antifraud flags."""

from datetime import UTC, datetime
from typing import Annotated, Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictStr
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.admin.models import FraudFlag
from app.admin.rate_limit import enforce_admin_rate_limit
from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent, User
from app.auth.routes import _require_origin
from app.db import get_db

router = APIRouter(prefix="/admin/fraud/flags", tags=["admin-fraud-flags"])
DatabaseSession = Annotated[Session, Depends(get_db)]
FraudStatus = Literal["OUVERTE", "EXAMINEE", "IGNOREE"]


class FraudFlagUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statut: FraudStatus
    note: StrictStr | None = Field(default=None, max_length=2000)


def _flag_view(flag: FraudFlag, user: User) -> dict[str, Any]:
    return {
        "id": flag.id,
        "userId": flag.user_id,
        "statut": flag.statut,
        "createdAt": flag.created_at,
        "examineeAt": flag.examinee_at,
        "user": {
            "id": user.id,
            "pseudo": user.pseudo,
        },
    }


def _load(db: Session, flag_id: str) -> tuple[FraudFlag, User]:
    row = db.execute(
        select(FraudFlag, User)
        .join(User, User.id == FraudFlag.user_id)
        .where(FraudFlag.id == flag_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Signalement anti-fraude introuvable.")
    return row


@router.get("")
def list_fraud_flags(
    request: Request,
    db: DatabaseSession,
    statut: Annotated[
        FraudStatus | None,
        Query(description="OUVERTE, EXAMINEE or IGNOREE"),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, Any]:
    actor = require_admin(request, db)
    enforce_admin_rate_limit(request, actor.id)
    criteria = [] if statut is None else [FraudFlag.statut == statut]
    total = int(db.scalar(select(func.count()).select_from(FraudFlag).where(*criteria)) or 0)
    rows = db.execute(
        select(FraudFlag, User)
        .join(User, User.id == FraudFlag.user_id)
        .where(*criteria)
        .order_by(FraudFlag.created_at.desc(), FraudFlag.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return {
        "items": [_flag_view(flag, user) for flag, user in rows],
        "total": total,
        "page": page,
        "limit": limit,
        "availability": {
            "sourceDetails": "not_implemented",
            "watchSession": "not_implemented",
        },
    }


@router.get("/{flag_id}")
def get_fraud_flag(flag_id: str, request: Request, db: DatabaseSession) -> dict[str, Any]:
    actor = require_admin(request, db)
    enforce_admin_rate_limit(request, actor.id)
    flag, user = _load(db, flag_id)
    audit_rows = db.execute(
        select(
            AdminAuditEvent.id,
            AdminAuditEvent.action,
            AdminAuditEvent.actor_id,
            User.pseudo,
            AdminAuditEvent.created_at,
        )
        .join(User, User.id == AdminAuditEvent.actor_id)
        .where(
            AdminAuditEvent.entity_type == "FraudFlag",
            AdminAuditEvent.entity_id == flag_id,
        )
        .order_by(AdminAuditEvent.created_at.asc(), AdminAuditEvent.id.asc())
        .limit(100)
    ).all()
    view = _flag_view(flag, user)
    view["availability"] = {
        "sourceDetails": "not_implemented",
        "watchSession": "not_implemented",
    }
    view["audit"] = [
        {
            "id": row.id,
            "action": row.action,
            "actor": {"id": row.actor_id, "pseudo": row.pseudo},
            "createdAt": row.created_at,
        }
        for row in audit_rows
    ]
    return view


@router.patch("/{flag_id}")
def update_fraud_flag(
    flag_id: str,
    payload: FraudFlagUpdate,
    request: Request,
    db: DatabaseSession,
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    enforce_admin_rate_limit(request, actor.id)
    flag, _ = _load(db, flag_id)
    previous_status = flag.statut
    examined_at = None if payload.statut == "OUVERTE" else datetime.now(UTC)
    result = db.execute(
        update(FraudFlag)
        .where(FraudFlag.id == flag_id, FraudFlag.statut == previous_status)
        .values(statut=payload.statut, examinee_at=examined_at)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="Le signalement a changé simultanément.")
    db.expire(flag)
    flag, user = _load(db, flag_id)
    metadata: dict[str, Any] = {
        "previousStatut": previous_status,
        "statut": payload.statut,
    }
    if payload.note and payload.note.strip():
        metadata["note"] = payload.note.strip()
    db.add(
        AdminAuditEvent(
            id=str(uuid4()),
            actor_id=actor.id,
            action="FRAUD_FLAG_STATUS_UPDATED",
            entity_type="FraudFlag",
            entity_id=flag_id,
            metadata_json=metadata,
        )
    )
    db.commit()
    return _flag_view(flag, user)
