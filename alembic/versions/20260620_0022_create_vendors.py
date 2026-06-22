"""create vendors

Revision ID: 20260620_0022
Revises: 20260620_0021
Create Date: 2026-06-20 00:22:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0022"
down_revision: str | None = "20260620_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_code", sa.String(length=50), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("vendor_type", sa.String(length=30), nullable=False),
        sa.Column("contact_person", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("mobile_number", sa.String(length=20), nullable=True),
        sa.Column("tax_identifier", sa.String(length=50), nullable=True),
        sa.Column("billing_address", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "vendor_type IN ('individual', 'company', 'firm', 'other')",
            name="ck_vendors_vendor_type",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_vendors_status"),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "vendor_code", name="uq_vendors_society_code"),
    )
    op.create_index(op.f("ix_vendors_email"), "vendors", ["email"])
    op.create_index(op.f("ix_vendors_mobile_number"), "vendors", ["mobile_number"])
    op.create_index(op.f("ix_vendors_society_id"), "vendors", ["society_id"])
    op.create_index(op.f("ix_vendors_tenant_id"), "vendors", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_vendors_tenant_id"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_society_id"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_mobile_number"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_email"), table_name="vendors")
    op.drop_table("vendors")
