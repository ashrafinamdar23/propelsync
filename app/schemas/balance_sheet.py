import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class BalanceSheetRowRead(BaseModel):
    account_id: uuid.UUID | None = None
    account_code: str
    account_name: str
    account_type: str
    amount: Decimal = Field(decimal_places=2)


class BalanceSheetReportRead(BaseModel):
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    as_of_date: date
    total_assets: Decimal = Field(decimal_places=2)
    total_liabilities: Decimal = Field(decimal_places=2)
    total_equity: Decimal = Field(decimal_places=2)
    current_surplus: Decimal = Field(decimal_places=2)
    total_liabilities_and_equity: Decimal = Field(decimal_places=2)
    is_balanced: bool
    asset_rows: list[BalanceSheetRowRead]
    liability_rows: list[BalanceSheetRowRead]
    equity_rows: list[BalanceSheetRowRead]
