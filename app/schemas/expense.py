import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExpenseBase(BaseModel):
    vendor_id: uuid.UUID | None = None
    expense_category_id: uuid.UUID
    payment_account_id: uuid.UUID | None = None
    expense_type: str = Field(default="vendor_bill", pattern="^(vendor_bill|cash_expense|other)$")
    vendor_bill_number: str | None = Field(default=None, max_length=100)
    reference_number: str | None = Field(default=None, max_length=100)
    expense_date: date
    due_date: date
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates_and_vendor(self) -> "ExpenseBase":
        if self.due_date < self.expense_date:
            raise ValueError("Due date must be on or after expense date.")
        if self.expense_type == "vendor_bill" and self.vendor_id is None:
            raise ValueError("Vendor bill expenses require a vendor.")
        return self


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class ExpenseCancelRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ExpenseRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    vendor_id: uuid.UUID | None = None
    expense_category_id: uuid.UUID
    expense_account_id: uuid.UUID
    payment_account_id: uuid.UUID | None = None
    journal_entry_id: uuid.UUID | None = None
    expense_type: str
    vendor_bill_number: str | None = None
    reference_number: str | None = None
    expense_date: date
    due_date: date
    description: str
    amount: Decimal = Field(gt=0, decimal_places=2)
    tax_amount: Decimal = Field(ge=0, decimal_places=2)
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    amount_paid: Decimal = Field(ge=0, decimal_places=2)
    amount_due: Decimal = Field(ge=0, decimal_places=2)
    status: str
    payment_status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
