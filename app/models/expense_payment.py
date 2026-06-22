import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ExpensePayment(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "expense_payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expense_payments_amount_positive"),
        CheckConstraint("unapplied_amount >= 0", name="ck_expense_payments_unapplied_non_negative"),
        CheckConstraint(
            "payment_mode IN ('cash', 'bank_transfer', 'cheque', 'upi', 'card', 'other')",
            name="ck_expense_payments_mode",
        ),
        CheckConstraint("status IN ('paid', 'reversed')", name="ck_expense_payments_status"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id"), nullable=False, index=True)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True, index=True)
    payment_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id"),
        nullable=False,
        index=True,
    )
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id"),
        nullable=True,
        index=True,
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unapplied_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    payment_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="paid")
    notes: Mapped[str | None] = mapped_column(Text)


class ExpensePaymentAllocation(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "expense_payment_allocations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "expense_payment_id", "expense_id", name="uq_expense_payment_allocation"),
        CheckConstraint("allocated_amount > 0", name="ck_expense_payment_allocations_amount_positive"),
        CheckConstraint("status IN ('active', 'reversed')", name="ck_expense_payment_allocations_status"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id"), nullable=False, index=True)
    expense_payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expense_payments.id"),
        nullable=False,
        index=True,
    )
    expense_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("expenses.id"), nullable=False, index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
