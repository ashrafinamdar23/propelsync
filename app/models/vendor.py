import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Vendor(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "vendors"
    __table_args__ = (
        UniqueConstraint("tenant_id", "society_id", "vendor_code", name="uq_vendors_society_code"),
        CheckConstraint(
            "vendor_type IN ('individual', 'company', 'firm', 'other')",
            name="ck_vendors_vendor_type",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_vendors_status",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_type: Mapped[str] = mapped_column(String(30), nullable=False, default="company")
    contact_person: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    mobile_number: Mapped[str | None] = mapped_column(String(20), index=True)
    tax_identifier: Mapped[str | None] = mapped_column(String(50))
    billing_address: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
