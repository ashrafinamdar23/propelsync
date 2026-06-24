"""add society member advance account

Revision ID: 20260620_0037
Revises: 20260620_0036
Create Date: 2026-06-20 00:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260620_0037"
down_revision: Union[str, None] = "20260620_0036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "societies",
        sa.Column("member_advance_account_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_societies_member_advance_account_id_chart_of_accounts",
        "societies",
        "chart_of_accounts",
        ["member_advance_account_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_societies_member_advance_account_id"),
        "societies",
        ["member_advance_account_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_societies_member_advance_account_id"), table_name="societies")
    op.drop_constraint(
        "fk_societies_member_advance_account_id_chart_of_accounts",
        "societies",
        type_="foreignkey",
    )
    op.drop_column("societies", "member_advance_account_id")
