"""Admin versioned editorial content and published-only public reads."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.admin.models import ContentVersion, ManagedContent
from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent
from app.auth.routes import _require_origin
from app.db import get_db

admin_router = APIRouter(prefix="/admin/content", tags=["admin-content"])
public_router = APIRouter(prefix="/content", tags=["content"])
DatabaseSession = Annotated[Session, Depends(get_db)]
CONTENT_TYPES = {"LANDING", "LEGAL", "ANNOUNCEMENT", "FAQ", "MEDIA"}


class ContentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=120)
    type: str = Field(pattern=r"^(LANDING|LEGAL|ANNOUNCEMENT|FAQ|MEDIA)$")
    locale: str = Field(pattern=r"^(fr|en)$")
    data: dict[str, Any]


class ContentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: dict[str, Any]


def _view(content: ManagedContent) -> dict[str, Any]:
    return {
        "id": content.id,
        "slug": content.slug,
        "type": content.type,
        "locale": content.locale,
        "status": content.status,
        "data": content.data,
        "version": content.version,
        "publishedAt": content.published_at,
        "createdAt": content.created_at,
        "updatedAt": content.updated_at,
        "createdById": content.created_by_id,
        "updatedById": content.updated_by_id,
    }


def _load(db: Session, content_id: str) -> ManagedContent:
    content = db.get(ManagedContent, content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Contenu introuvable.")
    return content


def _audit(
    db: Session,
    *,
    actor_id: str,
    action: str,
    content: ManagedContent,
    previous: dict[str, Any] | None = None,
) -> None:
    db.add(
        AdminAuditEvent(
            id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            entity_type="ManagedContent",
            entity_id=content.id,
            metadata_json={
                "previous": previous,
                "current": {
                    "version": content.version,
                    "status": content.status,
                    "slug": content.slug,
                    "type": content.type,
                    "locale": content.locale,
                },
            },
        )
    )


def _snapshot(db: Session, content: ManagedContent, actor_id: str) -> None:
    db.add(
        ContentVersion(
            id=str(uuid4()),
            content_id=content.id,
            version=content.version,
            data=content.data,
            status=content.status,
            created_by_id=actor_id,
        )
    )


@admin_router.get("")
def list_content(request: Request, db: DatabaseSession) -> list[dict[str, Any]]:
    require_admin(request, db)
    rows = db.scalars(
        select(ManagedContent).order_by(ManagedContent.updated_at.desc(), ManagedContent.id)
    ).all()
    return [_view(row) for row in rows]


@admin_router.post("")
def create_content(payload: ContentCreate, request: Request, db: DatabaseSession) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    content = ManagedContent(
        id=str(uuid4()),
        slug=payload.slug,
        type=payload.type,
        locale=payload.locale,
        status="DRAFT",
        data=payload.data,
        version=1,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(content)
    _snapshot(db, content, actor.id)
    _audit(db, actor_id=actor.id, action="CONTENT_CREATED", content=content)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Ce slug existe déjà pour ce type et cette langue."
        ) from error
    db.refresh(content)
    return _view(content)


@admin_router.get("/{content_id}")
def get_content(content_id: str, request: Request, db: DatabaseSession) -> dict[str, Any]:
    require_admin(request, db)
    return _view(_load(db, content_id))


@admin_router.patch("/{content_id}")
def update_content(
    content_id: str, payload: ContentUpdate, request: Request, db: DatabaseSession
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    content = _load(db, content_id)
    if content.data == payload.data:
        return _view(content)
    previous = {"version": content.version, "status": content.status, "data": content.data}
    result = db.execute(
        update(ManagedContent)
        .where(ManagedContent.id == content_id, ManagedContent.version == content.version)
        .values(
            data=payload.data,
            status="DRAFT",
            version=content.version + 1,
            updated_by_id=actor.id,
            published_at=None,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="Le contenu a changé simultanément.")
    db.expire(content)
    content = _load(db, content_id)
    _snapshot(db, content, actor.id)
    _audit(db, actor_id=actor.id, action="CONTENT_UPDATED", content=content, previous=previous)
    db.commit()
    return _view(content)


@admin_router.post("/{content_id}/publish")
def publish_content(content_id: str, request: Request, db: DatabaseSession) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    content = _load(db, content_id)
    if content.status == "PUBLISHED":
        return _view(content)
    previous = {"version": content.version, "status": content.status}
    result = db.execute(
        update(ManagedContent)
        .where(ManagedContent.id == content_id, ManagedContent.version == content.version)
        .values(
            status="PUBLISHED",
            version=content.version + 1,
            updated_by_id=actor.id,
            published_at=datetime.now(UTC),
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="Le contenu a changé simultanément.")
    db.expire(content)
    content = _load(db, content_id)
    _snapshot(db, content, actor.id)
    _audit(db, actor_id=actor.id, action="CONTENT_PUBLISHED", content=content, previous=previous)
    db.commit()
    return _view(content)


@admin_router.get("/{content_id}/history")
def content_history(content_id: str, request: Request, db: DatabaseSession) -> list[dict[str, Any]]:
    require_admin(request, db)
    _load(db, content_id)
    versions = db.scalars(
        select(ContentVersion)
        .where(ContentVersion.content_id == content_id)
        .order_by(ContentVersion.version.desc())
        .limit(100)
    ).all()
    return [
        {
            "id": row.id,
            "version": row.version,
            "data": row.data,
            "status": row.status,
            "createdById": row.created_by_id,
            "createdAt": row.created_at,
        }
        for row in versions
    ]


@admin_router.post("/{content_id}/restore/{version}")
def restore_content(
    content_id: str, version: int, request: Request, db: DatabaseSession
) -> dict[str, Any]:
    actor = require_admin(request, db)
    _require_origin(request)
    content = _load(db, content_id)
    source = db.scalar(
        select(ContentVersion).where(
            ContentVersion.content_id == content_id, ContentVersion.version == version
        )
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Version introuvable.")
    if content.data == source.data and content.status == source.status:
        return _view(content)
    previous = {"version": content.version, "status": content.status, "data": content.data}
    result = db.execute(
        update(ManagedContent)
        .where(ManagedContent.id == content_id, ManagedContent.version == content.version)
        .values(
            data=source.data,
            status=source.status,
            version=content.version + 1,
            updated_by_id=actor.id,
            published_at=datetime.now(UTC) if source.status == "PUBLISHED" else None,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise HTTPException(status_code=409, detail="Le contenu a changé simultanément.")
    db.expire(content)
    content = _load(db, content_id)
    _snapshot(db, content, actor.id)
    _audit(db, actor_id=actor.id, action="CONTENT_RESTORED", content=content, previous=previous)
    db.commit()
    return _view(content)


@public_router.get("/{content_type}/{locale}/{slug}")
def get_published_content(
    content_type: str, locale: str, slug: str, db: DatabaseSession
) -> dict[str, Any]:
    row = db.scalar(
        select(ManagedContent).where(
            ManagedContent.type == content_type.upper(),
            ManagedContent.locale == locale,
            ManagedContent.slug == slug,
            ManagedContent.status == "PUBLISHED",
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Contenu introuvable.")
    return {
        "slug": row.slug,
        "type": row.type,
        "locale": row.locale,
        "data": row.data,
        "updatedAt": row.updated_at,
    }
