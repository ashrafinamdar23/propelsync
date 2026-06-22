import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Flat(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "flats"
    __table_args__ = (
        Index(
            "uq_flats_number_with_wing",
            "tenant_id",
            "society_id",
            "building_id",
            "wing_id",
            "flat_number",
            unique=True,
            postgresql_where=text("wing_id IS NOT NULL"),
        ),
        Index(
            "uq_flats_number_without_wing",
            "tenant_id",
            "society_id",
            "building_id",
            "flat_number",
            unique=True,
            postgresql_where=text("wing_id IS NULL"),
        ),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_flats_status",
        ),
        CheckConstraint(
            "carpet_area_sqft IS NULL OR carpet_area_sqft >= 0",
            name="ck_flats_carpet_area_non_negative",
        ),
        CheckConstraint(
            "built_up_area_sqft IS NULL OR built_up_area_sqft >= 0",
            name="ck_flats_built_up_area_non_negative",
        ),
        CheckConstraint(
            "parking_count >= 0",
            name="ck_flats_parking_count_non_negative",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id"),
        nullable=False,
        index=True,
    )
    wing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wings.id"),
        nullable=True,
        index=True,
    )
    floor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("building_floors.id"),
        nullable=True,
        index=True,
    )
    flat_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("flat_types.id"),
        nullable=True,
        index=True,
    )
    flat_number: Mapped[str] = mapped_column(String(50), nullable=False)
    floor_number: Mapped[int | None] = mapped_column(Integer)
    carpet_area_sqft: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    built_up_area_sqft: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    parking_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
