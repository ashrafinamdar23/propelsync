"""add late fee application status

Revision ID: 20260620_0034
Revises: 20260620_0033
Create Date: 2026-06-20 00:34:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260620_0034"
down_revision: str | None = "20260620_0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "late_fee_applications",
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
    )
    op.create_check_constraint(
        "ck_late_fee_applications_status",
        "late_fee_applications",
        "status IN ('active', 'cancelled')",
    )
    op.alter_column("late_fee_applications", "status", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_late_fee_applications_status", "late_fee_applications", type_="check")
    op.drop_column("late_fee_applications", "status")
