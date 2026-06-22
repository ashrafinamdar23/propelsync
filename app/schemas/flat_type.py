import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FlatTypeBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    unit_category: str = Field(
        default="residential",
        pattern="^(residential|commercial|shop|office|parking|other)$",
    )
    bedroom_count: int | None = Field(default=None, ge=0)
    bathroom_count: int | None = Field(default=None, ge=0)
    carpet_area_sqft: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    built_up_area_sqft: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    default_parking_count: int = Field(default=0, ge=0)


class FlatTypeCreate(FlatTypeBase):
    pass


class FlatTypeUpdate(FlatTypeBase):
    pass


class FlatTypeRead(FlatTypeBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
