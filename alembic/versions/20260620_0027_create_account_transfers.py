"""create account transfers

Revision ID: 20260620_0027
Revises: 20260620_0026
Create Date: 2026-06-20 00:27:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0027"
down_revision: str | None = "20260620_0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transfer_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("transfer_mode", sa.String(length=30), nullable=False),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_account_transfers_amount_positive"),
        sa.CheckConstraint("from_account_id <> to_account_id", name="ck_account_transfers_different_accounts"),
        sa.CheckConstraint(
            "transfer_mode IN ('cash', 'bank_transfer', 'cheque', 'upi', 'card', 'other')",
            name="ck_account_transfers_mode",
        ),
        sa.CheckConstraint("status IN ('posted', 'reversed')", name="ck_account_transfers_status"),
        sa.ForeignKeyConstraint(["from_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["to_account_id"], ["chart_of_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_account_transfers_from_account_id"), "account_transfers", ["from_account_id"])
    op.create_index(op.f("ix_account_transfers_journal_entry_id"), "account_transfers", ["journal_entry_id"])
    op.create_index(op.f("ix_account_transfers_society_id"), "account_transfers", ["society_id"])
    op.create_index(op.f("ix_account_transfers_tenant_id"), "account_transfers", ["tenant_id"])
    op.create_index(op.f("ix_account_transfers_to_account_id"), "account_transfers", ["to_account_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_account_transfers_to_account_id"), table_name="account_transfers")
    op.drop_index(op.f("ix_account_transfers_tenant_id"), table_name="account_transfers")
    op.drop_index(op.f("ix_account_transfers_society_id"), table_name="account_transfers")
    op.drop_index(op.f("ix_account_transfers_journal_entry_id"), table_name="account_transfers")
    op.drop_index(op.f("ix_account_transfers_from_account_id"), table_name="account_transfers")
    op.drop_table("account_transfers")
