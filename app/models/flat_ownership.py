import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class FlatOwnership(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "flat_ownerships"
    __table_args__ = (
        Index(
            "uq_flat_ownerships_flat_owner_start",
            "tenant_id",
            "society_id",
            "flat_id",
            "owner_id",
            "effective_from",
            unique=True,
        ),
        Index(
            "uq_flat_ownerships_current_primary_owner",
            "tenant_id",
            "society_id",
            "flat_id",
            unique=True,
            postgresql_where=text(
                "ownership_type = 'primary_owner' AND effective_to IS NULL AND status = 'active'"
            ),
        ),
        CheckConstraint(
            "ownership_type IN ('primary_owner', 'co_owner')",
            name="ck_flat_ownerships_ownership_type",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_flat_ownerships_status",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_flat_ownerships_effective_dates",
        ),
        CheckConstraint(
            "ownership_percentage IS NULL OR "
            "(ownership_percentage > 0 AND ownership_percentage <= 100)",
            name="ck_flat_ownerships_percentage",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    flat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("flats.id"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("owners.id"),
        nullable=False,
        index=True,
    )
    ownership_type: Mapped[str] = mapped_column(String(30), nullable=False)
    ownership_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
