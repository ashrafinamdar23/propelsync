import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Invoice(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "society_id", "invoice_number", name="uq_invoices_number"),
        Index(
            "ix_invoices_flat_period",
            "tenant_id",
            "society_id",
            "flat_id",
            "billing_period_start",
            "billing_period_end",
        ),
        CheckConstraint(
            "status IN ('draft', 'issued', 'partially_paid', 'paid', 'overdue', 'cancelled')",
            name="ck_invoices_status",
        ),
        CheckConstraint("total_amount >= 0", name="ck_invoices_total_amount_non_negative"),
        CheckConstraint("amount_paid >= 0", name="ck_invoices_amount_paid_non_negative"),
        CheckConstraint("amount_due >= 0", name="ck_invoices_amount_due_non_negative"),
        CheckConstraint("billing_period_end >= billing_period_start", name="ck_invoices_period_dates"),
        CheckConstraint("due_date >= invoice_date", name="ck_invoices_due_date"),
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
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id"),
        nullable=True,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    notes: Mapped[str | None] = mapped_column(Text)


class InvoiceLineItem(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "invoice_line_items"
    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_id", "line_number", name="uq_invoice_line_number"),
        CheckConstraint("line_number > 0", name="ck_invoice_line_items_line_number"),
        CheckConstraint("quantity >= 0", name="ck_invoice_line_items_quantity_non_negative"),
        CheckConstraint("unit_amount >= 0", name="ck_invoice_line_items_unit_amount_non_negative"),
        CheckConstraint("line_amount >= 0", name="ck_invoice_line_items_line_amount_non_negative"),
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
    charge_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("charge_types.id"),
        nullable=False,
        index=True,
    )
    billing_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_rules.id"),
        nullable=True,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=1)
    unit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
