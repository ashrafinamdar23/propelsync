import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = None


class ExpenseCategoryWrite(ExpenseCategoryBase):
    expense_account_id: uuid.UUID


class ExpenseCategoryCreate(ExpenseCategoryWrite):
    pass


class ExpenseCategoryUpdate(ExpenseCategoryWrite):
    pass


class ExpenseCategoryRead(ExpenseCategoryBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    expense_account_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
