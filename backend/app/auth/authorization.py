"""Shared server-side role checks for protected Admin routes."""

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.session import claims_for_request


def require_admin(request: Request, db: Session) -> User:
    """Require a valid persisted web session and a current database Admin role."""
    _, user, _ = claims_for_request(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Session invalide.")
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès administrateur requis.")
    return user
