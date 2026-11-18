"""Health endpoints for the V2 service scaffold."""

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from app.admin.announcements import admin_router as admin_announcements_router
from app.admin.announcements import public_router as public_announcements_router
from app.admin.audit import router as admin_audit_router
from app.admin.content import admin_router as admin_content_router
from app.admin.content import public_router as public_content_router
from app.admin.dashboard import router as admin_dashboard_router
from app.admin.fraud_flags import router as admin_fraud_flags_router
from app.admin.raffles import router as admin_raffles_router
from app.admin.sponsors import router as admin_sponsors_router
from app.admin.users import router as admin_users_router
from app.auth.routes import router as auth_router
from app.db import engine
from app.points.routes import router as points_router
from app.raffles import admin_draw_router, viewer_router
from app.raffles import public_router as public_raffles_router

app = FastAPI(title="Skkup V2 API", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(auth_router)
app.include_router(points_router)
app.include_router(viewer_router)
app.include_router(public_raffles_router)
app.include_router(admin_users_router)
app.include_router(admin_audit_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_fraud_flags_router)
app.include_router(admin_raffles_router)
app.include_router(admin_draw_router)
app.include_router(admin_sponsors_router)
app.include_router(admin_announcements_router)
app.include_router(public_announcements_router)
app.include_router(admin_content_router)
app.include_router(public_content_router)
allowed_origins = [
    origin.strip().rstrip("/")
    for origin in os.environ.get(
        "AUTH_ALLOWED_ORIGINS",
        "http://localhost:3010,http://127.0.0.1:3010,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health/live", include_in_schema=False)
def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready", include_in_schema=False)
def ready() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(status_code=503, detail="database unavailable") from error
    return {"status": "ready"}


@app.exception_handler(RequestValidationError)
async def auth_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    """Return a safe, useful validation message without echoing credentials."""
    fields = {str(item["loc"][-1]) for item in error.errors() if len(item.get("loc", ())) > 1}
    if "email" in fields:
        message = "Adresse email invalide."
    elif "pseudo" in fields:
        message = "Le pseudo doit contenir au moins 2 caractères."
    elif "accepteReglement" in fields:
        message = "Le règlement du jeu doit être accepté."
    elif fields.intersection({"motDePasse", "nouveauMotDePasse", "ancienMotDePasse"}):
        message = "Le mot de passe ne respecte pas les exigences."
    else:
        message = "Vérifie les champs saisis."
    return JSONResponse(
        status_code=400,
        content={"statusCode": 400, "error": "Bad Request", "message": message},
    )
