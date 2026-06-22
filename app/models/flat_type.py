import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class FlatType(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "flat_types"
    __table_args__ = (
        UniqueConstraint("tenant_id", "society_id", "name", name="uq_flat_types_society_name"),
        UniqueConstraint("tenant_id", "society_id", "code", name="uq_flat_types_society_code"),
        CheckConstraint(
            "unit_category IN ('residential', 'commercial', 'shop', 'office', 'parking', 'other')",
            name="ck_flat_types_unit_category",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_flat_types_status",
        ),
        CheckConstraint(
            "bedroom_count IS NULL OR bedroom_count >= 0",
            name="ck_flat_types_bedroom_count_non_negative",
        ),
        CheckConstraint(
            "bathroom_count IS NULL OR bathroom_count >= 0",
            name="ck_flat_types_bathroom_count_non_negative",
        ),
        CheckConstraint(
            "carpet_area_sqft IS NULL OR carpet_area_sqft >= 0",
            name="ck_flat_types_carpet_area_non_negative",
        ),
        CheckConstraint(
            "built_up_area_sqft IS NULL OR built_up_area_sqft >= 0",
            name="ck_flat_types_built_up_area_non_negative",
        ),
        CheckConstraint(
            "default_parking_count >= 0",
            name="ck_flat_types_default_parking_count_non_negative",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50))
    unit_category: Mapped[str] = mapped_column(String(30), nullable=False, default="residential")
    bedroom_count: Mapped[int | None] = mapped_column(Integer)
    bathroom_count: Mapped[int | None] = mapped_column(Integer)
    carpet_area_sqft: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    built_up_area_sqft: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    default_parking_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
