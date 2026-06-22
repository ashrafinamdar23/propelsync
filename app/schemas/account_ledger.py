import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class AccountLedgerLineRead(BaseModel):
    journal_entry_id: uuid.UUID
    journal_line_id: uuid.UUID
    journal_date: date
    source_type: str
    source_id: uuid.UUID | None = None
    reference_number: str | None = None
    description: str
    line_description: str | None = None
    debit_amount: Decimal = Field(ge=0, decimal_places=2)
    credit_amount: Decimal = Field(ge=0, decimal_places=2)
    running_balance: Decimal = Field(decimal_places=2)


class AccountLedgerRead(BaseModel):
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    account_id: uuid.UUID
    account_code: str
    account_name: str
    account_type: str
    normal_balance: str
    date_from: date | None = None
    date_to: date | None = None
    opening_balance: Decimal = Field(decimal_places=2)
    total_debits: Decimal = Field(ge=0, decimal_places=2)
    total_credits: Decimal = Field(ge=0, decimal_places=2)
    closing_balance: Decimal = Field(decimal_places=2)
    lines: list[AccountLedgerLineRead]
