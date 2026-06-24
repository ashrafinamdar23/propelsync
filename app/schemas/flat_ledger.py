import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class FlatLedgerLineRead(BaseModel):
    line_date: date
    source_type: str
    source_id: uuid.UUID
    reference_number: str | None = None
    description: str
    debit_amount: Decimal = Field(ge=0, decimal_places=2)
    credit_amount: Decimal = Field(ge=0, decimal_places=2)
    running_balance: Decimal = Field(decimal_places=2)
    status: str


class FlatLedgerRead(BaseModel):
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    flat_id: uuid.UUID
    flat_number: str
    date_from: date | None = None
    date_to: date | None = None
    opening_balance: Decimal = Field(decimal_places=2)
    total_debits: Decimal = Field(ge=0, decimal_places=2)
    total_credits: Decimal = Field(ge=0, decimal_places=2)
    closing_balance: Decimal = Field(decimal_places=2)
    lines: list[FlatLedgerLineRead]
