import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FlatBase(BaseModel):
    wing_id: uuid.UUID | None = None
    floor_id: uuid.UUID | None = None
    flat_type_id: uuid.UUID | None = None
    flat_number: str = Field(min_length=1, max_length=50)
    floor_number: int | None = None
    carpet_area_sqft: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    built_up_area_sqft: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    parking_count: int | None = Field(default=None, ge=0)


class FlatCreate(FlatBase):
    pass


class FlatUpdate(FlatBase):
    pass


class FlatRead(FlatBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    building_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
