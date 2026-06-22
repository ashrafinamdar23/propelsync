"""create societies table

Revision ID: 20260620_0004
Revises: 20260620_0003
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0004"
down_revision: str | None = "20260620_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "societies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("registration_number", sa.String(length=100), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=True),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=False, server_default="India"),
        sa.Column(
            "timezone",
            sa.String(length=100),
            nullable=False,
            server_default="Asia/Kolkata",
        ),
        sa.Column("locale", sa.String(length=20), nullable=False, server_default="en-IN"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("financial_year_start_month", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(currency) = 3",
            name="ck_societies_currency_length",
        ),
        sa.CheckConstraint(
            "financial_year_start_month BETWEEN 1 AND 12",
            name="ck_societies_financial_year_start_month",
        ),
        sa.CheckConstraint("status IN ('active', 'suspended')", name="ck_societies_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_societies_tenant_name"),
        sa.UniqueConstraint(
            "tenant_id",
            "registration_number",
            name="uq_societies_tenant_registration_number",
        ),
    )
    op.create_index(op.f("ix_societies_tenant_id"), "societies", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_societies_tenant_id"), table_name="societies")
    op.drop_table("societies")
