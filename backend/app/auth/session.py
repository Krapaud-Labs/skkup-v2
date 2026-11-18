"""Validation of persisted web sessions for authenticated API routes."""

from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy.orm import Session

from app.auth.models import AuthSession, User
from app.auth.security import COOKIE_NAME, decode_session_token


def token_from_request(request: Request) -> str | None:
    return request.cookies.get(COOKIE_NAME)


def claims_for_request(
    request: Request, db: Session
) -> tuple[dict | None, User | None, AuthSession | None]:
    token = token_from_request(request)
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
    # Roles are deliberately read from the current database row on every
    # request; changing a role or deactivating the account takes effect now.
    # Issue #7 must separately compare this epoch for extension credentials.
    if user is None or not user.active or user.session_version != claims["sessionVersion"]:
        return None, None, None
    return claims, user, auth_session
