"""add billing rule schedule

Revision ID: 20260620_0017
Revises: 20260620_0016
Create Date: 2026-06-20 00:17:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260620_0017"
down_revision: str | None = "20260620_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("billing_rules", sa.Column("generation_day", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("billing_rules", sa.Column("due_day", sa.Integer(), nullable=False, server_default="10"))
    op.add_column(
        "billing_rules",
        sa.Column("billing_period_timing", sa.String(length=30), nullable=False, server_default="current_period"),
    )
    op.add_column("billing_rules", sa.Column("next_generation_date", sa.Date(), nullable=True))
    op.create_check_constraint(
        "ck_billing_rules_generation_day",
        "billing_rules",
        "generation_day >= 1 AND generation_day <= 31",
    )
    op.create_check_constraint(
        "ck_billing_rules_due_day",
        "billing_rules",
        "due_day >= 1 AND due_day <= 31",
    )
    op.create_check_constraint(
        "ck_billing_rules_period_timing",
        "billing_rules",
        "billing_period_timing IN ('current_period', 'next_period')",
    )
    op.create_index(op.f("ix_billing_rules_next_generation_date"), "billing_rules", ["next_generation_date"])
    op.alter_column("billing_rules", "generation_day", server_default=None)
    op.alter_column("billing_rules", "due_day", server_default=None)
    op.alter_column("billing_rules", "billing_period_timing", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_billing_rules_next_generation_date"), table_name="billing_rules")
    op.drop_constraint("ck_billing_rules_period_timing", "billing_rules", type_="check")
    op.drop_constraint("ck_billing_rules_due_day", "billing_rules", type_="check")
    op.drop_constraint("ck_billing_rules_generation_day", "billing_rules", type_="check")
    op.drop_column("billing_rules", "next_generation_date")
    op.drop_column("billing_rules", "billing_period_timing")
    op.drop_column("billing_rules", "due_day")
    op.drop_column("billing_rules", "generation_day")
