"""add opening balance journal source

Revision ID: 20260620_0032
Revises: 20260620_0031
Create Date: 2026-06-20 00:32:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260620_0032"
down_revision: str | None = "20260620_0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


OLD_SOURCE_TYPES = "'manual', 'invoice', 'payment', 'expense', 'expense_payment', 'transfer'"
NEW_SOURCE_TYPES = (
    "'manual', 'opening_balance', 'invoice', 'payment', 'expense', 'expense_payment', 'transfer'"
)


def upgrade() -> None:
    op.drop_constraint("ck_journal_entries_source_type", "journal_entries", type_="check")
    op.create_check_constraint(
        "ck_journal_entries_source_type",
        "journal_entries",
        f"source_type IN ({NEW_SOURCE_TYPES})",
    )


def downgrade() -> None:
    op.drop_constraint("ck_journal_entries_source_type", "journal_entries", type_="check")
    op.create_check_constraint(
        "ck_journal_entries_source_type",
        "journal_entries",
        f"source_type IN ({OLD_SOURCE_TYPES})",
    )
