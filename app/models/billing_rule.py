import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class BillingRule(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "billing_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "society_id", "name", name="uq_billing_rules_society_name"),
        CheckConstraint(
            "calculation_method IN ('fixed', 'area_based', 'parking_based', 'flat_type_fixed', 'manual')",
            name="ck_billing_rules_calculation_method",
        ),
        CheckConstraint(
            "area_basis IS NULL OR area_basis IN ('carpet_area', 'built_up_area')",
            name="ck_billing_rules_area_basis",
        ),
        CheckConstraint(
            "frequency IN ('monthly', 'quarterly', 'half_yearly', 'yearly', 'one_time')",
            name="ck_billing_rules_frequency",
        ),
        CheckConstraint(
            "scope_type IN ('all_flats', 'building', 'wing', 'flat_type')",
            name="ck_billing_rules_scope_type",
        ),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_billing_rules_status"),
        CheckConstraint("amount IS NULL OR amount >= 0", name="ck_billing_rules_amount_non_negative"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_billing_rules_dates"),
        CheckConstraint("generation_day >= 1 AND generation_day <= 31", name="ck_billing_rules_generation_day"),
        CheckConstraint("due_day >= 1 AND due_day <= 31", name="ck_billing_rules_due_day"),
        CheckConstraint(
            "billing_period_timing IN ('current_period', 'next_period')",
            name="ck_billing_rules_period_timing",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    charge_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("charge_types.id"),
        nullable=False,
        index=True,
    )
    building_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id"),
        nullable=True,
        index=True,
    )
    wing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wings.id"),
        nullable=True,
        index=True,
    )
    flat_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("flat_types.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    area_basis: Mapped[str | None] = mapped_column(String(30))
    frequency: Mapped[str] = mapped_column(String(30), nullable=False)
    generation_day: Mapped[int] = mapped_column(nullable=False)
    due_day: Mapped[int] = mapped_column(nullable=False)
    billing_period_timing: Mapped[str] = mapped_column(String(30), nullable=False)
    next_generation_date: Mapped[date | None] = mapped_column(nullable=True, index=True)
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False)
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
