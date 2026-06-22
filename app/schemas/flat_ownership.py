import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FlatOwnershipBase(BaseModel):
    owner_id: uuid.UUID
    ownership_type: str = Field(pattern="^(primary_owner|co_owner)$")
    ownership_percentage: Decimal | None = Field(default=None, gt=0, le=100)
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_effective_dates(self) -> "FlatOwnershipBase":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from.")
        return self


class FlatOwnershipCreate(FlatOwnershipBase):
    pass


class FlatOwnershipUpdate(FlatOwnershipBase):
    pass


class FlatOwnershipClose(BaseModel):
    effective_to: date


class FlatOwnershipRead(FlatOwnershipBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    flat_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
