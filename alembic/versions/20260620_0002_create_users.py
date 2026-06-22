"""create users table

Revision ID: 20260620_0002
Revises: 20260620_0001
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0002"
down_revision: str | None = "20260620_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("keycloak_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("mobile_number", sa.String(length=20), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column(
            "is_platform_superuser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_users_email_or_mobile_required",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'invited', 'suspended')",
            name="ck_users_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_keycloak_subject"), "users", ["keycloak_subject"], unique=True)
    op.create_index(op.f("ix_users_mobile_number"), "users", ["mobile_number"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_mobile_number"), table_name="users")
    op.drop_index(op.f("ix_users_keycloak_subject"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
