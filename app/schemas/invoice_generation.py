import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class InvoiceGenerationRequest(BaseModel):
    billing_period_start: date
    billing_period_end: date
    invoice_date: date
    due_date: date
    billing_rule_ids: list[uuid.UUID] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dates(self) -> "InvoiceGenerationRequest":
        if self.billing_period_end < self.billing_period_start:
            raise ValueError("Billing period end must be on or after start.")
        if self.due_date < self.invoice_date:
            raise ValueError("Due date must be on or after invoice date.")
        return self


class InvoiceGenerationLinePreview(BaseModel):
    billing_rule_id: uuid.UUID
    charge_type_id: uuid.UUID
    description: str
    quantity: Decimal = Field(ge=0, decimal_places=2)
    unit_amount: Decimal = Field(ge=0, decimal_places=2)
    line_amount: Decimal = Field(ge=0, decimal_places=2)


class InvoiceGenerationPreviewRow(BaseModel):
    flat_id: uuid.UUID
    flat_number: str
    owner_id: uuid.UUID | None = None
    status: Literal["valid", "invalid", "skipped"]
    errors: list[str]
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    lines: list[InvoiceGenerationLinePreview]


class InvoiceGenerationPreviewResponse(BaseModel):
    billing_period_start: date
    billing_period_end: date
    invoice_date: date
    due_date: date
    total_flats: int
    invoice_count: int
    valid_rows: int
    invalid_rows: int
    skipped_rows: int
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    rows: list[InvoiceGenerationPreviewRow]


class InvoiceGenerationConfirmResponse(BaseModel):
    generated_count: int
    invoice_ids: list[uuid.UUID]
