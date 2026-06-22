"""create membership tables

Revision ID: 20260620_0008
Revises: 20260620_0007
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0008"
down_revision: str | None = "20260620_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_memberships",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
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
        sa.CheckConstraint("role IN ('tenant_admin')", name="ck_tenant_memberships_role"),
        sa.CheckConstraint(
            "status IN ('active', 'invited', 'suspended')",
            name="ck_tenant_memberships_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "user_id",
            "role",
            name="uq_tenant_memberships_tenant_user_role",
        ),
    )
    op.create_index(
        op.f("ix_tenant_memberships_tenant_id"),
        "tenant_memberships",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tenant_memberships_user_id"),
        "tenant_memberships",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "society_memberships",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
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
            (
                "role IN ("
                "'society_admin', "
                "'treasurer', "
                "'accountant', "
                "'auditor', "
                "'committee_member', "
                "'flat_owner', "
                "'read_only_resident'"
                ")"
            ),
            name="ck_society_memberships_role",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'invited', 'suspended')",
            name="ck_society_memberships_status",
        ),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "user_id",
            "role",
            name="uq_society_memberships_scope_user_role",
        ),
    )
    op.create_index(
        op.f("ix_society_memberships_society_id"),
        "society_memberships",
        ["society_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_society_memberships_tenant_id"),
        "society_memberships",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_society_memberships_user_id"),
        "society_memberships",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_society_memberships_user_id"), table_name="society_memberships")
    op.drop_index(op.f("ix_society_memberships_tenant_id"), table_name="society_memberships")
    op.drop_index(op.f("ix_society_memberships_society_id"), table_name="society_memberships")
    op.drop_table("society_memberships")
    op.drop_index(op.f("ix_tenant_memberships_user_id"), table_name="tenant_memberships")
    op.drop_index(op.f("ix_tenant_memberships_tenant_id"), table_name="tenant_memberships")
    op.drop_table("tenant_memberships")
