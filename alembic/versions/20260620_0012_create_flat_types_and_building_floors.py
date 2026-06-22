"""create flat types and building floors

Revision ID: 20260620_0012
Revises: 20260620_0011
Create Date: 2026-06-20 00:12:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0012"
down_revision: str | None = "20260620_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "flat_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("unit_category", sa.String(length=30), nullable=False),
        sa.Column("bedroom_count", sa.Integer(), nullable=True),
        sa.Column("bathroom_count", sa.Integer(), nullable=True),
        sa.Column("carpet_area_sqft", sa.Numeric(10, 2), nullable=True),
        sa.Column("built_up_area_sqft", sa.Numeric(10, 2), nullable=True),
        sa.Column("default_parking_count", sa.Integer(), nullable=False),
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
            "unit_category IN ('residential', 'commercial', 'shop', 'office', 'parking', 'other')",
            name="ck_flat_types_unit_category",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_flat_types_status"),
        sa.CheckConstraint(
            "bedroom_count IS NULL OR bedroom_count >= 0",
            name="ck_flat_types_bedroom_count_non_negative",
        ),
        sa.CheckConstraint(
            "bathroom_count IS NULL OR bathroom_count >= 0",
            name="ck_flat_types_bathroom_count_non_negative",
        ),
        sa.CheckConstraint(
            "carpet_area_sqft IS NULL OR carpet_area_sqft >= 0",
            name="ck_flat_types_carpet_area_non_negative",
        ),
        sa.CheckConstraint(
            "built_up_area_sqft IS NULL OR built_up_area_sqft >= 0",
            name="ck_flat_types_built_up_area_non_negative",
        ),
        sa.CheckConstraint(
            "default_parking_count >= 0",
            name="ck_flat_types_default_parking_count_non_negative",
        ),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "name", name="uq_flat_types_society_name"),
        sa.UniqueConstraint("tenant_id", "society_id", "code", name="uq_flat_types_society_code"),
    )
    op.create_index(op.f("ix_flat_types_society_id"), "flat_types", ["society_id"])
    op.create_index(op.f("ix_flat_types_tenant_id"), "flat_types", ["tenant_id"])

    op.create_table(
        "building_floors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("floor_label", sa.String(length=100), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=False),
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
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_building_floors_status"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "building_id",
            "floor_label",
            name="uq_building_floors_label",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "building_id",
            "floor_number",
            name="uq_building_floors_number",
        ),
    )
    op.create_index(op.f("ix_building_floors_building_id"), "building_floors", ["building_id"])
    op.create_index(op.f("ix_building_floors_society_id"), "building_floors", ["society_id"])
    op.create_index(op.f("ix_building_floors_tenant_id"), "building_floors", ["tenant_id"])

    op.add_column("flats", sa.Column("floor_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("flats", sa.Column("flat_type_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_flats_floor_id"), "flats", ["floor_id"])
    op.create_index(op.f("ix_flats_flat_type_id"), "flats", ["flat_type_id"])
    op.create_foreign_key("fk_flats_floor_id", "flats", "building_floors", ["floor_id"], ["id"])
    op.create_foreign_key("fk_flats_flat_type_id", "flats", "flat_types", ["flat_type_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_flats_flat_type_id", "flats", type_="foreignkey")
    op.drop_constraint("fk_flats_floor_id", "flats", type_="foreignkey")
    op.drop_index(op.f("ix_flats_flat_type_id"), table_name="flats")
    op.drop_index(op.f("ix_flats_floor_id"), table_name="flats")
    op.drop_column("flats", "flat_type_id")
    op.drop_column("flats", "floor_id")

    op.drop_index(op.f("ix_building_floors_tenant_id"), table_name="building_floors")
    op.drop_index(op.f("ix_building_floors_society_id"), table_name="building_floors")
    op.drop_index(op.f("ix_building_floors_building_id"), table_name="building_floors")
    op.drop_table("building_floors")

    op.drop_index(op.f("ix_flat_types_tenant_id"), table_name="flat_types")
    op.drop_index(op.f("ix_flat_types_society_id"), table_name="flat_types")
    op.drop_table("flat_types")
