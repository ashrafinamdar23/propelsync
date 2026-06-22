"""create expense categories

Revision ID: 20260620_0023
Revises: 20260620_0022
Create Date: 2026-06-20 00:23:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0023"
down_revision: str | None = "20260620_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expense_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("expense_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_expense_categories_status"),
        sa.ForeignKeyConstraint(["expense_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "code", name="uq_expense_categories_society_code"),
        sa.UniqueConstraint("tenant_id", "society_id", "name", name="uq_expense_categories_society_name"),
    )
    op.create_index(op.f("ix_expense_categories_expense_account_id"), "expense_categories", ["expense_account_id"])
    op.create_index(op.f("ix_expense_categories_society_id"), "expense_categories", ["society_id"])
    op.create_index(op.f("ix_expense_categories_tenant_id"), "expense_categories", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_expense_categories_tenant_id"), table_name="expense_categories")
    op.drop_index(op.f("ix_expense_categories_society_id"), table_name="expense_categories")
    op.drop_index(op.f("ix_expense_categories_expense_account_id"), table_name="expense_categories")
    op.drop_table("expense_categories")
