import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class JournalEntry(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('manual', 'opening_balance', 'invoice', 'payment', 'expense', 'expense_payment', 'transfer')",
            name="ck_journal_entries_source_type",
        ),
        CheckConstraint("status IN ('posted', 'reversed')", name="ck_journal_entries_status"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id"), nullable=False, index=True)
    journal_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    reversal_of_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id"),
        nullable=True,
        index=True,
    )
    reference_number: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="posted")
    notes: Mapped[str | None] = mapped_column(Text)


class JournalLine(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "journal_lines"
    __table_args__ = (
        UniqueConstraint("tenant_id", "journal_entry_id", "line_number", name="uq_journal_lines_entry_line"),
        CheckConstraint("line_number > 0", name="ck_journal_lines_line_number_positive"),
        CheckConstraint("debit_amount >= 0", name="ck_journal_lines_debit_non_negative"),
        CheckConstraint("credit_amount >= 0", name="ck_journal_lines_credit_non_negative"),
        CheckConstraint("debit_amount + credit_amount > 0", name="ck_journal_lines_amount_positive"),
        CheckConstraint(
            "debit_amount = 0 OR credit_amount = 0",
            name="ck_journal_lines_single_sided",
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id"), nullable=False, index=True)
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
