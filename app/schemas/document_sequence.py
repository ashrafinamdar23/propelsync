import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentSequenceBase(BaseModel):
    prefix: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9]+$")
    include_period: bool = True
    include_financial_year: bool = False
    separator: str = Field(default="-", max_length=3)
    next_sequence: int = Field(ge=1)
    padding: int = Field(ge=1, le=10)
    reset_policy: str = Field(pattern="^(monthly|financial_year|never)$")

    @model_validator(mode="after")
    def validate_shape(self) -> "DocumentSequenceBase":
        if self.separator and not all(character in "-_/." for character in self.separator):
            raise ValueError("Separator may only contain -, _, /, or .")
        return self


class DocumentSequenceUpdate(DocumentSequenceBase):
    pass


class DocumentSequenceRead(DocumentSequenceBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    document_type: str
    current_reset_key: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
