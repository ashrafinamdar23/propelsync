"""create payments

Revision ID: 20260620_0021
Revises: 20260620_0020
Create Date: 2026-06-20 00:21:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0021"
down_revision: str | None = "20260620_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deposit_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("unapplied_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_mode", sa.String(length=30), nullable=False),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        sa.CheckConstraint("unapplied_amount >= 0", name="ck_payments_unapplied_amount_non_negative"),
        sa.CheckConstraint(
            "payment_mode IN ('cash', 'bank_transfer', 'cheque', 'upi', 'card', 'other')",
            name="ck_payments_mode",
        ),
        sa.CheckConstraint("status IN ('received', 'reversed')", name="ck_payments_status"),
        sa.ForeignKeyConstraint(["deposit_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_deposit_account_id"), "payments", ["deposit_account_id"])
    op.create_index(op.f("ix_payments_flat_id"), "payments", ["flat_id"])
    op.create_index(op.f("ix_payments_owner_id"), "payments", ["owner_id"])
    op.create_index(op.f("ix_payments_society_id"), "payments", ["society_id"])
    op.create_index(op.f("ix_payments_tenant_id"), "payments", ["tenant_id"])

    op.create_table(
        "payment_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("allocated_amount > 0", name="ck_payment_allocations_amount_positive"),
        sa.CheckConstraint("status IN ('active', 'reversed')", name="ck_payment_allocations_status"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "payment_id", "invoice_id", name="uq_payment_allocation_invoice"),
    )
    op.create_index(op.f("ix_payment_allocations_invoice_id"), "payment_allocations", ["invoice_id"])
    op.create_index(op.f("ix_payment_allocations_payment_id"), "payment_allocations", ["payment_id"])
    op.create_index(op.f("ix_payment_allocations_society_id"), "payment_allocations", ["society_id"])
    op.create_index(op.f("ix_payment_allocations_tenant_id"), "payment_allocations", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_allocations_tenant_id"), table_name="payment_allocations")
    op.drop_index(op.f("ix_payment_allocations_society_id"), table_name="payment_allocations")
    op.drop_index(op.f("ix_payment_allocations_payment_id"), table_name="payment_allocations")
    op.drop_index(op.f("ix_payment_allocations_invoice_id"), table_name="payment_allocations")
    op.drop_table("payment_allocations")
    op.drop_index(op.f("ix_payments_tenant_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_society_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_owner_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_flat_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_deposit_account_id"), table_name="payments")
    op.drop_table("payments")
