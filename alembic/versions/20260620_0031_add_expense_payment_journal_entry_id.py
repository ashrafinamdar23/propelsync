"""add expense payment journal entry id

Revision ID: 20260620_0031
Revises: 20260620_0030
Create Date: 2026-06-20 00:31:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0031"
down_revision: str | None = "20260620_0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("expense_payments", sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_expense_payments_journal_entry_id_journal_entries",
        "expense_payments",
        "journal_entries",
        ["journal_entry_id"],
        ["id"],
    )
    op.create_index(op.f("ix_expense_payments_journal_entry_id"), "expense_payments", ["journal_entry_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_expense_payments_journal_entry_id"), table_name="expense_payments")
    op.drop_constraint(
        "fk_expense_payments_journal_entry_id_journal_entries",
        "expense_payments",
        type_="foreignkey",
    )
    op.drop_column("expense_payments", "journal_entry_id")
