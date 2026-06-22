"""create expenses

Revision ID: 20260620_0024
Revises: 20260620_0023
Create Date: 2026-06-20 00:24:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0024"
down_revision: str | None = "20260620_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expense_category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expense_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expense_type", sa.String(length=30), nullable=False),
        sa.Column("vendor_bill_number", sa.String(length=100), nullable=True),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_due", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("payment_status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("expense_date <= due_date", name="ck_expenses_due_date"),
        sa.CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        sa.CheckConstraint("tax_amount >= 0", name="ck_expenses_tax_amount_non_negative"),
        sa.CheckConstraint("total_amount >= 0", name="ck_expenses_total_amount_non_negative"),
        sa.CheckConstraint("amount_paid >= 0", name="ck_expenses_amount_paid_non_negative"),
        sa.CheckConstraint("amount_due >= 0", name="ck_expenses_amount_due_non_negative"),
        sa.CheckConstraint(
            "expense_type IN ('vendor_bill', 'cash_expense', 'other')",
            name="ck_expenses_type",
        ),
        sa.CheckConstraint("status IN ('recorded', 'approved', 'cancelled')", name="ck_expenses_status"),
        sa.CheckConstraint(
            "payment_status IN ('unpaid', 'partially_paid', 'paid')",
            name="ck_expenses_payment_status",
        ),
        sa.ForeignKeyConstraint(["expense_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["expense_category_id"], ["expense_categories.id"]),
        sa.ForeignKeyConstraint(["payment_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_expenses_expense_account_id"), "expenses", ["expense_account_id"])
    op.create_index(op.f("ix_expenses_expense_category_id"), "expenses", ["expense_category_id"])
    op.create_index(op.f("ix_expenses_payment_account_id"), "expenses", ["payment_account_id"])
    op.create_index(op.f("ix_expenses_society_id"), "expenses", ["society_id"])
    op.create_index(op.f("ix_expenses_tenant_id"), "expenses", ["tenant_id"])
    op.create_index(op.f("ix_expenses_vendor_id"), "expenses", ["vendor_id"])
    op.create_index(
        "uq_expenses_vendor_bill_number",
        "expenses",
        ["tenant_id", "society_id", "vendor_id", "vendor_bill_number"],
        unique=True,
        postgresql_where=sa.text("vendor_id IS NOT NULL AND vendor_bill_number IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_expenses_vendor_bill_number", table_name="expenses")
    op.drop_index(op.f("ix_expenses_vendor_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_tenant_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_society_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_payment_account_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_expense_category_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_expense_account_id"), table_name="expenses")
    op.drop_table("expenses")
