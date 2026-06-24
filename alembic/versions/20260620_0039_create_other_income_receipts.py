"""create other income receipts

Revision ID: 20260620_0039
Revises: 20260620_0038
Create Date: 2026-06-20 00:39:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0039"
down_revision: Union[str, None] = "20260620_0038"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "other_income_receipts",
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("income_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deposit_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("receipt_date", sa.Date(), nullable=False),
        sa.Column("payer_name", sa.String(length=255), nullable=False),
        sa.Column("payer_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("receipt_mode", sa.String(length=30), nullable=False),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_other_income_receipts_amount_positive"),
        sa.CheckConstraint(
            "payer_type IN ('bank', 'vendor', 'resident', 'external_party', 'other')",
            name="ck_other_income_receipts_payer_type",
        ),
        sa.CheckConstraint(
            "receipt_mode IN ('cash', 'bank_transfer', 'cheque', 'upi', 'card', 'other')",
            name="ck_other_income_receipts_mode",
        ),
        sa.CheckConstraint("status IN ('received', 'reversed')", name="ck_other_income_receipts_status"),
        sa.ForeignKeyConstraint(["deposit_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["income_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_other_income_receipts_deposit_account_id"), "other_income_receipts", ["deposit_account_id"])
    op.create_index(op.f("ix_other_income_receipts_income_account_id"), "other_income_receipts", ["income_account_id"])
    op.create_index(op.f("ix_other_income_receipts_journal_entry_id"), "other_income_receipts", ["journal_entry_id"])
    op.create_index(op.f("ix_other_income_receipts_receipt_date"), "other_income_receipts", ["receipt_date"])
    op.create_index(op.f("ix_other_income_receipts_society_id"), "other_income_receipts", ["society_id"])
    op.create_index(op.f("ix_other_income_receipts_tenant_id"), "other_income_receipts", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_other_income_receipts_tenant_id"), table_name="other_income_receipts")
    op.drop_index(op.f("ix_other_income_receipts_society_id"), table_name="other_income_receipts")
    op.drop_index(op.f("ix_other_income_receipts_receipt_date"), table_name="other_income_receipts")
    op.drop_index(op.f("ix_other_income_receipts_journal_entry_id"), table_name="other_income_receipts")
    op.drop_index(op.f("ix_other_income_receipts_income_account_id"), table_name="other_income_receipts")
    op.drop_index(op.f("ix_other_income_receipts_deposit_account_id"), table_name="other_income_receipts")
    op.drop_table("other_income_receipts")
