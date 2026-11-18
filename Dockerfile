FROM python:3.13.18-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/app ./app
COPY backend/migrations ./migrations
RUN uv sync --locked --no-dev --no-editable

FROM python:3.13.18-slim AS runtime
RUN apt-get update \
    && apt-get install --no-install-recommends -y tzdata \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Paris
WORKDIR /app
COPY --from=builder --chown=10001:10001 /app/backend/.venv /app/backend/.venv
COPY --chown=10001:10001 alembic.ini /app/alembic.ini
COPY --chown=10001:10001 backend/migrations /app/backend/migrations
USER 10001:10001
