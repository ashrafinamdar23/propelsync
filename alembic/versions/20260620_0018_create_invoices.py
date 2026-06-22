"""create invoices

Revision ID: 20260620_0018
Revises: 20260620_0017
Create Date: 2026-06-20 00:18:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0018"
down_revision: str | None = "20260620_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invoice_number", sa.String(length=50), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("billing_period_start", sa.Date(), nullable=False),
        sa.Column("billing_period_end", sa.Date(), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_due", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'issued', 'partially_paid', 'paid', 'overdue', 'cancelled')",
            name="ck_invoices_status",
        ),
        sa.CheckConstraint("total_amount >= 0", name="ck_invoices_total_amount_non_negative"),
        sa.CheckConstraint("amount_paid >= 0", name="ck_invoices_amount_paid_non_negative"),
        sa.CheckConstraint("amount_due >= 0", name="ck_invoices_amount_due_non_negative"),
        sa.CheckConstraint("billing_period_end >= billing_period_start", name="ck_invoices_period_dates"),
        sa.CheckConstraint("due_date >= invoice_date", name="ck_invoices_due_date"),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "invoice_number", name="uq_invoices_number"),
    )
    op.create_index("uq_invoices_flat_period", "invoices", ["tenant_id", "society_id", "flat_id", "billing_period_start", "billing_period_end"], unique=True)
    op.create_index(op.f("ix_invoices_flat_id"), "invoices", ["flat_id"])
    op.create_index(op.f("ix_invoices_owner_id"), "invoices", ["owner_id"])
    op.create_index(op.f("ix_invoices_society_id"), "invoices", ["society_id"])
    op.create_index(op.f("ix_invoices_tenant_id"), "invoices", ["tenant_id"])

    op.create_table(
        "invoice_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("charge_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("billing_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("line_number > 0", name="ck_invoice_line_items_line_number"),
        sa.CheckConstraint("quantity >= 0", name="ck_invoice_line_items_quantity_non_negative"),
        sa.CheckConstraint("unit_amount >= 0", name="ck_invoice_line_items_unit_amount_non_negative"),
        sa.CheckConstraint("line_amount >= 0", name="ck_invoice_line_items_line_amount_non_negative"),
        sa.ForeignKeyConstraint(["billing_rule_id"], ["billing_rules.id"]),
        sa.ForeignKeyConstraint(["charge_type_id"], ["charge_types.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "invoice_id", "line_number", name="uq_invoice_line_number"),
    )
    op.create_index(op.f("ix_invoice_line_items_billing_rule_id"), "invoice_line_items", ["billing_rule_id"])
    op.create_index(op.f("ix_invoice_line_items_charge_type_id"), "invoice_line_items", ["charge_type_id"])
    op.create_index(op.f("ix_invoice_line_items_invoice_id"), "invoice_line_items", ["invoice_id"])
    op.create_index(op.f("ix_invoice_line_items_society_id"), "invoice_line_items", ["society_id"])
    op.create_index(op.f("ix_invoice_line_items_tenant_id"), "invoice_line_items", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_invoice_line_items_tenant_id"), table_name="invoice_line_items")
    op.drop_index(op.f("ix_invoice_line_items_society_id"), table_name="invoice_line_items")
    op.drop_index(op.f("ix_invoice_line_items_invoice_id"), table_name="invoice_line_items")
    op.drop_index(op.f("ix_invoice_line_items_charge_type_id"), table_name="invoice_line_items")
    op.drop_index(op.f("ix_invoice_line_items_billing_rule_id"), table_name="invoice_line_items")
    op.drop_table("invoice_line_items")
    op.drop_index(op.f("ix_invoices_tenant_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_society_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_owner_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_flat_id"), table_name="invoices")
    op.drop_index("uq_invoices_flat_period", table_name="invoices")
    op.drop_table("invoices")
