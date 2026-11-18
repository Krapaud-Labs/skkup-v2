"""Bounded, minimally selected global Admin audit history."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent, User
from app.db import get_db

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("")
def list_admin_audit(
    request: Request,
    db: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, Any]:
    require_admin(request, db)
    total = int(db.scalar(select(func.count()).select_from(AdminAuditEvent)) or 0)
    rows = db.execute(
        select(
            AdminAuditEvent.id,
            AdminAuditEvent.action,
            AdminAuditEvent.entity_type,
            AdminAuditEvent.entity_id,
            AdminAuditEvent.created_at,
            User.id.label("actor_id"),
            User.pseudo.label("actor_pseudo"),
        )
        .join(User, User.id == AdminAuditEvent.actor_id)
        .order_by(AdminAuditEvent.created_at.desc(), AdminAuditEvent.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "action": row.action,
                "entityType": row.entity_type,
                "entityId": row.entity_id,
                "createdAt": row.created_at,
                "actor": {"id": row.actor_id, "pseudo": row.actor_pseudo},
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }
