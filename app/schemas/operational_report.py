import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class BillingReportRow(BaseModel):
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
    status: str


class BillingReportRead(BaseModel):
    society_id: uuid.UUID
    period_start: date
    period_end: date
    invoice_count: int
    total_billed: Decimal = Field(decimal_places=2)
    total_paid: Decimal = Field(decimal_places=2)
    total_due: Decimal = Field(decimal_places=2)
    rows: list[BillingReportRow]


class CollectionReportRow(BaseModel):
    payment_id: uuid.UUID
    payment_date: date
    flat_number: str
    building_name: str
    wing_name: str | None = None
    payment_mode: str
    reference_number: str | None = None
    amount: Decimal = Field(decimal_places=2)
    unapplied_amount: Decimal = Field(decimal_places=2)
    status: str


class CollectionReportRead(BaseModel):
    society_id: uuid.UUID
    period_start: date
    period_end: date
    payment_count: int
    total_collected: Decimal = Field(decimal_places=2)
    total_unapplied: Decimal = Field(decimal_places=2)
    rows: list[CollectionReportRow]


class ExpenseReportRow(BaseModel):
    expense_id: uuid.UUID
    expense_date: date
    due_date: date
    category_name: str
    vendor_name: str | None = None
    expense_type: str
    reference_number: str | None = None
    vendor_bill_number: str | None = None
    description: str
    amount: Decimal = Field(decimal_places=2)
    tax_amount: Decimal = Field(decimal_places=2)
    total_amount: Decimal = Field(decimal_places=2)
    amount_paid: Decimal = Field(decimal_places=2)
    amount_due: Decimal = Field(decimal_places=2)
    status: str
    payment_status: str


class ExpenseReportRead(BaseModel):
    society_id: uuid.UUID
    period_start: date
    period_end: date
    expense_count: int
    total_expense: Decimal = Field(decimal_places=2)
    total_paid: Decimal = Field(decimal_places=2)
    total_due: Decimal = Field(decimal_places=2)
    rows: list[ExpenseReportRow]


class DefaulterReportRow(BaseModel):
    flat_id: uuid.UUID
    flat_number: str
    building_name: str
    wing_name: str | None = None
    invoice_count: int
    overdue_amount: Decimal = Field(decimal_places=2)
    oldest_due_date: date | None = None
    days_overdue: int


class DefaulterReportRead(BaseModel):
    society_id: uuid.UUID
    as_of_date: date
    defaulter_count: int
    total_overdue: Decimal = Field(decimal_places=2)
    rows: list[DefaulterReportRow]
