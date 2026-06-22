import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentSequence(UUIDPrimaryKeyMixin, TenantOwnedMixin, TimestampMixin, Base):
    __tablename__ = "document_sequences"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "society_id",
            "document_type",
            name="uq_document_sequences_society_type",
        ),
        CheckConstraint("document_type IN ('invoice', 'receipt')", name="ck_document_sequences_type"),
        CheckConstraint("next_sequence > 0", name="ck_document_sequences_next_sequence"),
        CheckConstraint("padding BETWEEN 1 AND 10", name="ck_document_sequences_padding"),
        CheckConstraint(
            "reset_policy IN ('monthly', 'financial_year', 'never')",
            name="ck_document_sequences_reset_policy",
        ),
        CheckConstraint("char_length(separator) BETWEEN 0 AND 3", name="ck_document_sequences_separator"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("societies.id"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False, default="INV")
    include_period: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    include_financial_year: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    separator: Mapped[str] = mapped_column(String(3), nullable=False, default="-")
    next_sequence: Mapped[int] = mapped_column(nullable=False, default=1)
    padding: Mapped[int] = mapped_column(nullable=False, default=5)
    reset_policy: Mapped[str] = mapped_column(String(30), nullable=False, default="never")
    current_reset_key: Mapped[str] = mapped_column(String(30), nullable=False, default="GLOBAL")
