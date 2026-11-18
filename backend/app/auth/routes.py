"""V1-shaped member authentication and session lifecycle endpoints."""

import os
import threading
import time
from collections import deque
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import AuthSession, User
from app.auth.schemas import ChangePasswordRequest, LoginRequest, RegisterRequest
from app.auth.security import (
    COOKIE_NAME,
    COOKIE_SECURE,
    SESSION_SECONDS,
    create_session_token,
    decode_session_token,
    hash_password,
    new_session_id,
    verify_password,
)
from app.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
DatabaseSession = Annotated[Session, Depends(get_db)]
_rate_lock = threading.Lock()
_attempts: dict[tuple[str, str], deque[float]] = {}
_RATE_RULES = {"register": (5, 3600), "login": (10, 60), "password": (3, 3600)}


def _origin_allowed(request: Request) -> bool:
    origin = request.headers.get("origin")
    if origin is None:
        return False
    configured = os.environ.get(
        "AUTH_ALLOWED_ORIGINS",
        "http://localhost:3010,http://127.0.0.1:3010,http://localhost:3000,http://127.0.0.1:3000",
    )
    allowed = {item.strip().rstrip("/") for item in configured.split(",") if item.strip()}
    return origin.rstrip("/") in allowed


def _require_origin(request: Request) -> None:
    if not _origin_allowed(request):
        raise HTTPException(status_code=403, detail="Request origin is not allowed.")


def _rate_limit(request: Request, action: str) -> None:
    limit, window = _RATE_RULES[action]
    address = request.client.host if request.client else "unknown"
    now = time.monotonic()
    key = (action, address)
    with _rate_lock:
        stale = [
            item for item, values in _attempts.items() if not values or now - values[-1] > 3600
        ]
        for item in stale:
            _attempts.pop(item, None)
        if len(_attempts) >= 10_000 and key not in _attempts:
            for item in list(_attempts)[:1_000]:
                _attempts.pop(item, None)
        bucket = _attempts.setdefault(key, deque())
        while bucket and now - bucket[0] >= window:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(window - (now - bucket[0])))
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts.",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)


def _token_from_request(request: Request) -> str | None:
    return request.cookies.get(COOKIE_NAME)


def _claims_for_request(
    request: Request, db: Session
) -> tuple[dict | None, User | None, AuthSession | None]:
    token = _token_from_request(request)
    if not token:
        return None, None, None
    claims = decode_session_token(token)
    if not claims:
        return None, None, None
    auth_session = db.get(AuthSession, claims["sid"])
    if (
        auth_session is None
        or auth_session.user_id != claims["sub"]
        or auth_session.revoked_at is not None
        or auth_session.expires_at <= datetime.now(UTC)
        or auth_session.session_version != claims["sessionVersion"]
    ):
        return None, None, None
    user = db.get(User, claims["sub"])
    # The account epoch also invalidates future extension credentials once
    # that domain is implemented; issue #7 must enforce the same comparison.
    if user is None or not user.active or user.session_version != claims["sessionVersion"]:
        return None, None, None
    return claims, user, auth_session


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def _issue_session(db: Session, user: User) -> str:
    session_id = new_session_id()
    token, expires = create_session_token(
        user_id=user.id,
        email=user.email,
        session_id=session_id,
        session_version=user.session_version,
    )
    db.add(
        AuthSession(
            id=session_id,
            user_id=user.id,
            session_version=user.session_version,
            expires_at=expires,
        )
    )
    return token


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: DatabaseSession,
) -> dict[str, str]:
    _require_origin(request)
    _rate_limit(request, "register")
    if payload.accepteReglement is not True:
        raise HTTPException(status_code=400, detail="Le règlement du jeu doit être accepté.")
    user = User(
        id=new_session_id(),
        email=payload.email,
        password_hash=hash_password(payload.motDePasse),
        pseudo=payload.pseudo,
        role="VIEWER",
        active=True,
        session_version=0,
        terms_accepted_at=datetime.now(UTC),
    )
    db.add(user)
    try:
        db.flush()
        token = _issue_session(db, user)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Inscription impossible avec ces informations."
        ) from error
    _set_session_cookie(response, token)
    return {"pseudo": user.pseudo}


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DatabaseSession,
) -> dict[str, str]:
    _require_origin(request)
    _rate_limit(request, "login")
    user = db.scalar(select(User).where(User.email == payload.email))
    if (
        user is None
        or not user.active
        or not verify_password(payload.motDePasse, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Identifiants invalides.")
    token = _issue_session(db, user)
    db.commit()
    _set_session_cookie(response, token)
    return {"pseudo": user.pseudo}


@router.get("/session")
def current_session(request: Request, response: Response, db: DatabaseSession) -> dict:
    _, user, _ = _claims_for_request(request, db)
    if user is None:
        if _token_from_request(request):
            _clear_session_cookie(response)
        return {"authentifie": False, "profil": None}
    return {
        "authentifie": True,
        "profil": {
            "id": user.id,
            "email": user.email,
            "pseudo": user.pseudo,
            "role": user.role,
            "soldePoints": user.points_balance,
            "streakActuel": user.current_streak,
            "streakMax": user.max_streak,
            "derniereVisiteAt": user.last_visit_at,
            "createdAt": user.created_at,
        },
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: DatabaseSession,
) -> Response:
    _require_origin(request)
    _, _, auth_session = _claims_for_request(request, db)
    if auth_session is not None:
        auth_session.revoked_at = datetime.now(UTC)
        db.commit()
    _clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    db: DatabaseSession,
) -> Response:
    _require_origin(request)
    _rate_limit(request, "password")
    _, user, _ = _claims_for_request(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Session invalide.")
    if not verify_password(payload.ancienMotDePasse, user.password_hash):
        raise HTTPException(status_code=401, detail="Ancien mot de passe incorrect.")
    if payload.ancienMotDePasse == payload.nouveauMotDePasse:
        raise HTTPException(
            status_code=400,
            detail="Le nouveau mot de passe doit être différent de l’ancien.",
        )
    now = datetime.now(UTC)
    db.execute(
        update(User).where(User.id == user.id).values(
            password_hash=hash_password(payload.nouveauMotDePasse),
            session_version=User.session_version + 1,
        )
    )
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    db.commit()
    _clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
