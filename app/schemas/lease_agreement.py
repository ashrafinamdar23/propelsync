import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class LeaseAgreementBase(BaseModel):
    owner_id: uuid.UUID
    resident_id: uuid.UUID | None = None
    tenant_name: str = Field(min_length=1, max_length=255)
    tenant_email: EmailStr | None = None
    tenant_mobile_number: str | None = Field(default=None, max_length=20)
    agreement_start_date: date
    agreement_end_date: date
    move_in_date: date
    move_out_date: date | None = None
    monthly_rent: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    security_deposit: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    police_verification_status: str = Field(
        default="pending",
        pattern="^(not_required|pending|completed)$",
    )
    document_reference: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "LeaseAgreementBase":
        if self.agreement_end_date < self.agreement_start_date:
            raise ValueError("agreement_end_date must be on or after agreement_start_date.")
        if self.move_out_date is not None and self.move_out_date < self.move_in_date:
            raise ValueError("move_out_date must be on or after move_in_date.")
        return self


class LeaseAgreementCreate(LeaseAgreementBase):
    pass


class LeaseAgreementUpdate(LeaseAgreementBase):
    pass


class LeaseAgreementTerminate(BaseModel):
    move_out_date: date
    reason: str = Field(min_length=3, max_length=500)


class LeaseAgreementRead(LeaseAgreementBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    building_id: uuid.UUID
    flat_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
