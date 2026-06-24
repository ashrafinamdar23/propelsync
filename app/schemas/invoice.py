import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ManualInvoiceLineCreate(BaseModel):
    charge_type_id: uuid.UUID
    description: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0, decimal_places=2)
    unit_amount: Decimal = Field(gt=0, decimal_places=2)


class ManualInvoiceCreate(BaseModel):
    flat_id: uuid.UUID
    owner_id: uuid.UUID | None = None
    invoice_date: date
    due_date: date
    billing_period_start: date
    billing_period_end: date
    notes: str | None = None
    late_fee_rule_ids: list[uuid.UUID] = Field(default_factory=list)
    line_items: list[ManualInvoiceLineCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dates(self) -> "ManualInvoiceCreate":
        if self.billing_period_end < self.billing_period_start:
            raise ValueError("Billing period end must be on or after start.")
        if self.due_date < self.invoice_date:
            raise ValueError("Due date must be on or after invoice date.")
        return self


class InvoiceCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class InvoiceBulkCancelRequest(BaseModel):
    invoice_ids: list[uuid.UUID] = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=500)


class InvoiceBulkCancelResult(BaseModel):
    invoice_id: uuid.UUID
    status: str
    invoice_number: str | None = None
    error: str | None = None


class InvoiceBulkCancelResponse(BaseModel):
    requested_count: int
    cancelled_count: int
    failed_count: int
    results: list[InvoiceBulkCancelResult]


class InvoiceLineItemRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    invoice_id: uuid.UUID
    charge_type_id: uuid.UUID
    billing_rule_id: uuid.UUID | None = None
    line_number: int
    description: str
    quantity: Decimal = Field(ge=0, decimal_places=2)
    unit_amount: Decimal = Field(ge=0, decimal_places=2)
    line_amount: Decimal = Field(ge=0, decimal_places=2)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    flat_id: uuid.UUID
    owner_id: uuid.UUID | None = None
    journal_entry_id: uuid.UUID | None = None
    invoice_number: str
    invoice_date: date
    due_date: date
    billing_period_start: date
    billing_period_end: date
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    amount_paid: Decimal = Field(ge=0, decimal_places=2)
    amount_due: Decimal = Field(ge=0, decimal_places=2)
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceDetailRead(InvoiceRead):
    line_items: list[InvoiceLineItemRead]
