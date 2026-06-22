import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class TrialBalanceRowRead(BaseModel):
    account_id: uuid.UUID
    account_code: str
    account_name: str
    account_type: str
    normal_balance: str
    status: str
    debit_balance: Decimal = Field(ge=0, decimal_places=2)
    credit_balance: Decimal = Field(ge=0, decimal_places=2)


class TrialBalanceRead(BaseModel):
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    as_of_date: date
    total_debits: Decimal = Field(ge=0, decimal_places=2)
    total_credits: Decimal = Field(ge=0, decimal_places=2)
    is_balanced: bool
    rows: list[TrialBalanceRowRead]
