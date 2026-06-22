import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class LeaseAgreement(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "lease_agreements"
    __table_args__ = (
        Index(
            "uq_lease_agreements_active_flat",
            "tenant_id",
            "society_id",
            "flat_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        CheckConstraint(
            "status IN ('draft', 'active', 'expired', 'terminated', 'renewed')",
            name="ck_lease_agreements_status",
        ),
        CheckConstraint(
            "police_verification_status IN ('not_required', 'pending', 'completed')",
            name="ck_lease_agreements_police_verification_status",
        ),
        CheckConstraint(
            "agreement_end_date >= agreement_start_date",
            name="ck_lease_agreements_agreement_dates",
        ),
        CheckConstraint(
            "move_out_date IS NULL OR move_out_date >= move_in_date",
            name="ck_lease_agreements_move_dates",
        ),
        CheckConstraint(
            "monthly_rent IS NULL OR monthly_rent >= 0",
            name="ck_lease_agreements_monthly_rent_non_negative",
        ),
        CheckConstraint(
            "security_deposit IS NULL OR security_deposit >= 0",
            name="ck_lease_agreements_security_deposit_non_negative",
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
    resident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("residents.id"),
        nullable=True,
        index=True,
    )
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_email: Mapped[str | None] = mapped_column(String(255), index=True)
    tenant_mobile_number: Mapped[str | None] = mapped_column(String(20), index=True)
    agreement_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    agreement_end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    move_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    move_out_date: Mapped[date | None] = mapped_column(Date)
    monthly_rent: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    security_deposit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    police_verification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )
    document_reference: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    notes: Mapped[str | None] = mapped_column(Text)
