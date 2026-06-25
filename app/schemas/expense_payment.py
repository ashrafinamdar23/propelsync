import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExpensePaymentAllocationCreate(BaseModel):
    expense_id: uuid.UUID
    allocated_amount: Decimal = Field(gt=0, decimal_places=2)


class ExpensePaymentCreate(BaseModel):
    vendor_id: uuid.UUID | None = None
    payment_account_id: uuid.UUID
    payment_date: date
    amount: Decimal = Field(gt=0, decimal_places=2)
    payment_mode: str = Field(pattern="^(cash|bank_transfer|cheque|upi|card|other)$")
    reference_number: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    allocations: list[ExpensePaymentAllocationCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_allocations(self) -> "ExpensePaymentCreate":
        expense_ids = [allocation.expense_id for allocation in self.allocations]
        if len(expense_ids) != len(set(expense_ids)):
            raise ValueError("Expense allocation rows must be unique.")
        total_allocated = sum((allocation.allocated_amount for allocation in self.allocations), Decimal("0.00"))
        if total_allocated > self.amount:
            raise ValueError("Allocated amount cannot exceed payment amount.")
        return self


class ExpensePaymentAllocateRequest(BaseModel):
    allocations: list[ExpensePaymentAllocationCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_allocations(self) -> "ExpensePaymentAllocateRequest":
        expense_ids = [allocation.expense_id for allocation in self.allocations]
        if len(expense_ids) != len(set(expense_ids)):
            raise ValueError("Expense allocation rows must be unique.")
        return self


class ExpensePaymentAllocationRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    expense_payment_id: uuid.UUID
    expense_id: uuid.UUID
    allocated_amount: Decimal = Field(gt=0, decimal_places=2)
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpensePaymentRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    vendor_id: uuid.UUID | None = None
    payment_account_id: uuid.UUID
    journal_entry_id: uuid.UUID | None = None
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


class ExpensePaymentDetailRead(ExpensePaymentRead):
    allocations: list[ExpensePaymentAllocationRead]
