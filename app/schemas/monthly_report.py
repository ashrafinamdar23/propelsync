import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.balance_sheet import BalanceSheetReportRead


class MonthlyReportSummary(BaseModel):
    opening_bank_balance: Decimal = Field(decimal_places=2)
    opening_cash_balance: Decimal = Field(decimal_places=2)
    opening_total_balance: Decimal = Field(decimal_places=2)
    bank_collection: Decimal = Field(decimal_places=2)
    cash_collection: Decimal = Field(decimal_places=2)
    total_collection: Decimal = Field(decimal_places=2)
    bank_expense: Decimal = Field(decimal_places=2)
    cash_expense: Decimal = Field(decimal_places=2)
    total_expense: Decimal = Field(decimal_places=2)
    closing_bank_balance: Decimal = Field(decimal_places=2)
    closing_cash_balance: Decimal = Field(decimal_places=2)
    closing_total_balance: Decimal = Field(decimal_places=2)
    pending_due_amount: Decimal = Field(decimal_places=2)


class MonthlyCollectionRow(BaseModel):
    payment_id: uuid.UUID
    payment_date: date
    flat_number: str
    building_name: str
    wing_name: str | None = None
    payment_mode: str
    account_name: str | None = None
    reference_number: str | None = None
    amount: Decimal = Field(decimal_places=2)
    normal_amount: Decimal = Field(decimal_places=2)
    penalty_amount: Decimal = Field(decimal_places=2)
    unapplied_amount: Decimal = Field(decimal_places=2)
    status: str


class MonthlyExpenseRow(BaseModel):
    expense_id: uuid.UUID
    expense_date: date
    due_date: date
    category_name: str
    vendor_name: str | None = None
    payment_account_name: str | None = None
    expense_type: str
    reference_number: str | None = None
    vendor_bill_number: str | None = None
    description: str
    total_amount: Decimal = Field(decimal_places=2)
    amount_paid: Decimal = Field(decimal_places=2)
    amount_due: Decimal = Field(decimal_places=2)
    payment_status: str
    status: str


class MonthlyPendingDueRow(BaseModel):
    invoice_id: uuid.UUID
    invoice_number: str
    flat_number: str
    building_name: str
    wing_name: str | None = None
    invoice_date: date
    due_date: date
    billing_period_start: date
    billing_period_end: date
    total_amount: Decimal = Field(decimal_places=2)
    amount_paid: Decimal = Field(decimal_places=2)
    amount_due: Decimal = Field(decimal_places=2)
    days_overdue: int
    status: str


class MonthlyBalanceRow(BaseModel):
    month_start: date
    opening_bank_balance: Decimal = Field(decimal_places=2)
    opening_cash_balance: Decimal = Field(decimal_places=2)
    bank_collection: Decimal = Field(decimal_places=2)
    cash_collection: Decimal = Field(decimal_places=2)
    bank_expense: Decimal = Field(decimal_places=2)
    cash_expense: Decimal = Field(decimal_places=2)
    closing_bank_balance: Decimal = Field(decimal_places=2)
    closing_cash_balance: Decimal = Field(decimal_places=2)
    closing_total_balance: Decimal = Field(decimal_places=2)


class MonthlySocietyReportRead(BaseModel):
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    report_month: str
    period_start: date
    period_end: date
    summary: MonthlyReportSummary
    collections: list[MonthlyCollectionRow]
    expenses: list[MonthlyExpenseRow]
    pending_dues: list[MonthlyPendingDueRow]
    month_on_month: list[MonthlyBalanceRow]
    balance_sheet: BalanceSheetReportRead
