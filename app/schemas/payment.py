import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PaymentAllocationCreate(BaseModel):
    invoice_id: uuid.UUID
    allocated_amount: Decimal = Field(gt=0, decimal_places=2)


class PaymentCreate(BaseModel):
    flat_id: uuid.UUID
    owner_id: uuid.UUID | None = None
    deposit_account_id: uuid.UUID | None = None
    journal_entry_id: uuid.UUID | None = None
    payment_date: date
    amount: Decimal = Field(gt=0, decimal_places=2)
    payment_mode: str = Field(pattern="^(cash|bank_transfer|cheque|upi|card|other)$")
    reference_number: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    allocations: list[PaymentAllocationCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_allocations(self) -> "PaymentCreate":
        invoice_ids = [allocation.invoice_id for allocation in self.allocations]
        if len(invoice_ids) != len(set(invoice_ids)):
            raise ValueError("Invoice allocation rows must be unique.")
        total_allocated = sum((allocation.allocated_amount for allocation in self.allocations), Decimal("0.00"))
        if total_allocated > self.amount:
            raise ValueError("Allocated amount cannot exceed payment amount.")
        return self


class PaymentReverseRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class PaymentAllocationRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    payment_id: uuid.UUID
    invoice_id: uuid.UUID
    allocated_amount: Decimal = Field(gt=0, decimal_places=2)
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    flat_id: uuid.UUID
    owner_id: uuid.UUID | None = None
    deposit_account_id: uuid.UUID | None = None
    payment_date: date
    amount: Decimal = Field(gt=0, decimal_places=2)
    unapplied_amount: Decimal = Field(ge=0, decimal_places=2)
    payment_mode: str
    reference_number: str | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentDetailRead(PaymentRead):
    allocations: list[PaymentAllocationRead]
