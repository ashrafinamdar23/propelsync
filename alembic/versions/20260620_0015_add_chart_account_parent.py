"""add chart account parent

Revision ID: 20260620_0015
Revises: 20260620_0014
Create Date: 2026-06-20 00:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0015"
down_revision: str | None = "20260620_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chart_of_accounts",
        sa.Column("parent_account_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_chart_of_accounts_parent_account_id"),
        "chart_of_accounts",
        ["parent_account_id"],
    )
    op.create_foreign_key(
        "fk_chart_accounts_parent_account_id",
        "chart_of_accounts",
        "chart_of_accounts",
        ["parent_account_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_chart_accounts_parent_account_id", "chart_of_accounts", type_="foreignkey")
    op.drop_index(op.f("ix_chart_of_accounts_parent_account_id"), table_name="chart_of_accounts")
    op.drop_column("chart_of_accounts", "parent_account_id")
