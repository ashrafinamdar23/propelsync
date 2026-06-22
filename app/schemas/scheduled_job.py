import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ScheduledBillingRuleDueRead(BaseModel):
    billing_rule_id: uuid.UUID
    billing_rule_name: str
    charge_type_id: uuid.UUID
    next_generation_date: date | None
    frequency: str
    generation_day: int
    due_day: int
    status: str
    reason: str


class ScheduledLateFeeRuleDueRead(BaseModel):
    late_fee_rule_id: uuid.UUID
    late_fee_rule_name: str
    charge_type_id: uuid.UUID
    grace_days: int
    eligible_invoice_count: int
    total_penalty_amount: Decimal = Field(ge=0, decimal_places=2)
    status: str
    reason: str


class ScheduledDueWorkRead(BaseModel):
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    as_of_date: date
    billing_due_count: int
    late_fee_due_count: int
    billing_rules: list[ScheduledBillingRuleDueRead]
    late_fee_rules: list[ScheduledLateFeeRuleDueRead]


class ScheduledJobRunRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    job_type: str
    run_mode: str
    status: str
    as_of_date: date
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: str | None = None
    error_message: str | None = None
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduledRunDueJobsRequest(BaseModel):
    as_of_date: date
    include_billing: bool = True
    include_late_fees: bool = True


class ScheduledRunDueJobsResponse(BaseModel):
    billing_job_run: ScheduledJobRunRead | None = None
    late_fee_job_run: ScheduledJobRunRead | None = None
    generated_invoice_count: int
    generated_penalty_invoice_count: int
    billing_rule_count: int
    late_fee_rule_count: int
