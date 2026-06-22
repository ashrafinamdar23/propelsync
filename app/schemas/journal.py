import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JournalLineCreate(BaseModel):
    account_id: uuid.UUID
    description: str | None = Field(default=None, max_length=255)
    debit_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    credit_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)

    @model_validator(mode="after")
    def validate_single_sided_amount(self) -> "JournalLineCreate":
        if self.debit_amount <= 0 and self.credit_amount <= 0:
            raise ValueError("Journal line must have either debit or credit amount.")
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValueError("Journal line cannot have both debit and credit amount.")
        return self


class JournalEntryCreate(BaseModel):
    journal_date: date
    reference_number: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=255)
    notes: str | None = None
    lines: list[JournalLineCreate] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_balanced(self) -> "JournalEntryCreate":
        total_debit = sum((line.debit_amount for line in self.lines), Decimal("0.00"))
        total_credit = sum((line.credit_amount for line in self.lines), Decimal("0.00"))
        if total_debit != total_credit:
            raise ValueError("Journal entry debits and credits must balance.")
        return self


class OpeningBalanceJournalCreate(BaseModel):
    opening_date: date
    reference_number: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    lines: list[JournalLineCreate] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_balanced(self) -> "OpeningBalanceJournalCreate":
        total_debit = sum((line.debit_amount for line in self.lines), Decimal("0.00"))
        total_credit = sum((line.credit_amount for line in self.lines), Decimal("0.00"))
        if total_debit != total_credit:
            raise ValueError("Opening balance debits and credits must balance.")
        return self


class JournalReverseRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class JournalLineRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    journal_entry_id: uuid.UUID
    account_id: uuid.UUID
    line_number: int
    description: str | None = None
    debit_amount: Decimal = Field(ge=0, decimal_places=2)
    credit_amount: Decimal = Field(ge=0, decimal_places=2)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalEntryRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    journal_date: date
    source_type: str
    source_id: uuid.UUID | None = None
    reversal_of_entry_id: uuid.UUID | None = None
    reference_number: str | None = None
    description: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalEntryDetailRead(JournalEntryRead):
    lines: list[JournalLineRead]
