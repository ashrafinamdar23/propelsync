"""create owners table

Revision ID: 20260620_0009
Revises: 20260620_0008
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0009"
down_revision: str | None = "20260620_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "owners",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_type", sa.String(length=30), nullable=False, server_default="individual"),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("mobile_number", sa.String(length=20), nullable=True),
        sa.Column("tax_identifier", sa.String(length=50), nullable=True),
        sa.Column("billing_address", sa.Text(), nullable=True),
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
            "owner_type IN ('individual', 'company', 'trust', 'other')",
            name="ck_owners_owner_type",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_owners_status"),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_owners_email"), "owners", ["email"], unique=False)
    op.create_index(op.f("ix_owners_mobile_number"), "owners", ["mobile_number"], unique=False)
    op.create_index(op.f("ix_owners_society_id"), "owners", ["society_id"], unique=False)
    op.create_index(op.f("ix_owners_tenant_id"), "owners", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_owners_user_id"), "owners", ["user_id"], unique=False)
    op.create_index(
        "uq_owners_society_user",
        "owners",
        ["tenant_id", "society_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_owners_society_user", table_name="owners")
    op.drop_index(op.f("ix_owners_user_id"), table_name="owners")
    op.drop_index(op.f("ix_owners_tenant_id"), table_name="owners")
    op.drop_index(op.f("ix_owners_society_id"), table_name="owners")
    op.drop_index(op.f("ix_owners_mobile_number"), table_name="owners")
    op.drop_index(op.f("ix_owners_email"), table_name="owners")
    op.drop_table("owners")
