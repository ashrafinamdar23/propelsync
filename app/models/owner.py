import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Owner(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "owners"
    __table_args__ = (
        Index(
            "uq_owners_society_user",
            "tenant_id",
            "society_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        CheckConstraint(
            "owner_type IN ('individual', 'company', 'trust', 'other')",
            name="ck_owners_owner_type",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_owners_status",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    owner_type: Mapped[str] = mapped_column(String(30), nullable=False, default="individual")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    mobile_number: Mapped[str | None] = mapped_column(String(20), index=True)
    tax_identifier: Mapped[str | None] = mapped_column(String(50))
    billing_address: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
