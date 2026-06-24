import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class LateFeeRule(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "late_fee_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "society_id", "name", name="uq_late_fee_rules_society_name"),
        CheckConstraint(
            "calculation_method IN ('fixed', 'percent_of_due')",
            name="ck_late_fee_rules_calculation_method",
        ),
        CheckConstraint("amount > 0", name="ck_late_fee_rules_amount_positive"),
        CheckConstraint("grace_days >= 0", name="ck_late_fee_rules_grace_days_non_negative"),
        CheckConstraint(
            "repeat_interval_days IS NULL OR repeat_interval_days > 0",
            name="ck_late_fee_rules_repeat_interval_positive",
        ),
        CheckConstraint(
            "max_applications_per_invoice IS NULL OR max_applications_per_invoice > 0",
            name="ck_late_fee_rules_max_applications_positive",
        ),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_late_fee_rules_status"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_late_fee_rules_dates"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    grace_days: Mapped[int] = mapped_column(nullable=False, default=0)
    repeat_interval_days: Mapped[int | None] = mapped_column(nullable=True)
    max_applications_per_invoice: Mapped[int | None] = mapped_column(nullable=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")


class LateFeeApplication(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "late_fee_applications"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "society_id",
            "late_fee_rule_id",
            "original_invoice_id",
            "applied_as_of_date",
            name="uq_late_fee_applications_invoice_rule_as_of",
        ),
        Index(
            "ix_late_fee_applications_original",
            "tenant_id",
            "society_id",
            "original_invoice_id",
        ),
        CheckConstraint("penalty_amount > 0", name="ck_late_fee_applications_amount_positive"),
        CheckConstraint("status IN ('active', 'cancelled')", name="ck_late_fee_applications_status"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    late_fee_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("late_fee_rules.id"),
        nullable=False,
        index=True,
    )
    original_invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )
    penalty_invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )
    applied_as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    penalty_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")


class BillingRuleLateFeeRule(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "billing_rule_late_fee_rules"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "society_id",
            "billing_rule_id",
            "late_fee_rule_id",
            name="uq_billing_rule_late_fee_rule",
        ),
        CheckConstraint("priority >= 0", name="ck_billing_rule_late_fee_rules_priority"),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_billing_rule_late_fee_rules_status"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_billing_rule_late_fee_rules_dates",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    billing_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_rules.id"),
        nullable=False,
        index=True,
    )
    late_fee_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("late_fee_rules.id"),
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(nullable=False, default=0)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")


class InvoiceLateFeeRule(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "invoice_late_fee_rules"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "society_id",
            "invoice_id",
            "late_fee_rule_id",
            name="uq_invoice_late_fee_rule",
        ),
        CheckConstraint("priority >= 0", name="ck_invoice_late_fee_rules_priority"),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_invoice_late_fee_rules_status"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )
    late_fee_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("late_fee_rules.id"),
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(nullable=False, default=0)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="billing_rule")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
