"""Shared database-state snapshots for authorization-denial contract checks."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, select


def snapshot_database(engine: Engine, metadata: Any) -> dict[str, tuple[tuple[Any, ...], ...]]:
    """Return every table row in stable order for before/after denial assertions."""
    snapshot: dict[str, tuple[tuple[Any, ...], ...]] = {}
    with engine.connect() as connection:
        for table in metadata.sorted_tables:
            rows = connection.execute(select(table)).all()
            snapshot[table.name] = tuple(sorted((tuple(row) for row in rows), key=repr))
    return snapshot
