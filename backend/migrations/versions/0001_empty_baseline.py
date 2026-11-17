"""Create the reversible, intentionally empty V2 baseline."""

from collections.abc import Sequence

revision: str = "0001_empty_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Record the baseline without importing or creating product data."""


def downgrade() -> None:
    """Keep the database schema empty; Alembic removes its own version row."""
