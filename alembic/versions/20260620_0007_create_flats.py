"""create flats table

Revision ID: 20260620_0007
Revises: 20260620_0006
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0007"
down_revision: str | None = "20260620_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "wings",
        "building_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_table(
        "flats",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wing_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("flat_number", sa.String(length=50), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=True),
        sa.Column("carpet_area_sqft", sa.Numeric(10, 2), nullable=True),
        sa.Column("built_up_area_sqft", sa.Numeric(10, 2), nullable=True),
        sa.Column("parking_count", sa.Integer(), nullable=False, server_default="0"),
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
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_flats_status"),
        sa.CheckConstraint(
            "carpet_area_sqft IS NULL OR carpet_area_sqft >= 0",
            name="ck_flats_carpet_area_non_negative",
        ),
        sa.CheckConstraint(
            "built_up_area_sqft IS NULL OR built_up_area_sqft >= 0",
            name="ck_flats_built_up_area_non_negative",
        ),
        sa.CheckConstraint(
            "parking_count >= 0",
            name="ck_flats_parking_count_non_negative",
        ),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["wing_id"], ["wings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_flats_building_id"), "flats", ["building_id"], unique=False)
    op.create_index(op.f("ix_flats_society_id"), "flats", ["society_id"], unique=False)
    op.create_index(op.f("ix_flats_tenant_id"), "flats", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_flats_wing_id"), "flats", ["wing_id"], unique=False)
    op.create_index(
        "uq_flats_number_with_wing",
        "flats",
        ["tenant_id", "society_id", "building_id", "wing_id", "flat_number"],
        unique=True,
        postgresql_where=sa.text("wing_id IS NOT NULL"),
    )
    op.create_index(
        "uq_flats_number_without_wing",
        "flats",
        ["tenant_id", "society_id", "building_id", "flat_number"],
        unique=True,
        postgresql_where=sa.text("wing_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_flats_number_without_wing", table_name="flats")
    op.drop_index("uq_flats_number_with_wing", table_name="flats")
    op.drop_index(op.f("ix_flats_wing_id"), table_name="flats")
    op.drop_index(op.f("ix_flats_tenant_id"), table_name="flats")
    op.drop_index(op.f("ix_flats_society_id"), table_name="flats")
    op.drop_index(op.f("ix_flats_building_id"), table_name="flats")
    op.drop_table("flats")
    op.alter_column(
        "wings",
        "building_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
