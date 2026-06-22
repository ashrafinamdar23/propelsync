import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class AgeingBuckets(BaseModel):
    current: Decimal = Field(decimal_places=2)
    days_1_30: Decimal = Field(decimal_places=2)
    days_31_60: Decimal = Field(decimal_places=2)
    days_61_90: Decimal = Field(decimal_places=2)
    days_90_plus: Decimal = Field(decimal_places=2)


class OutstandingFlatRow(BaseModel):
    flat_id: uuid.UUID
    flat_number: str
    building_id: uuid.UUID
    building_name: str
    wing_id: uuid.UUID | None = None
    wing_name: str | None = None
    invoice_count: int
    total_outstanding: Decimal = Field(decimal_places=2)
    overdue_amount: Decimal = Field(decimal_places=2)
    oldest_due_date: date | None = None
    ageing: AgeingBuckets


class OutstandingSummary(BaseModel):
    society_id: uuid.UUID
    as_of_date: date
    flat_count: int
    flats_with_outstanding: int
    invoice_count: int
    total_outstanding: Decimal = Field(decimal_places=2)
    overdue_amount: Decimal = Field(decimal_places=2)
    ageing: AgeingBuckets
    rows: list[OutstandingFlatRow]
