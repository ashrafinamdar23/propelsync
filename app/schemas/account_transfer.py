import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AccountTransferCreate(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    transfer_date: date
    amount: Decimal = Field(gt=0, decimal_places=2)
    transfer_mode: str = Field(pattern="^(cash|bank_transfer|cheque|upi|card|other)$")
    reference_number: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=255)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_distinct_accounts(self) -> "AccountTransferCreate":
        if self.from_account_id == self.to_account_id:
            raise ValueError("Transfer source and destination accounts must be different.")
        return self


class AccountTransferRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    journal_entry_id: uuid.UUID | None = None
    transfer_date: date
    amount: Decimal = Field(gt=0, decimal_places=2)
    transfer_mode: str
    reference_number: str | None = None
    description: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
