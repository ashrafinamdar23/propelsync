import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class ResidentBase(BaseModel):
    owner_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    resident_type: str = Field(
        pattern="^(owner_occupier|tenant|family_member|staff|other)$",
    )
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    mobile_number: str | None = Field(default=None, max_length=20)
    move_in_date: date
    move_out_date: date | None = None

    @model_validator(mode="after")
    def validate_move_dates(self) -> "ResidentBase":
        if self.move_out_date is not None and self.move_out_date < self.move_in_date:
            raise ValueError("move_out_date must be on or after move_in_date.")
        return self


class ResidentCreate(ResidentBase):
    pass


class ResidentUpdate(ResidentBase):
    pass


class ResidentMoveOut(BaseModel):
    move_out_date: date


class ResidentRead(ResidentBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    flat_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
