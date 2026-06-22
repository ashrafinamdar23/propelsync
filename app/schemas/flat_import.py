import uuid
from typing import Literal

from pydantic import BaseModel, Field


class FlatImportPreviewInput(BaseModel):
    flat_number: str | None = Field(default=None, max_length=50)
    flat_type_code: str | None = Field(default=None, max_length=50)
    floor_label: str | None = Field(default=None, max_length=100)
    wing_code: str | None = Field(default=None, max_length=50)


class FlatImportPreviewRequest(BaseModel):
    rows: list[FlatImportPreviewInput] = Field(min_length=1, max_length=1000)


class FlatImportConfirmRequest(BaseModel):
    rows: list[FlatImportPreviewInput] = Field(min_length=1, max_length=1000)


class FlatImportResolvedReference(BaseModel):
    id: uuid.UUID | None = None
    label: str | None = None


class FlatImportPreviewResolved(BaseModel):
    flat_type: FlatImportResolvedReference | None = None
    floor: FlatImportResolvedReference | None = None
    wing: FlatImportResolvedReference | None = None


class FlatImportPreviewRow(BaseModel):
    row_number: int
    input: FlatImportPreviewInput
    status: Literal["valid", "invalid"]
    errors: list[str]
    resolved: FlatImportPreviewResolved


class FlatImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[FlatImportPreviewRow]


class FlatImportConfirmResponse(BaseModel):
    imported_count: int
    flat_ids: list[uuid.UUID]
