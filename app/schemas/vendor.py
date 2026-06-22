import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VendorBase(BaseModel):
    vendor_code: str = Field(min_length=1, max_length=50)
    vendor_name: str = Field(min_length=1, max_length=255)
    vendor_type: str = Field(default="company", pattern="^(individual|company|firm|other)$")
    contact_person: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    mobile_number: str | None = Field(default=None, max_length=20)
    tax_identifier: str | None = Field(default=None, max_length=50)
    billing_address: str | None = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(VendorBase):
    pass


class VendorRead(VendorBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
