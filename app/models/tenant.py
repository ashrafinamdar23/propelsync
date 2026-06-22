from sqlalchemy import CheckConstraint, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended')",
            name="ck_tenants_status",
        ),
        CheckConstraint(
            "char_length(currency) = 3",
            name="ck_tenants_currency_length",
        ),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    subscription_plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="starter",
    )
    billing_email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="Asia/Kolkata")
    locale: Mapped[str] = mapped_column(String(20), nullable=False, default="en-IN")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
