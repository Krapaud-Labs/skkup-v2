"""Add Admin-managed announcements and versioned editorial content."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_admin_editorial"
down_revision: str | Sequence[str] | None = "0004_admin_user_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("titre", sa.String(length=160), nullable=False),
        sa.Column("texte", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("actif", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("debut_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fin_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')", name="ck_announcements_status"
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_announcements_created", "announcements", ["created_at", "id"])

    op.create_table(
        "managed_contents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("type", sa.String(length=24), nullable=False),
        sa.Column("locale", sa.String(length=2), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column("updated_by_id", sa.String(length=36), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "type IN ('LANDING', 'LEGAL', 'ANNOUNCEMENT', 'FAQ', 'MEDIA')",
            name="ck_managed_contents_type",
        ),
        sa.CheckConstraint("locale IN ('fr', 'en')", name="ck_managed_contents_locale"),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED')", name="ck_managed_contents_status"),
        sa.CheckConstraint("version >= 1", name="ck_managed_contents_version_positive"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", "type", "locale", name="uq_managed_contents_slug_type_locale"),
    )
    op.create_index(
        "ix_managed_contents_type_locale_status",
        "managed_contents",
        ["type", "locale", "status"],
    )

    op.create_table(
        "content_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("content_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("version >= 1", name="ck_content_versions_version_positive"),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED')", name="ck_content_versions_status"),
        sa.ForeignKeyConstraint(["content_id"], ["managed_contents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_id", "version", name="uq_content_versions_content_version"),
    )
    op.create_index(
        "ix_content_versions_content_created", "content_versions", ["content_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_content_versions_content_created", table_name="content_versions")
    op.drop_table("content_versions")
    op.drop_index("ix_managed_contents_type_locale_status", table_name="managed_contents")
    op.drop_table("managed_contents")
    op.drop_index("ix_announcements_created", table_name="announcements")
    op.drop_table("announcements")
