"""add expense journal posting fields

Revision ID: 20260620_0030
Revises: 20260620_0029
Create Date: 2026-06-20 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0030"
down_revision: str | None = "20260620_0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("societies", sa.Column("payable_account_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_societies_payable_account_id_chart_of_accounts",
        "societies",
        "chart_of_accounts",
        ["payable_account_id"],
        ["id"],
    )
    op.create_index(op.f("ix_societies_payable_account_id"), "societies", ["payable_account_id"])

    op.add_column("expenses", sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_expenses_journal_entry_id_journal_entries",
        "expenses",
        "journal_entries",
        ["journal_entry_id"],
        ["id"],
    )
    op.create_index(op.f("ix_expenses_journal_entry_id"), "expenses", ["journal_entry_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_expenses_journal_entry_id"), table_name="expenses")
    op.drop_constraint("fk_expenses_journal_entry_id_journal_entries", "expenses", type_="foreignkey")
    op.drop_column("expenses", "journal_entry_id")

    op.drop_index(op.f("ix_societies_payable_account_id"), table_name="societies")
    op.drop_constraint("fk_societies_payable_account_id_chart_of_accounts", "societies", type_="foreignkey")
    op.drop_column("societies", "payable_account_id")
