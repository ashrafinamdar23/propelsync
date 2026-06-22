"""add payment journal entry id

Revision ID: 20260620_0029
Revises: 20260620_0028
Create Date: 2026-06-20 00:29:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0029"
down_revision: str | None = "20260620_0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_payments_journal_entry_id_journal_entries",
        "payments",
        "journal_entries",
        ["journal_entry_id"],
        ["id"],
    )
    op.create_index(op.f("ix_payments_journal_entry_id"), "payments", ["journal_entry_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_journal_entry_id"), table_name="payments")
    op.drop_constraint("fk_payments_journal_entry_id_journal_entries", "payments", type_="foreignkey")
    op.drop_column("payments", "journal_entry_id")
