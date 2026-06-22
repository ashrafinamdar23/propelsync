import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LateFeeRuleBase(BaseModel):
    charge_type_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    calculation_method: Literal["fixed", "percent_of_due"]
    amount: Decimal = Field(gt=0, decimal_places=2)
    grace_days: int = Field(ge=0)
    repeat_interval_days: int | None = Field(default=None, gt=0)
    max_applications_per_invoice: int | None = Field(default=None, gt=0)
    effective_from: date
    effective_to: date | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "LateFeeRuleBase":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Effective to must be on or after effective from.")
        return self


class LateFeeRuleCreate(LateFeeRuleBase):
    pass


class LateFeeRuleUpdate(LateFeeRuleBase):
    pass


class LateFeeRuleRead(LateFeeRuleBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LateFeePreviewRequest(BaseModel):
    as_of_date: date
    late_fee_rule_ids: list[uuid.UUID] = Field(min_length=1)


class LateFeePreviewRow(BaseModel):
    original_invoice_id: uuid.UUID
    original_invoice_number: str
    flat_id: uuid.UUID
    flat_number: str
    due_date: date
    applied_as_of_date: date
    days_overdue: int
    amount_due: Decimal = Field(ge=0, decimal_places=2)
    late_fee_rule_id: uuid.UUID
    late_fee_rule_name: str
    status: Literal["valid", "invalid", "skipped"]
    errors: list[str]
    penalty_amount: Decimal = Field(ge=0, decimal_places=2)


class LateFeePreviewResponse(BaseModel):
    as_of_date: date
    invoice_count: int
    valid_rows: int
    invalid_rows: int
    skipped_rows: int
    total_penalty_amount: Decimal = Field(ge=0, decimal_places=2)
    rows: list[LateFeePreviewRow]


class LateFeeApplyResponse(BaseModel):
    generated_count: int
    invoice_ids: list[uuid.UUID]
