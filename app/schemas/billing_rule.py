import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BillingRuleBase(BaseModel):
    charge_type_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    calculation_method: str = Field(pattern="^(fixed|area_based|parking_based|flat_type_fixed|manual)$")
    amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    area_basis: str | None = Field(default=None, pattern="^(carpet_area|built_up_area)$")
    frequency: str = Field(pattern="^(monthly|quarterly|half_yearly|yearly|one_time)$")
    generation_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)
    billing_period_timing: str = Field(pattern="^(current_period|next_period)$")
    next_generation_date: date | None = None
    scope_type: str = Field(pattern="^(all_flats|building|wing|flat_type)$")
    building_id: uuid.UUID | None = None
    wing_id: uuid.UUID | None = None
    flat_type_id: uuid.UUID | None = None
    effective_from: date
    effective_to: date | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_rule_shape(self) -> "BillingRuleBase":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Effective to must be on or after effective from.")

        if self.calculation_method == "area_based" and self.area_basis is None:
            raise ValueError("Area basis is required for area-based rules.")
        if self.calculation_method != "area_based" and self.area_basis is not None:
            raise ValueError("Area basis is only allowed for area-based rules.")

        if self.calculation_method != "manual" and self.amount is None:
            raise ValueError("Amount is required for automatic billing rules.")

        if self.scope_type == "all_flats":
            if self.building_id is not None or self.wing_id is not None or self.flat_type_id is not None:
                raise ValueError("All-flats rules cannot include building, wing, or flat type scope.")
        elif self.scope_type == "building":
            if self.building_id is None or self.wing_id is not None or self.flat_type_id is not None:
                raise ValueError("Building scope requires only building.")
        elif self.scope_type == "wing":
            if self.building_id is None or self.wing_id is None or self.flat_type_id is not None:
                raise ValueError("Wing scope requires building and wing.")
        elif self.scope_type == "flat_type":
            if self.flat_type_id is None or self.building_id is not None or self.wing_id is not None:
                raise ValueError("Flat-type scope requires only flat type.")

        if self.calculation_method == "flat_type_fixed" and self.scope_type != "flat_type":
            raise ValueError("Flat-type fixed rules must use flat-type scope.")
        return self


class BillingRuleCreate(BillingRuleBase):
    pass


class BillingRuleUpdate(BillingRuleBase):
    pass


class BillingRuleRead(BillingRuleBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    society_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
