import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class BuildingFloor(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "building_floors"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "society_id",
            "building_id",
            "floor_label",
            name="uq_building_floors_label",
        ),
        UniqueConstraint(
            "tenant_id",
            "society_id",
            "building_id",
            "floor_number",
            name="uq_building_floors_number",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_building_floors_status",
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
    floor_label: Mapped[str] = mapped_column(String(100), nullable=False)
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
