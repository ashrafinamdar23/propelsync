"""create billing rules

Revision ID: 20260620_0016
Revises: 20260620_0015
Create Date: 2026-06-20 00:16:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0016"
down_revision: str | None = "20260620_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "billing_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("charge_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("wing_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("flat_type_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("calculation_method", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("area_basis", sa.String(length=30), nullable=True),
        sa.Column("frequency", sa.String(length=30), nullable=False),
        sa.Column("scope_type", sa.String(length=30), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
            "calculation_method IN ('fixed', 'area_based', 'parking_based', 'flat_type_fixed', 'manual')",
            name="ck_billing_rules_calculation_method",
        ),
        sa.CheckConstraint(
            "area_basis IS NULL OR area_basis IN ('carpet_area', 'built_up_area')",
            name="ck_billing_rules_area_basis",
        ),
        sa.CheckConstraint(
            "frequency IN ('monthly', 'quarterly', 'half_yearly', 'yearly', 'one_time')",
            name="ck_billing_rules_frequency",
        ),
        sa.CheckConstraint(
            "scope_type IN ('all_flats', 'building', 'wing', 'flat_type')",
            name="ck_billing_rules_scope_type",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_billing_rules_status"),
        sa.CheckConstraint("amount IS NULL OR amount >= 0", name="ck_billing_rules_amount_non_negative"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_billing_rules_dates"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"]),
        sa.ForeignKeyConstraint(["charge_type_id"], ["charge_types.id"]),
        sa.ForeignKeyConstraint(["flat_type_id"], ["flat_types.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["wing_id"], ["wings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "name", name="uq_billing_rules_society_name"),
    )
    op.create_index(op.f("ix_billing_rules_building_id"), "billing_rules", ["building_id"])
    op.create_index(op.f("ix_billing_rules_charge_type_id"), "billing_rules", ["charge_type_id"])
    op.create_index(op.f("ix_billing_rules_flat_type_id"), "billing_rules", ["flat_type_id"])
    op.create_index(op.f("ix_billing_rules_society_id"), "billing_rules", ["society_id"])
    op.create_index(op.f("ix_billing_rules_tenant_id"), "billing_rules", ["tenant_id"])
    op.create_index(op.f("ix_billing_rules_wing_id"), "billing_rules", ["wing_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_billing_rules_wing_id"), table_name="billing_rules")
    op.drop_index(op.f("ix_billing_rules_tenant_id"), table_name="billing_rules")
    op.drop_index(op.f("ix_billing_rules_society_id"), table_name="billing_rules")
    op.drop_index(op.f("ix_billing_rules_flat_type_id"), table_name="billing_rules")
    op.drop_index(op.f("ix_billing_rules_charge_type_id"), table_name="billing_rules")
    op.drop_index(op.f("ix_billing_rules_building_id"), table_name="billing_rules")
    op.drop_table("billing_rules")
