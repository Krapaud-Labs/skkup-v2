"""Health endpoints for the V2 service scaffold."""

import os

from fastapi import FastAPI, HTTPException
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI(title="Skkup V2 scaffold", docs_url=None, redoc_url=None, openapi_url=None)


def database_url() -> URL:
    required = ("DB_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required database environment variables: {', '.join(missing)}")

    return URL.create(
        "postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
    )


engine = create_engine(database_url(), pool_pre_ping=True)


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
