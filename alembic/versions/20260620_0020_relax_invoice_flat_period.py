"""relax invoice flat period uniqueness

Revision ID: 20260620_0020
Revises: 20260620_0019
Create Date: 2026-06-20 00:20:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260620_0020"
down_revision: str | None = "20260620_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("uq_invoices_flat_period", table_name="invoices")
    op.create_index(
        "ix_invoices_flat_period",
        "invoices",
        ["tenant_id", "society_id", "flat_id", "billing_period_start", "billing_period_end"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_invoices_flat_period", table_name="invoices")
    op.create_index(
        "uq_invoices_flat_period",
        "invoices",
        ["tenant_id", "society_id", "flat_id", "billing_period_start", "billing_period_end"],
        unique=True,
    )
