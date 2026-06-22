import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChartOfAccountBase(BaseModel):
    parent_account_id: uuid.UUID | None = None
    account_code: str = Field(min_length=1, max_length=50)
    account_name: str = Field(min_length=1, max_length=255)
    account_type: str = Field(pattern="^(asset|liability|equity|income|expense)$")
    normal_balance: str = Field(pattern="^(debit|credit)$")
    description: str | None = None

    @field_validator("parent_account_id", mode="before")
    @classmethod
    def blank_parent_account_id_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


class ChartOfAccountCreate(ChartOfAccountBase):
    pass


class ChartOfAccountUpdate(ChartOfAccountBase):
    pass


class ChartOfAccountRead(ChartOfAccountBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
