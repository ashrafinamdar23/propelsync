import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SocietyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    registration_number: str | None = Field(default=None, max_length=100)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str = Field(default="India", min_length=1, max_length=100)
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=100)
    locale: str = Field(default="en-IN", min_length=1, max_length=20)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    financial_year_start_month: int = Field(default=4, ge=1, le=12)
    receivable_account_id: uuid.UUID | None = None
    payable_account_id: uuid.UUID | None = None


class SocietyCreate(SocietyBase):
    pass


class SocietyUpdate(SocietyBase):
    pass


class SocietyRead(SocietyBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
