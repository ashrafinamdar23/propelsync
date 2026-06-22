"""create document sequences

Revision ID: 20260620_0019
Revises: 20260620_0018
Create Date: 2026-06-20 00:19:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0019"
down_revision: str | None = "20260620_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.String(length=30), nullable=False),
        sa.Column("prefix", sa.String(length=20), nullable=False),
        sa.Column("include_period", sa.Boolean(), nullable=False),
        sa.Column("include_financial_year", sa.Boolean(), nullable=False),
        sa.Column("separator", sa.String(length=3), nullable=False),
        sa.Column("next_sequence", sa.Integer(), nullable=False),
        sa.Column("padding", sa.Integer(), nullable=False),
        sa.Column("reset_policy", sa.String(length=30), nullable=False),
        sa.Column("current_reset_key", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("document_type IN ('invoice', 'receipt')", name="ck_document_sequences_type"),
        sa.CheckConstraint("next_sequence > 0", name="ck_document_sequences_next_sequence"),
        sa.CheckConstraint("padding BETWEEN 1 AND 10", name="ck_document_sequences_padding"),
        sa.CheckConstraint(
            "reset_policy IN ('monthly', 'financial_year', 'never')",
            name="ck_document_sequences_reset_policy",
        ),
        sa.CheckConstraint("char_length(separator) BETWEEN 0 AND 3", name="ck_document_sequences_separator"),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "society_id",
            "document_type",
            name="uq_document_sequences_society_type",
        ),
    )
    op.create_index(op.f("ix_document_sequences_society_id"), "document_sequences", ["society_id"])
    op.create_index(op.f("ix_document_sequences_tenant_id"), "document_sequences", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_document_sequences_tenant_id"), table_name="document_sequences")
    op.drop_index(op.f("ix_document_sequences_society_id"), table_name="document_sequences")
    op.drop_table("document_sequences")
