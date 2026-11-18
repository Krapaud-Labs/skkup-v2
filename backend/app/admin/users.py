"""V1-grounded Admin user consultation and account status management."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, StrictBool
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent, AuthSession, User
from app.auth.routes import _require_origin
from app.db import get_db
from app.points.models import PointsTransaction

router = APIRouter(prefix="/admin/users", tags=["admin-users"])
DatabaseSession = Annotated[Session, Depends(get_db)]


class UpdateUserStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actif: StrictBool


def _compte_user(db: Session, user_id: str, *, details: bool = False) -> dict[str, Any] | None:
    user = db.get(User, user_id)
    if user is None:
        return None

    counts: dict[str, int | None] = {
        # These source-V1 counters have no corresponding V2 models yet. Null
        # communicates unavailable data instead of incorrectly reporting 0.
        "raffleTickets": None,
        "watchSessions": None,
    }
    if details:
        counts["pointsTransactions"] = (
            db.scalar(
                select(func.count(PointsTransaction.id)).where(PointsTransaction.user_id == user_id)
            )
            or 0
        )
    return {
        "id": user.id,
        "pseudo": user.pseudo,
        "email": user.email,
        "role": user.role,
        "actif": user.active,
        "soldePoints": user.points_balance,
        "streakActuel": user.current_streak,
        **({"streakMax": user.max_streak} if details else {}),
        **({"derniereVisiteAt": user.last_visit_at} if details else {}),
        "createdAt": user.created_at,
        "_count": counts,
    }


@router.get("")
def lister_utilisateurs(
    request: Request,
    db: DatabaseSession,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> list[dict[str, Any]]:
    require_admin(request, db)
    statement = select(User)
    term = search.strip() if search else ""
    if term:
        statement = statement.where(
            or_(User.pseudo.ilike(f"%{term}%"), User.email.ilike(f"%{term}%"))
        )
    users = db.scalars(statement.order_by(User.created_at.desc()).limit(100)).all()
    return [
        {
            "id": user.id,
            "pseudo": user.pseudo,
            "email": user.email,
            "role": user.role,
            "actif": user.active,
            "soldePoints": user.points_balance,
            "streakActuel": user.current_streak,
            "createdAt": user.created_at,
            "_count": {"raffleTickets": None, "watchSessions": None},
        }
        for user in users
    ]


@router.get("/{user_id}")
def detail_utilisateur(user_id: str, request: Request, db: DatabaseSession) -> dict[str, Any]:
    require_admin(request, db)
    result = _compte_user(db, user_id, details=True)
    if result is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return result


@router.get("/{user_id}/audit")
def historique_utilisateur(
    user_id: str, request: Request, db: DatabaseSession
) -> list[dict[str, Any]]:
    require_admin(request, db)
    events = db.scalars(
        select(AdminAuditEvent)
        .where(AdminAuditEvent.entity_type == "User", AdminAuditEvent.entity_id == user_id)
        .order_by(AdminAuditEvent.created_at.desc())
        .limit(100)
    ).all()
    return [
        {
            "id": event.id,
            "action": event.action,
            "metadata": event.metadata_json,
            "actorId": event.actor_id,
            "createdAt": event.created_at,
        }
        for event in events
    ]


@router.patch("/{user_id}/status")
def modifier_statut_utilisateur(
    user_id: str,
    payload: UpdateUserStatus,
    request: Request,
    db: DatabaseSession,
) -> dict[str, Any]:
    admin = require_admin(request, db)
    _require_origin(request)
    if user_id == admin.id and not payload.actif:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un administrateur ne peut pas désactiver sa propre session.",
        )

    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    previous_active = user.active
    user.active = payload.actif
    action = "USER_ACTIVATED" if payload.actif else "USER_DEACTIVATED"
    if not payload.actif:
        user.session_version += 1
        db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
    db.add(
        AdminAuditEvent(
            id=str(uuid4()),
            actor_id=admin.id,
            action=action,
            entity_type="User",
            entity_id=user_id,
            metadata_json={"previousActif": previous_active, "actif": payload.actif},
        )
    )
    db.commit()
    return {"id": user.id, "pseudo": user.pseudo, "role": user.role, "actif": user.active}
