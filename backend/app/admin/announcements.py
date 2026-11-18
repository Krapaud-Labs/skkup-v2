"""Admin announcement lifecycle and public active-announcement query."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.admin.models import Announcement
from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent
from app.auth.routes import _require_origin
from app.db import get_db

admin_router = APIRouter(prefix="/admin/announcements", tags=["admin-announcements"])
public_router = APIRouter(tags=["announcements"])
DatabaseSession = Annotated[Session, Depends(get_db)]


class AnnouncementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: str = Field(min_length=1, max_length=160)
    texte: str = Field(min_length=1, max_length=2000)
    debutAt: datetime | None = None
    finAt: datetime | None = None

    @model_validator(mode="after")
    def validate_window(self) -> "AnnouncementCreate":
        _validate_window(self.debutAt, self.finAt)
        return self


class AnnouncementUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: str | None = Field(default=None, min_length=1, max_length=160)
    texte: str | None = Field(default=None, min_length=1, max_length=2000)
    actif: StrictBool | None = None
    debutAt: datetime | None = None
    finAt: datetime | None = None


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _validate_window(start: datetime | None, end: datetime | None) -> None:
    normalized_start = _normalize_datetime(start)
    normalized_end = _normalize_datetime(end)
    if (
        normalized_start is not None
        and normalized_end is not None
        and normalized_end < normalized_start
    ):
        raise ValueError("La fin d'affichage doit être postérieure au début.")


def _snapshot(announcement: Announcement) -> dict[str, Any]:
    return {
        "titre": announcement.titre,
        "texte": announcement.texte,
        "debutAt": announcement.debut_at.isoformat() if announcement.debut_at else None,
        "finAt": announcement.fin_at.isoformat() if announcement.fin_at else None,
        "status": announcement.status,
    }


def _announcement_view(announcement: Announcement) -> dict[str, Any]:
    return {
        "id": announcement.id,
        "titre": announcement.titre,
        "texte": announcement.texte,
        "status": announcement.status,
        "actif": announcement.actif,
        "debutAt": announcement.debut_at,
        "finAt": announcement.fin_at,
        "createdAt": announcement.created_at,
    }


def _record_audit(
    db: Session,
    *,
    actor_id: str,
    action: str,
    entity_id: str,
    metadata: dict[str, Any],
) -> None:
    db.add(
        AdminAuditEvent(
            id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            entity_type="Announcement",
            entity_id=entity_id,
            metadata_json=metadata,
        )
    )


def _load_announcement(db: Session, announcement_id: str) -> Announcement:
    announcement = db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Annonce introuvable.")
    return announcement


def _persist_transition(
    db: Session,
    *,
    announcement: Announcement,
    actor_id: str,
    status: str,
) -> Announcement:
    if announcement.status == status:
        return announcement
    if status == "PUBLISHED" and announcement.status != "DRAFT":
        raise HTTPException(
            status_code=409, detail="Seule une annonce brouillon peut être publiée."
        )
    previous = _snapshot(announcement)
    result = db.execute(
        update(Announcement)
        .where(Announcement.id == announcement.id, Announcement.status == announcement.status)
        .values(status=status, actif=status == "PUBLISHED")
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="L'annonce a changé simultanément.")
    db.expire(announcement)
    current = _load_announcement(db, announcement.id)
    _record_audit(
        db,
        actor_id=actor_id,
        action="ANNOUNCEMENT_PUBLISHED" if status == "PUBLISHED" else "ANNOUNCEMENT_ARCHIVED",
        entity_id=announcement.id,
        metadata={"previous": previous, "current": _snapshot(current)},
    )
    return current


@admin_router.post("")
def create_announcement(
    payload: AnnouncementCreate, request: Request, db: DatabaseSession
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    announcement = Announcement(
        id=str(uuid4()),
        titre=payload.titre,
        texte=payload.texte,
        status="DRAFT",
        actif=False,
        debut_at=_normalize_datetime(payload.debutAt),
        fin_at=_normalize_datetime(payload.finAt),
        created_by_id=actor.id,
    )
    db.add(announcement)
    db.flush()
    _record_audit(
        db,
        actor_id=actor.id,
        action="ANNOUNCEMENT_CREATED",
        entity_id=announcement.id,
        metadata={"titre": announcement.titre, "status": announcement.status, "actif": False},
    )
    db.commit()
    return _announcement_view(announcement)


@admin_router.get("")
def list_admin_announcements(request: Request, db: DatabaseSession) -> list[dict[str, Any]]:
    require_admin(request, db)
    announcements = db.scalars(
        select(Announcement).order_by(Announcement.created_at.desc(), Announcement.id.desc())
    ).all()
    return [_announcement_view(item) for item in announcements]


@admin_router.patch("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdate,
    request: Request,
    db: DatabaseSession,
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    announcement = _load_announcement(db, announcement_id)
    if announcement.status == "ARCHIVED":
        raise HTTPException(status_code=409, detail="Restaurez l'annonce avant de la modifier.")

    changes = payload.model_dump(exclude_unset=True)
    start = _normalize_datetime(changes.get("debutAt")) or announcement.debut_at
    end = _normalize_datetime(changes.get("finAt")) or announcement.fin_at
    try:
        _validate_window(start, end)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    next_status = announcement.status
    if changes.get("actif") is True:
        next_status = "PUBLISHED"
    elif changes.get("actif") is False:
        next_status = "ARCHIVED"
    values: dict[str, Any] = {"status": next_status, "actif": next_status == "PUBLISHED"}
    if changes.get("titre") is not None:
        values["titre"] = changes["titre"]
    if changes.get("texte") is not None:
        values["texte"] = changes["texte"]
    if changes.get("debutAt") is not None:
        values["debut_at"] = _normalize_datetime(changes["debutAt"])
    if changes.get("finAt") is not None:
        values["fin_at"] = _normalize_datetime(changes["finAt"])
    has_changes = any(
        getattr(announcement, field) != value
        for field, value in values.items()
        if field in {"status", "actif", "titre", "texte", "debut_at", "fin_at"}
    )
    if not has_changes:
        return _announcement_view(announcement)

    previous = _snapshot(announcement)
    result = db.execute(
        update(Announcement)
        .where(Announcement.id == announcement.id, Announcement.status == announcement.status)
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="L'annonce a changé simultanément.")
    db.expire(announcement)
    current = _load_announcement(db, announcement.id)
    action = (
        "ANNOUNCEMENT_ARCHIVED"
        if next_status == "ARCHIVED"
        else "ANNOUNCEMENT_PUBLISHED"
        if next_status == "PUBLISHED" and previous["status"] != "PUBLISHED"
        else "ANNOUNCEMENT_UPDATED"
    )
    _record_audit(
        db,
        actor_id=actor.id,
        action=action,
        entity_id=announcement.id,
        metadata={"changes": changes, "previous": previous, "current": _snapshot(current)},
    )
    db.commit()
    return _announcement_view(current)


@admin_router.post("/{announcement_id}/publish")
def publish_announcement(
    announcement_id: str, request: Request, db: DatabaseSession
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    announcement = _load_announcement(db, announcement_id)
    current = _persist_transition(
        db, announcement=announcement, actor_id=actor.id, status="PUBLISHED"
    )
    db.commit()
    return _announcement_view(current)


@admin_router.get("/{announcement_id}/history")
def announcement_history(
    announcement_id: str, request: Request, db: DatabaseSession
) -> list[dict[str, Any]]:
    require_admin(request, db)
    events = db.scalars(
        select(AdminAuditEvent)
        .where(
            AdminAuditEvent.entity_type == "Announcement",
            AdminAuditEvent.entity_id == announcement_id,
        )
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


@admin_router.delete("/{announcement_id}")
def archive_announcement(
    announcement_id: str, request: Request, db: DatabaseSession
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    announcement = _load_announcement(db, announcement_id)
    current = _persist_transition(
        db, announcement=announcement, actor_id=actor.id, status="ARCHIVED"
    )
    db.commit()
    return _announcement_view(current)


@admin_router.post("/{announcement_id}/restore/{event_id}")
def restore_announcement(
    announcement_id: str, event_id: str, request: Request, db: DatabaseSession
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    announcement = _load_announcement(db, announcement_id)
    archive_event = db.scalar(
        select(AdminAuditEvent).where(
            AdminAuditEvent.id == event_id,
            AdminAuditEvent.entity_type == "Announcement",
            AdminAuditEvent.entity_id == announcement_id,
        )
    )
    if archive_event is None:
        raise HTTPException(status_code=404, detail="Événement d'historique introuvable.")
    if archive_event.action != "ANNOUNCEMENT_ARCHIVED":
        raise HTTPException(status_code=409, detail="Seul un archivage peut être restauré.")

    existing_restore = db.scalar(
        select(AdminAuditEvent).where(
            AdminAuditEvent.entity_type == "Announcement",
            AdminAuditEvent.entity_id == announcement_id,
            AdminAuditEvent.action == "ANNOUNCEMENT_RESTORED",
            AdminAuditEvent.metadata_json["sourceEventId"].as_string() == event_id,
        )
    )
    previous = archive_event.metadata_json.get("previous") or {}
    restored_status = (
        "PUBLISHED"
        if previous.get("status") == "PUBLISHED"
        or (
            previous.get("status") is None
            and archive_event.metadata_json.get("previousActiveState")
        )
        else "DRAFT"
    )
    target = {
        "titre": previous.get("titre", announcement.titre),
        "texte": previous.get("texte", announcement.texte),
        "debut_at": _normalize_datetime(datetime.fromisoformat(previous["debutAt"]))
        if previous.get("debutAt")
        else announcement.debut_at,
        "fin_at": _normalize_datetime(datetime.fromisoformat(previous["finAt"]))
        if previous.get("finAt")
        else announcement.fin_at,
        "status": restored_status,
        "actif": restored_status == "PUBLISHED",
    }
    if existing_restore is not None:
        current_values = {
            "titre": announcement.titre,
            "texte": announcement.texte,
            "debut_at": announcement.debut_at,
            "fin_at": announcement.fin_at,
            "status": announcement.status,
            "actif": announcement.actif,
        }
        if current_values == target:
            return _announcement_view(announcement)
        raise HTTPException(status_code=409, detail="L'annonce a changé depuis cette restauration.")
    if announcement.status != "ARCHIVED":
        raise HTTPException(
            status_code=409, detail="Seule une annonce archivée peut être restaurée."
        )

    result = db.execute(
        update(Announcement)
        .where(Announcement.id == announcement_id, Announcement.status == "ARCHIVED")
        .values(**target)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="L'annonce a changé simultanément.")
    db.expire(announcement)
    current = _load_announcement(db, announcement_id)
    _record_audit(
        db,
        actor_id=actor.id,
        action="ANNOUNCEMENT_RESTORED",
        entity_id=announcement_id,
        metadata={
            "sourceEventId": event_id,
            "previous": _snapshot(announcement),
            "current": _snapshot(current),
        },
    )
    db.commit()
    return _announcement_view(current)


@public_router.get("/announcements/active")
def active_announcements(db: DatabaseSession) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    items = db.scalars(
        select(Announcement)
        .where(
            Announcement.actif.is_(True),
            Announcement.status == "PUBLISHED",
            (Announcement.debut_at.is_(None) | (Announcement.debut_at <= now)),
            (Announcement.fin_at.is_(None) | (Announcement.fin_at >= now)),
        )
        .order_by(Announcement.created_at.desc(), Announcement.id.desc())
    ).all()
    return [
        {
            "id": item.id,
            "titre": item.titre,
            "texte": item.texte,
            "debutAt": item.debut_at,
            "finAt": item.fin_at,
        }
        for item in items
    ]
