"""create buildings table

Revision ID: 20260620_0005
Revises: 20260620_0004
Create Date: 2026-06-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0005"
down_revision: str | None = "20260620_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.CheckConstraint("status IN ('active', 'suspended')", name="ck_buildings_status"),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "society_id", "code", name="uq_buildings_society_code"),
        sa.UniqueConstraint("tenant_id", "society_id", "name", name="uq_buildings_society_name"),
    )
    op.create_index(op.f("ix_buildings_society_id"), "buildings", ["society_id"], unique=False)
    op.create_index(op.f("ix_buildings_tenant_id"), "buildings", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_buildings_tenant_id"), table_name="buildings")
    op.drop_index(op.f("ix_buildings_society_id"), table_name="buildings")
    op.drop_table("buildings")
