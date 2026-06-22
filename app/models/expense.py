import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Expense(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "expenses"
    __table_args__ = (
        Index(
            "uq_expenses_vendor_bill_number",
            "tenant_id",
            "society_id",
            "vendor_id",
            "vendor_bill_number",
            unique=True,
            postgresql_where=text("vendor_id IS NOT NULL AND vendor_bill_number IS NOT NULL"),
        ),
        CheckConstraint("expense_date <= due_date", name="ck_expenses_due_date"),
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        CheckConstraint("tax_amount >= 0", name="ck_expenses_tax_amount_non_negative"),
        CheckConstraint("total_amount >= 0", name="ck_expenses_total_amount_non_negative"),
        CheckConstraint("amount_paid >= 0", name="ck_expenses_amount_paid_non_negative"),
        CheckConstraint("amount_due >= 0", name="ck_expenses_amount_due_non_negative"),
        CheckConstraint(
            "expense_type IN ('vendor_bill', 'cash_expense', 'other')",
            name="ck_expenses_type",
        ),
        CheckConstraint(
            "status IN ('recorded', 'approved', 'cancelled')",
            name="ck_expenses_status",
        ),
        CheckConstraint(
            "payment_status IN ('unpaid', 'partially_paid', 'paid')",
            name="ck_expenses_payment_status",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id"),
        nullable=True,
        index=True,
    )
    expense_category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expense_categories.id"),
        nullable=False,
        index=True,
    )
    expense_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id"),
        nullable=False,
        index=True,
    )
    payment_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id"),
        nullable=True,
        index=True,
    )
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id"),
        nullable=True,
        index=True,
    )
    expense_type: Mapped[str] = mapped_column(String(30), nullable=False, default="vendor_bill")
    vendor_bill_number: Mapped[str | None] = mapped_column(String(100))
    reference_number: Mapped[str | None] = mapped_column(String(100))
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="recorded")
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="unpaid")
    notes: Mapped[str | None] = mapped_column(Text)
