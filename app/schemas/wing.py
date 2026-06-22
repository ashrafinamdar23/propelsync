import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WingBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)


class WingCreate(WingBase):
    pass


class WingUpdate(WingBase):
    pass


class WingRead(WingBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    building_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
