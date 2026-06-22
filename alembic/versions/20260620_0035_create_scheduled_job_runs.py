"""create scheduled job runs

Revision ID: 20260620_0035
Revises: 20260620_0034
Create Date: 2026-06-20 00:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0035"
down_revision: str | None = "20260620_0034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheduled_job_runs",
        sa.Column("society_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("run_mode", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "job_type IN ('billing_generation', 'late_fee_application')",
            name="ck_scheduled_job_runs_job_type",
        ),
        sa.CheckConstraint("run_mode IN ('manual', 'scheduled')", name="ck_scheduled_job_runs_run_mode"),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_scheduled_job_runs_status",
        ),
        sa.ForeignKeyConstraint(["society_id"], ["societies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scheduled_job_runs_as_of_date"), "scheduled_job_runs", ["as_of_date"], unique=False)
    op.create_index(op.f("ix_scheduled_job_runs_job_type"), "scheduled_job_runs", ["job_type"], unique=False)
    op.create_index(op.f("ix_scheduled_job_runs_society_id"), "scheduled_job_runs", ["society_id"], unique=False)
    op.create_index(op.f("ix_scheduled_job_runs_status"), "scheduled_job_runs", ["status"], unique=False)
    op.create_index(op.f("ix_scheduled_job_runs_tenant_id"), "scheduled_job_runs", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scheduled_job_runs_tenant_id"), table_name="scheduled_job_runs")
    op.drop_index(op.f("ix_scheduled_job_runs_status"), table_name="scheduled_job_runs")
    op.drop_index(op.f("ix_scheduled_job_runs_society_id"), table_name="scheduled_job_runs")
    op.drop_index(op.f("ix_scheduled_job_runs_job_type"), table_name="scheduled_job_runs")
    op.drop_index(op.f("ix_scheduled_job_runs_as_of_date"), table_name="scheduled_job_runs")
    op.drop_table("scheduled_job_runs")
