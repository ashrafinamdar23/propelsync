"""create charge types

Revision ID: 20260620_0013
Revises: 20260620_0012
Create Date: 2026-06-20 00:13:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0013"
down_revision: str | None = "20260620_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "charge_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("charge_category", sa.String(length=30), nullable=False),
        sa.Column("revenue_account_code", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "charge_category IN ('regular', 'fund', 'utility', 'penalty', 'tax', 'adjustment', 'other')",
            name="ck_charge_types_charge_category",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_charge_types_status"),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "name", name="uq_charge_types_society_name"),
        sa.UniqueConstraint("tenant_id", "society_id", "code", name="uq_charge_types_society_code"),
    )
    op.create_index(op.f("ix_charge_types_society_id"), "charge_types", ["society_id"])
    op.create_index(op.f("ix_charge_types_tenant_id"), "charge_types", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_charge_types_tenant_id"), table_name="charge_types")
    op.drop_index(op.f("ix_charge_types_society_id"), table_name="charge_types")
    op.drop_table("charge_types")
