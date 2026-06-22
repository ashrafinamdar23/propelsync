"""create journals

Revision ID: 20260620_0026
Revises: 20260620_0025
Create Date: 2026-06-20 00:26:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0026"
down_revision: str | None = "20260620_0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journal_date", sa.Date(), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reversal_of_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "source_type IN ('manual', 'invoice', 'payment', 'expense', 'expense_payment', 'transfer')",
            name="ck_journal_entries_source_type",
        ),
        sa.CheckConstraint("status IN ('posted', 'reversed')", name="ck_journal_entries_status"),
        sa.ForeignKeyConstraint(["reversal_of_entry_id"], ["journal_entries.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_journal_entries_reversal_of_entry_id"), "journal_entries", ["reversal_of_entry_id"])
    op.create_index(op.f("ix_journal_entries_society_id"), "journal_entries", ["society_id"])
    op.create_index(op.f("ix_journal_entries_source_id"), "journal_entries", ["source_id"])
    op.create_index(op.f("ix_journal_entries_tenant_id"), "journal_entries", ["tenant_id"])

    op.create_table(
        "journal_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("debit_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("credit_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("line_number > 0", name="ck_journal_lines_line_number_positive"),
        sa.CheckConstraint("debit_amount >= 0", name="ck_journal_lines_debit_non_negative"),
        sa.CheckConstraint("credit_amount >= 0", name="ck_journal_lines_credit_non_negative"),
        sa.CheckConstraint("debit_amount + credit_amount > 0", name="ck_journal_lines_amount_positive"),
        sa.CheckConstraint("debit_amount = 0 OR credit_amount = 0", name="ck_journal_lines_single_sided"),
        sa.ForeignKeyConstraint(["account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "journal_entry_id", "line_number", name="uq_journal_lines_entry_line"),
    )
    op.create_index(op.f("ix_journal_lines_account_id"), "journal_lines", ["account_id"])
    op.create_index(op.f("ix_journal_lines_journal_entry_id"), "journal_lines", ["journal_entry_id"])
    op.create_index(op.f("ix_journal_lines_society_id"), "journal_lines", ["society_id"])
    op.create_index(op.f("ix_journal_lines_tenant_id"), "journal_lines", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_journal_lines_tenant_id"), table_name="journal_lines")
    op.drop_index(op.f("ix_journal_lines_society_id"), table_name="journal_lines")
    op.drop_index(op.f("ix_journal_lines_journal_entry_id"), table_name="journal_lines")
    op.drop_index(op.f("ix_journal_lines_account_id"), table_name="journal_lines")
    op.drop_table("journal_lines")
    op.drop_index(op.f("ix_journal_entries_tenant_id"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_source_id"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_society_id"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_reversal_of_entry_id"), table_name="journal_entries")
    op.drop_table("journal_entries")
