import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Resident(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "residents"
    __table_args__ = (
        Index(
            "uq_residents_flat_user_current",
            "tenant_id",
            "society_id",
            "flat_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL AND move_out_date IS NULL"),
        ),
        CheckConstraint(
            "resident_type IN ('owner_occupier', 'tenant', 'family_member', 'staff', 'other')",
            name="ck_residents_resident_type",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_residents_status",
        ),
        CheckConstraint(
            "move_out_date IS NULL OR move_out_date >= move_in_date",
            name="ck_residents_move_dates",
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
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("owners.id"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    resident_type: Mapped[str] = mapped_column(String(30), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    mobile_number: Mapped[str | None] = mapped_column(String(20), index=True)
    move_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    move_out_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
