import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OwnerBase(BaseModel):
    user_id: uuid.UUID | None = None
    owner_type: str = Field(default="individual", pattern="^(individual|company|trust|other)$")
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    mobile_number: str | None = Field(default=None, max_length=20)
    tax_identifier: str | None = Field(default=None, max_length=50)
    billing_address: str | None = None


class OwnerCreate(OwnerBase):
    pass


class OwnerUpdate(OwnerBase):
    pass


class OwnerRead(OwnerBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
