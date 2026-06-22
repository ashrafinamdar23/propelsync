import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AccountTransfer(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "account_transfers"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_account_transfers_amount_positive"),
        CheckConstraint("from_account_id <> to_account_id", name="ck_account_transfers_different_accounts"),
        CheckConstraint(
            "transfer_mode IN ('cash', 'bank_transfer', 'cheque', 'upi', 'card', 'other')",
            name="ck_account_transfers_mode",
        ),
        CheckConstraint("status IN ('posted', 'reversed')", name="ck_account_transfers_status"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id"), nullable=False, index=True)
    from_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id"),
        nullable=False,
        index=True,
    )
    to_account_id: Mapped[uuid.UUID] = mapped_column(
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
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    transfer_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="posted")
    notes: Mapped[str | None] = mapped_column(Text)
