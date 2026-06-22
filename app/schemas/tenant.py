import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=2, max_length=100)
    subscription_plan: str = Field(default="starter", min_length=1, max_length=50)
    billing_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=100)
    locale: str = Field(default="en-IN", min_length=1, max_length=20)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TenantUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    subscription_plan: str = Field(min_length=1, max_length=50)
    billing_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    timezone: str = Field(min_length=1, max_length=100)
    locale: str = Field(min_length=1, max_length=20)
    currency: str = Field(min_length=3, max_length=3)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TenantRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    subscription_plan: str
    billing_email: str | None
    phone: str | None
    timezone: str
    locale: str
    currency: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
