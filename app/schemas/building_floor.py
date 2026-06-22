import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildingFloorBase(BaseModel):
    floor_label: str = Field(min_length=1, max_length=100)
    floor_number: int


class BuildingFloorCreate(BuildingFloorBase):
    pass


class BuildingFloorUpdate(BuildingFloorBase):
    pass


class BuildingFloorRead(BuildingFloorBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    building_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
