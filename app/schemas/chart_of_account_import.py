import uuid
from typing import Literal

from pydantic import BaseModel, Field


class ChartOfAccountImportInput(BaseModel):
    account_code: str | None = Field(default=None, max_length=50)
    parent_account_code: str | None = Field(default=None, max_length=50)
    account_name: str | None = Field(default=None, max_length=255)
    account_type: str | None = Field(default=None, max_length=30)
    normal_balance: str | None = Field(default=None, max_length=30)
    description: str | None = None


class ChartOfAccountImportPreviewRequest(BaseModel):
    rows: list[ChartOfAccountImportInput] = Field(min_length=1, max_length=1000)


class ChartOfAccountImportConfirmRequest(BaseModel):
    rows: list[ChartOfAccountImportInput] = Field(min_length=1, max_length=1000)


class ChartOfAccountImportPreviewRow(BaseModel):
    row_number: int
    input: ChartOfAccountImportInput
    status: Literal["valid", "invalid"]
    errors: list[str]


class ChartOfAccountImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[ChartOfAccountImportPreviewRow]


class ChartOfAccountImportConfirmResponse(BaseModel):
    imported_count: int
    account_ids: list[uuid.UUID]
