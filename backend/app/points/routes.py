"""Authenticated Viewer endpoints for points and daily progression."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.routes import _claims_for_request, _require_origin
from app.db import get_db
from app.points.service import (
    checkin_daily,
    get_points_summary,
    points_history,
    reward_ticket_inventory,
)

router = APIRouter(prefix="/me", tags=["viewer-points"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def _current_user(request: Request, db: DatabaseSession) -> User:
    _, user, _ = _claims_for_request(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Session invalide.")
    return user


@router.get("/points")
def viewer_points(request: Request, db: DatabaseSession) -> dict:
    user = _current_user(request, db)
    return get_points_summary(db, user.id)


@router.get("")
def viewer_profile(request: Request, db: DatabaseSession) -> dict:
    user = _current_user(request, db)
    return {
        "id": user.id,
        "email": user.email,
        "pseudo": user.pseudo,
        "role": user.role,
        "soldePoints": user.points_balance,
        "streakActuel": user.current_streak,
        "streakMax": user.max_streak,
        "derniereVisiteAt": user.last_visit_at,
        "createdAt": user.created_at,
    }


@router.get("/points/history")
def viewer_points_history(
    request: Request,
    db: DatabaseSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    user = _current_user(request, db)
    return points_history(db, user.id, page=page, limit=limit)


@router.get("/reward-tickets")
def viewer_reward_tickets(
    request: Request,
    db: DatabaseSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    user = _current_user(request, db)
    return reward_ticket_inventory(db, user.id, page=page, limit=limit)


@router.post("/daily-checkin")
def daily_checkin(request: Request, db: DatabaseSession) -> dict:
    _require_origin(request)
    user = _current_user(request, db)
    return checkin_daily(db, user.id)
