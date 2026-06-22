"""create lease agreements

Revision ID: 20260620_0036
Revises: 20260620_0035
Create Date: 2026-06-20 00:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0036"
down_revision: Union[str, None] = "20260620_0035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lease_agreements",
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_name", sa.String(length=255), nullable=False),
        sa.Column("tenant_email", sa.String(length=255), nullable=True),
        sa.Column("tenant_mobile_number", sa.String(length=20), nullable=True),
        sa.Column("agreement_start_date", sa.Date(), nullable=False),
        sa.Column("agreement_end_date", sa.Date(), nullable=False),
        sa.Column("move_in_date", sa.Date(), nullable=False),
        sa.Column("move_out_date", sa.Date(), nullable=True),
        sa.Column("monthly_rent", sa.Numeric(12, 2), nullable=True),
        sa.Column("security_deposit", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "police_verification_status",
            sa.String(length=30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("document_reference", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "agreement_end_date >= agreement_start_date",
            name="ck_lease_agreements_agreement_dates",
        ),
        sa.CheckConstraint(
            "monthly_rent IS NULL OR monthly_rent >= 0",
            name="ck_lease_agreements_monthly_rent_non_negative",
        ),
        sa.CheckConstraint(
            "move_out_date IS NULL OR move_out_date >= move_in_date",
            name="ck_lease_agreements_move_dates",
        ),
        sa.CheckConstraint(
            "police_verification_status IN ('not_required', 'pending', 'completed')",
            name="ck_lease_agreements_police_verification_status",
        ),
        sa.CheckConstraint(
            "security_deposit IS NULL OR security_deposit >= 0",
            name="ck_lease_agreements_security_deposit_non_negative",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'expired', 'terminated', 'renewed')",
            name="ck_lease_agreements_status",
        ),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"]),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"]),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lease_agreements_agreement_end_date"),
        "lease_agreements",
        ["agreement_end_date"],
    )
    op.create_index(op.f("ix_lease_agreements_building_id"), "lease_agreements", ["building_id"])
    op.create_index(op.f("ix_lease_agreements_flat_id"), "lease_agreements", ["flat_id"])
    op.create_index(op.f("ix_lease_agreements_owner_id"), "lease_agreements", ["owner_id"])
    op.create_index(op.f("ix_lease_agreements_resident_id"), "lease_agreements", ["resident_id"])
    op.create_index(op.f("ix_lease_agreements_society_id"), "lease_agreements", ["society_id"])
    op.create_index(op.f("ix_lease_agreements_tenant_email"), "lease_agreements", ["tenant_email"])
    op.create_index(op.f("ix_lease_agreements_tenant_id"), "lease_agreements", ["tenant_id"])
    op.create_index(
        op.f("ix_lease_agreements_tenant_mobile_number"),
        "lease_agreements",
        ["tenant_mobile_number"],
    )
    op.create_index(
        "uq_lease_agreements_active_flat",
        "lease_agreements",
        ["tenant_id", "society_id", "flat_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_lease_agreements_active_flat",
        table_name="lease_agreements",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index(op.f("ix_lease_agreements_tenant_mobile_number"), table_name="lease_agreements")
    op.drop_index(op.f("ix_lease_agreements_tenant_id"), table_name="lease_agreements")
    op.drop_index(op.f("ix_lease_agreements_tenant_email"), table_name="lease_agreements")
    op.drop_index(op.f("ix_lease_agreements_society_id"), table_name="lease_agreements")
    op.drop_index(op.f("ix_lease_agreements_resident_id"), table_name="lease_agreements")
    op.drop_index(op.f("ix_lease_agreements_owner_id"), table_name="lease_agreements")
    op.drop_index(op.f("ix_lease_agreements_flat_id"), table_name="lease_agreements")
    op.drop_index(op.f("ix_lease_agreements_building_id"), table_name="lease_agreements")
    op.drop_index(op.f("ix_lease_agreements_agreement_end_date"), table_name="lease_agreements")
    op.drop_table("lease_agreements")
