import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class IncomeExpenseRowRead(BaseModel):
    account_id: uuid.UUID
    account_code: str
    account_name: str
    account_type: str
    amount: Decimal = Field(decimal_places=2)


class IncomeExpenseReportRead(BaseModel):
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    period_start: date
    period_end: date
    total_income: Decimal = Field(ge=0, decimal_places=2)
    total_expense: Decimal = Field(ge=0, decimal_places=2)
    net_surplus: Decimal = Field(decimal_places=2)
    income_rows: list[IncomeExpenseRowRead]
    expense_rows: list[IncomeExpenseRowRead]
