"""create flat ownerships table

Revision ID: 20260620_0010
Revises: 20260620_0009
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0010"
down_revision: str | None = "20260620_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "flat_ownerships",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ownership_type", sa.String(length=30), nullable=False),
        sa.Column("ownership_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
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
            "ownership_type IN ('primary_owner', 'co_owner')",
            name="ck_flat_ownerships_ownership_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_flat_ownerships_status",
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_flat_ownerships_effective_dates",
        ),
        sa.CheckConstraint(
            "ownership_percentage IS NULL OR "
            "(ownership_percentage > 0 AND ownership_percentage <= 100)",
            name="ck_flat_ownerships_percentage",
        ),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_flat_ownerships_flat_id"),
        "flat_ownerships",
        ["flat_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_flat_ownerships_owner_id"),
        "flat_ownerships",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_flat_ownerships_society_id"),
        "flat_ownerships",
        ["society_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_flat_ownerships_tenant_id"),
        "flat_ownerships",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "uq_flat_ownerships_current_primary_owner",
        "flat_ownerships",
        ["tenant_id", "society_id", "flat_id"],
        unique=True,
        postgresql_where=sa.text(
            "ownership_type = 'primary_owner' AND effective_to IS NULL AND status = 'active'"
        ),
    )
    op.create_index(
        "uq_flat_ownerships_flat_owner_start",
        "flat_ownerships",
        ["tenant_id", "society_id", "flat_id", "owner_id", "effective_from"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_flat_ownerships_flat_owner_start", table_name="flat_ownerships")
    op.drop_index("uq_flat_ownerships_current_primary_owner", table_name="flat_ownerships")
    op.drop_index(op.f("ix_flat_ownerships_tenant_id"), table_name="flat_ownerships")
    op.drop_index(op.f("ix_flat_ownerships_society_id"), table_name="flat_ownerships")
    op.drop_index(op.f("ix_flat_ownerships_owner_id"), table_name="flat_ownerships")
    op.drop_index(op.f("ix_flat_ownerships_flat_id"), table_name="flat_ownerships")
    op.drop_table("flat_ownerships")
