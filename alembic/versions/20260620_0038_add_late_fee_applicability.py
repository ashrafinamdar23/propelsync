"""add late fee applicability

Revision ID: 20260620_0038
Revises: 20260620_0037
Create Date: 2026-06-20 00:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0038"
down_revision: Union[str, None] = "20260620_0037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "billing_rule_late_fee_rules",
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("billing_rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("late_fee_rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_billing_rule_late_fee_rules_dates"),
        sa.CheckConstraint("priority >= 0", name="ck_billing_rule_late_fee_rules_priority"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_billing_rule_late_fee_rules_status"),
        sa.ForeignKeyConstraint(["billing_rule_id"], ["billing_rules.id"]),
        sa.ForeignKeyConstraint(["late_fee_rule_id"], ["late_fee_rules.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "billing_rule_id",
            "late_fee_rule_id",
            name="uq_billing_rule_late_fee_rule",
        ),
    )
    op.create_index(op.f("ix_billing_rule_late_fee_rules_billing_rule_id"), "billing_rule_late_fee_rules", ["billing_rule_id"])
    op.create_index(op.f("ix_billing_rule_late_fee_rules_late_fee_rule_id"), "billing_rule_late_fee_rules", ["late_fee_rule_id"])
    op.create_index(op.f("ix_billing_rule_late_fee_rules_society_id"), "billing_rule_late_fee_rules", ["society_id"])
    op.create_index(op.f("ix_billing_rule_late_fee_rules_tenant_id"), "billing_rule_late_fee_rules", ["tenant_id"])

    op.create_table(
        "invoice_late_fee_rules",
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("late_fee_rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("priority >= 0", name="ck_invoice_late_fee_rules_priority"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_invoice_late_fee_rules_status"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["late_fee_rule_id"], ["late_fee_rules.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "invoice_id",
            "late_fee_rule_id",
            name="uq_invoice_late_fee_rule",
        ),
    )
    op.create_index(op.f("ix_invoice_late_fee_rules_invoice_id"), "invoice_late_fee_rules", ["invoice_id"])
    op.create_index(op.f("ix_invoice_late_fee_rules_late_fee_rule_id"), "invoice_late_fee_rules", ["late_fee_rule_id"])
    op.create_index(op.f("ix_invoice_late_fee_rules_society_id"), "invoice_late_fee_rules", ["society_id"])
    op.create_index(op.f("ix_invoice_late_fee_rules_tenant_id"), "invoice_late_fee_rules", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_invoice_late_fee_rules_tenant_id"), table_name="invoice_late_fee_rules")
    op.drop_index(op.f("ix_invoice_late_fee_rules_society_id"), table_name="invoice_late_fee_rules")
    op.drop_index(op.f("ix_invoice_late_fee_rules_late_fee_rule_id"), table_name="invoice_late_fee_rules")
    op.drop_index(op.f("ix_invoice_late_fee_rules_invoice_id"), table_name="invoice_late_fee_rules")
    op.drop_table("invoice_late_fee_rules")

    op.drop_index(op.f("ix_billing_rule_late_fee_rules_tenant_id"), table_name="billing_rule_late_fee_rules")
    op.drop_index(op.f("ix_billing_rule_late_fee_rules_society_id"), table_name="billing_rule_late_fee_rules")
    op.drop_index(op.f("ix_billing_rule_late_fee_rules_late_fee_rule_id"), table_name="billing_rule_late_fee_rules")
    op.drop_index(op.f("ix_billing_rule_late_fee_rules_billing_rule_id"), table_name="billing_rule_late_fee_rules")
    op.drop_table("billing_rule_late_fee_rules")
