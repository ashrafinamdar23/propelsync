"""create residents table

Revision ID: 20260620_0011
Revises: 20260620_0010
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0011"
down_revision: str | None = "20260620_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "residents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resident_type", sa.String(length=30), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("mobile_number", sa.String(length=20), nullable=True),
        sa.Column("move_in_date", sa.Date(), nullable=False),
        sa.Column("move_out_date", sa.Date(), nullable=True),
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
            "resident_type IN ('owner_occupier', 'tenant', 'family_member', 'staff', 'other')",
            name="ck_residents_resident_type",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_residents_status"),
        sa.CheckConstraint(
            "move_out_date IS NULL OR move_out_date >= move_in_date",
            name="ck_residents_move_dates",
        ),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_residents_email"), "residents", ["email"], unique=False)
    op.create_index(op.f("ix_residents_flat_id"), "residents", ["flat_id"], unique=False)
    op.create_index(
        op.f("ix_residents_mobile_number"),
        "residents",
        ["mobile_number"],
        unique=False,
    )
    op.create_index(op.f("ix_residents_owner_id"), "residents", ["owner_id"], unique=False)
    op.create_index(op.f("ix_residents_society_id"), "residents", ["society_id"], unique=False)
    op.create_index(op.f("ix_residents_tenant_id"), "residents", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_residents_user_id"), "residents", ["user_id"], unique=False)
    op.create_index(
        "uq_residents_flat_user_current",
        "residents",
        ["tenant_id", "society_id", "flat_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL AND move_out_date IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_residents_flat_user_current", table_name="residents")
    op.drop_index(op.f("ix_residents_user_id"), table_name="residents")
    op.drop_index(op.f("ix_residents_tenant_id"), table_name="residents")
    op.drop_index(op.f("ix_residents_society_id"), table_name="residents")
    op.drop_index(op.f("ix_residents_owner_id"), table_name="residents")
    op.drop_index(op.f("ix_residents_mobile_number"), table_name="residents")
    op.drop_index(op.f("ix_residents_flat_id"), table_name="residents")
    op.drop_index(op.f("ix_residents_email"), table_name="residents")
    op.drop_table("residents")
