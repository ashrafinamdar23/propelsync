"""create chart of accounts

Revision ID: 20260620_0014
Revises: 20260620_0013
Create Date: 2026-06-20 00:14:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0014"
down_revision: str | None = "20260620_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chart_of_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_code", sa.String(length=50), nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=False),
        sa.Column("account_type", sa.String(length=30), nullable=False),
        sa.Column("normal_balance", sa.String(length=10), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "account_type IN ('asset', 'liability', 'equity', 'income', 'expense')",
            name="ck_chart_accounts_account_type",
        ),
        sa.CheckConstraint(
            "normal_balance IN ('debit', 'credit')",
            name="ck_chart_accounts_normal_balance",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_chart_accounts_status"),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "account_code", name="uq_chart_accounts_code"),
        sa.UniqueConstraint("tenant_id", "society_id", "account_name", name="uq_chart_accounts_name"),
    )
    op.create_index(op.f("ix_chart_of_accounts_society_id"), "chart_of_accounts", ["society_id"])
    op.create_index(op.f("ix_chart_of_accounts_tenant_id"), "chart_of_accounts", ["tenant_id"])

    op.add_column(
        "charge_types",
        sa.Column("revenue_account_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(op.f("ix_charge_types_revenue_account_id"), "charge_types", ["revenue_account_id"])
    op.create_foreign_key(
        "fk_charge_types_revenue_account_id",
        "charge_types",
        "chart_of_accounts",
        ["revenue_account_id"],
        ["id"],
    )
    op.drop_constraint("ck_charge_types_charge_category", "charge_types", type_="check")
    op.drop_column("charge_types", "charge_category")
    op.drop_column("charge_types", "revenue_account_code")


def downgrade() -> None:
    op.add_column(
        "charge_types",
        sa.Column("revenue_account_code", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "charge_types",
        sa.Column("charge_category", sa.String(length=30), nullable=False, server_default="regular"),
    )
    op.create_check_constraint(
        "ck_charge_types_charge_category",
        "charge_types",
        "charge_category IN ('regular', 'fund', 'utility', 'penalty', 'tax', 'adjustment', 'other')",
    )
    op.drop_constraint("fk_charge_types_revenue_account_id", "charge_types", type_="foreignkey")
    op.drop_index(op.f("ix_charge_types_revenue_account_id"), table_name="charge_types")
    op.drop_column("charge_types", "revenue_account_id")
    op.drop_index(op.f("ix_chart_of_accounts_tenant_id"), table_name="chart_of_accounts")
    op.drop_index(op.f("ix_chart_of_accounts_society_id"), table_name="chart_of_accounts")
    op.drop_table("chart_of_accounts")
