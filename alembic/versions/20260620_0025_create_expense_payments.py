"""create expense payments

Revision ID: 20260620_0025
Revises: 20260620_0024
Create Date: 2026-06-20 00:25:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0025"
down_revision: str | None = "20260620_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expense_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("unapplied_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_mode", sa.String(length=30), nullable=False),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_expense_payments_amount_positive"),
        sa.CheckConstraint("unapplied_amount >= 0", name="ck_expense_payments_unapplied_non_negative"),
        sa.CheckConstraint(
            "payment_mode IN ('cash', 'bank_transfer', 'cheque', 'upi', 'card', 'other')",
            name="ck_expense_payments_mode",
        ),
        sa.CheckConstraint("status IN ('paid', 'reversed')", name="ck_expense_payments_status"),
        sa.ForeignKeyConstraint(["payment_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_expense_payments_payment_account_id"), "expense_payments", ["payment_account_id"])
    op.create_index(op.f("ix_expense_payments_society_id"), "expense_payments", ["society_id"])
    op.create_index(op.f("ix_expense_payments_tenant_id"), "expense_payments", ["tenant_id"])
    op.create_index(op.f("ix_expense_payments_vendor_id"), "expense_payments", ["vendor_id"])

    op.create_table(
        "expense_payment_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expense_payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("allocated_amount > 0", name="ck_expense_payment_allocations_amount_positive"),
        sa.CheckConstraint("status IN ('active', 'reversed')", name="ck_expense_payment_allocations_status"),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"]),
        sa.ForeignKeyConstraint(["expense_payment_id"], ["expense_payments.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "expense_payment_id", "expense_id", name="uq_expense_payment_allocation"),
    )
    op.create_index(op.f("ix_expense_payment_allocations_expense_id"), "expense_payment_allocations", ["expense_id"])
    op.create_index(
        op.f("ix_expense_payment_allocations_expense_payment_id"),
        "expense_payment_allocations",
        ["expense_payment_id"],
    )
    op.create_index(op.f("ix_expense_payment_allocations_society_id"), "expense_payment_allocations", ["society_id"])
    op.create_index(op.f("ix_expense_payment_allocations_tenant_id"), "expense_payment_allocations", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_expense_payment_allocations_tenant_id"), table_name="expense_payment_allocations")
    op.drop_index(op.f("ix_expense_payment_allocations_society_id"), table_name="expense_payment_allocations")
    op.drop_index(
        op.f("ix_expense_payment_allocations_expense_payment_id"),
        table_name="expense_payment_allocations",
    )
    op.drop_index(op.f("ix_expense_payment_allocations_expense_id"), table_name="expense_payment_allocations")
    op.drop_table("expense_payment_allocations")
    op.drop_index(op.f("ix_expense_payments_vendor_id"), table_name="expense_payments")
    op.drop_index(op.f("ix_expense_payments_tenant_id"), table_name="expense_payments")
    op.drop_index(op.f("ix_expense_payments_society_id"), table_name="expense_payments")
    op.drop_index(op.f("ix_expense_payments_payment_account_id"), table_name="expense_payments")
    op.drop_table("expense_payments")
