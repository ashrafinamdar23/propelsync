import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OtherIncomeReceiptCreate(BaseModel):
    receipt_date: date
    payer_name: str = Field(min_length=1, max_length=255)
    payer_type: str = Field(pattern="^(bank|vendor|resident|external_party|other)$")
    income_account_id: uuid.UUID
    deposit_account_id: uuid.UUID
    amount: Decimal = Field(gt=0, decimal_places=2)
    receipt_mode: str = Field(pattern="^(cash|bank_transfer|cheque|upi|card|other)$")
    reference_number: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=255)
    notes: str | None = None


class OtherIncomeReceiptReverseRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class OtherIncomeReceiptRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    income_account_id: uuid.UUID
    deposit_account_id: uuid.UUID
    journal_entry_id: uuid.UUID | None = None
    receipt_date: date
    payer_name: str
    payer_type: str
    amount: Decimal = Field(gt=0, decimal_places=2)
    receipt_mode: str
    reference_number: str | None = None
    description: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
