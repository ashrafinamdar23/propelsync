"""create late fee rules

Revision ID: 20260620_0033
Revises: 20260620_0032
Create Date: 2026-06-20 00:33:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0033"
down_revision: str | None = "20260620_0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "late_fee_rules",
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("charge_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("calculation_method", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("grace_days", sa.Integer(), nullable=False),
        sa.Column("repeat_interval_days", sa.Integer(), nullable=True),
        sa.Column("max_applications_per_invoice", sa.Integer(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "calculation_method IN ('fixed', 'percent_of_due')",
            name="ck_late_fee_rules_calculation_method",
        ),
        sa.CheckConstraint("amount > 0", name="ck_late_fee_rules_amount_positive"),
        sa.CheckConstraint("grace_days >= 0", name="ck_late_fee_rules_grace_days_non_negative"),
        sa.CheckConstraint(
            "repeat_interval_days IS NULL OR repeat_interval_days > 0",
            name="ck_late_fee_rules_repeat_interval_positive",
        ),
        sa.CheckConstraint(
            "max_applications_per_invoice IS NULL OR max_applications_per_invoice > 0",
            name="ck_late_fee_rules_max_applications_positive",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_late_fee_rules_status"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_late_fee_rules_dates"),
        sa.ForeignKeyConstraint(["charge_type_id"], ["charge_types.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "name", name="uq_late_fee_rules_society_name"),
    )
    op.create_index(op.f("ix_late_fee_rules_charge_type_id"), "late_fee_rules", ["charge_type_id"], unique=False)
    op.create_index(op.f("ix_late_fee_rules_society_id"), "late_fee_rules", ["society_id"], unique=False)
    op.create_index(op.f("ix_late_fee_rules_tenant_id"), "late_fee_rules", ["tenant_id"], unique=False)

    op.create_table(
        "late_fee_applications",
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("late_fee_rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("penalty_invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applied_as_of_date", sa.Date(), nullable=False),
        sa.Column("penalty_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("penalty_amount > 0", name="ck_late_fee_applications_amount_positive"),
        sa.ForeignKeyConstraint(["late_fee_rule_id"], ["late_fee_rules.id"]),
        sa.ForeignKeyConstraint(["original_invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["penalty_invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "late_fee_rule_id",
            "original_invoice_id",
            "applied_as_of_date",
            name="uq_late_fee_applications_invoice_rule_as_of",
        ),
    )
    op.create_index(
        "ix_late_fee_applications_original",
        "late_fee_applications",
        ["tenant_id", "society_id", "original_invoice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_late_fee_applications_applied_as_of_date"),
        "late_fee_applications",
        ["applied_as_of_date"],
        unique=False,
    )
    op.create_index(op.f("ix_late_fee_applications_late_fee_rule_id"), "late_fee_applications", ["late_fee_rule_id"], unique=False)
    op.create_index(op.f("ix_late_fee_applications_original_invoice_id"), "late_fee_applications", ["original_invoice_id"], unique=False)
    op.create_index(op.f("ix_late_fee_applications_penalty_invoice_id"), "late_fee_applications", ["penalty_invoice_id"], unique=False)
    op.create_index(op.f("ix_late_fee_applications_society_id"), "late_fee_applications", ["society_id"], unique=False)
    op.create_index(op.f("ix_late_fee_applications_tenant_id"), "late_fee_applications", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_late_fee_applications_tenant_id"), table_name="late_fee_applications")
    op.drop_index(op.f("ix_late_fee_applications_society_id"), table_name="late_fee_applications")
    op.drop_index(op.f("ix_late_fee_applications_penalty_invoice_id"), table_name="late_fee_applications")
    op.drop_index(op.f("ix_late_fee_applications_original_invoice_id"), table_name="late_fee_applications")
    op.drop_index(op.f("ix_late_fee_applications_late_fee_rule_id"), table_name="late_fee_applications")
    op.drop_index(op.f("ix_late_fee_applications_applied_as_of_date"), table_name="late_fee_applications")
    op.drop_index("ix_late_fee_applications_original", table_name="late_fee_applications")
    op.drop_table("late_fee_applications")
    op.drop_index(op.f("ix_late_fee_rules_tenant_id"), table_name="late_fee_rules")
    op.drop_index(op.f("ix_late_fee_rules_society_id"), table_name="late_fee_rules")
    op.drop_index(op.f("ix_late_fee_rules_charge_type_id"), table_name="late_fee_rules")
    op.drop_table("late_fee_rules")
