"""Bounded Admin cockpit summary from domains implemented in V2."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admin.models import Announcement, ManagedContent
from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent, User
from app.db import get_db

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])
DatabaseSession = Annotated[Session, Depends(get_db)]
ACTIVITY_LIMIT = 8
ROW_LIMIT = 5


def _count(db: Session, model: type, *criteria: Any) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(*criteria)) or 0)


@router.get("/summary")
def dashboard_summary(request: Request, db: DatabaseSession) -> dict[str, Any]:
    require_admin(request, db)

    published_announcement = Announcement.status == "PUBLISHED"
    published_content = ManagedContent.status == "PUBLISHED"
    counts = {
        "users": _count(db, User),
        "activeUsers": _count(db, User, User.active.is_(True)),
        # These domains are not connected until the #7/#8/#9 persistence slices.
        # Null communicates unavailable; it must not be presented as a true zero.
        "openRaffles": None,
        "totalRaffles": None,
        "availableLots": None,
        "totalLots": None,
        "publishedContent": _count(db, ManagedContent, published_content),
        "activeAnnouncements": _count(db, Announcement, published_announcement),
        "totalAnnouncements": _count(db, Announcement),
        "openFraudFlags": None,
        "totalFraudFlags": None,
        "activeStreams": None,
    }

    activity_rows = db.execute(
        select(AdminAuditEvent, User.id, User.pseudo)
        .join(User, User.id == AdminAuditEvent.actor_id)
        .order_by(AdminAuditEvent.created_at.desc(), AdminAuditEvent.id.desc())
        .limit(ACTIVITY_LIMIT)
    ).all()
    recent_activity = [
        {
            "id": event.id,
            "action": event.action,
            "entityType": event.entity_type,
            "entityId": event.entity_id,
            "createdAt": event.created_at,
            "actor": {"id": actor_id, "pseudo": pseudo},
        }
        for event, actor_id, pseudo in activity_rows
    ]

    announcements = db.scalars(
        select(Announcement)
        .where(published_announcement)
        .order_by(Announcement.created_at.desc(), Announcement.id.desc())
        .limit(ROW_LIMIT)
    ).all()
    contents = db.scalars(
        select(ManagedContent)
        .where(published_content)
        .order_by(ManagedContent.updated_at.desc(), ManagedContent.id.asc())
        .limit(ROW_LIMIT)
    ).all()

    return {
        "availability": {
            "users": "available",
            "activity": "available",
            "announcements": "available",
            "contents": "available",
            "raffles": "not_implemented",
            "lots": "not_implemented",
            "fraudFlags": "not_implemented",
            "streams": "not_implemented",
        },
        "counts": counts,
        "recentActivity": recent_activity,
        "raffles": None,
        "lots": None,
        "announcements": [
            {
                "id": row.id,
                "titre": row.titre,
                "texte": row.texte,
                "status": row.status,
                "actif": row.actif,
                "debutAt": row.debut_at,
                "finAt": row.fin_at,
            }
            for row in announcements
        ],
        "fraudFlags": None,
        "contents": [
            {
                "id": row.id,
                "slug": row.slug,
                "locale": row.locale,
                "status": row.status,
                "version": row.version,
            }
            for row in contents
        ],
    }
