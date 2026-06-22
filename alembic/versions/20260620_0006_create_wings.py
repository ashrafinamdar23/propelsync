"""create wings table

Revision ID: 20260620_0006
Revises: 20260620_0005
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0006"
down_revision: str | None = "20260620_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
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
        sa.CheckConstraint("status IN ('active', 'suspended')", name="ck_wings_status"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "building_id",
            "code",
            name="uq_wings_scope_code",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "building_id",
            "name",
            name="uq_wings_scope_name",
        ),
    )
    op.create_index(op.f("ix_wings_building_id"), "wings", ["building_id"], unique=False)
    op.create_index(op.f("ix_wings_society_id"), "wings", ["society_id"], unique=False)
    op.create_index(op.f("ix_wings_tenant_id"), "wings", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_wings_tenant_id"), table_name="wings")
    op.drop_index(op.f("ix_wings_society_id"), table_name="wings")
    op.drop_index(op.f("ix_wings_building_id"), table_name="wings")
    op.drop_table("wings")
