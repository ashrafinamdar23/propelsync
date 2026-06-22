import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChargeTypeBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = None


class ChargeTypeWrite(ChargeTypeBase):
    revenue_account_id: uuid.UUID


class ChargeTypeCreate(ChargeTypeWrite):
    pass


class ChargeTypeUpdate(ChargeTypeWrite):
    pass


class ChargeTypeRead(ChargeTypeBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    revenue_account_id: uuid.UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
