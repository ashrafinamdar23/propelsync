import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Society(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "societies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_societies_tenant_name"),
        UniqueConstraint(
            "tenant_id",
            "registration_number",
            name="uq_societies_tenant_registration_number",
        ),
        CheckConstraint(
            "status IN ('active', 'suspended')",
            name="ck_societies_status",
        ),
        CheckConstraint(
            "financial_year_start_month BETWEEN 1 AND 12",
            name="ck_societies_financial_year_start_month",
        ),
        CheckConstraint(
            "char_length(currency) = 3",
            name="ck_societies_currency_length",
        ),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(100))
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="Asia/Kolkata")
    locale: Mapped[str] = mapped_column(String(20), nullable=False, default="en-IN")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    financial_year_start_month: Mapped[int] = mapped_column(nullable=False, default=4)
    receivable_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id"),
        nullable=True,
        index=True,
    )
    payable_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id"),
        nullable=True,
        index=True,
    )
    member_advance_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
