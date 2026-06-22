import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.models import BillingRule, Building, ChargeType, FlatType, Society, User, Wing
from app.schemas.billing_rule import BillingRuleCreate, BillingRuleUpdate
from app.services.billing_rules import (
    BillingRuleAlreadyExistsError,
    BillingRuleReferenceInvalidError,
    change_billing_rule_status,
    create_billing_rule,
    update_billing_rule,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_rule: BillingRule | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_rule = existing_rule
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_rule

    def add(self, instance: object) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        for instance in self.added:
            if getattr(instance, "id", None) is None:
                instance.id = uuid.uuid4()

    def commit(self) -> None:
        self.committed = True

    def refresh(self, _: object) -> None:
        return None


def build_actor() -> User:
    return User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@example.com",
        full_name="Society Admin",
    )


def build_context(tenant_id: uuid.UUID, actor: User) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant=None,  # type: ignore[arg-type]
        user=actor,
    )


def build_payload(charge_type_id: uuid.UUID, **overrides: object) -> BillingRuleCreate:
    values = {
        "charge_type_id": charge_type_id,
        "name": "Monthly Maintenance",
        "calculation_method": "fixed",
        "amount": Decimal("2500.00"),
        "area_basis": None,
        "frequency": "monthly",
        "generation_day": 1,
        "due_day": 10,
        "billing_period_timing": "current_period",
        "next_generation_date": date(2026, 4, 1),
        "scope_type": "all_flats",
        "building_id": None,
        "wing_id": None,
        "flat_type_id": None,
        "effective_from": date(2026, 4, 1),
        "effective_to": None,
        "description": None,
    }
    values.update(overrides)
    return BillingRuleCreate(**values)


def test_create_billing_rule_adds_rule_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    charge_type_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    charge_type = ChargeType(
        id=charge_type_id,
        tenant_id=tenant_id,
        society_id=society_id,
        name="Maintenance",
        revenue_account_id=uuid.uuid4(),
        status="active",
    )
    session = FakeSession(scalar_results=[society, None, charge_type])

    rule = create_billing_rule(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=build_payload(charge_type_id),
        actor=actor,
    )

    assert rule.tenant_id == tenant_id
    assert rule.society_id == society_id
    assert rule.charge_type_id == charge_type_id
    assert rule.amount == Decimal("2500.00")
    assert session.committed is True
    assert len(session.added) == 2


def test_create_billing_rule_rejects_duplicate_name() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    charge_type_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    existing = BillingRule(
        tenant_id=tenant_id,
        society_id=society_id,
        charge_type_id=charge_type_id,
        name="Monthly Maintenance",
        calculation_method="fixed",
        amount=Decimal("2500.00"),
        frequency="monthly",
        generation_day=1,
        due_day=10,
        billing_period_timing="current_period",
        next_generation_date=date(2026, 4, 1),
        scope_type="all_flats",
        effective_from=date(2026, 4, 1),
        status="active",
    )
    session = FakeSession(scalar_results=[society, existing])

    with pytest.raises(BillingRuleAlreadyExistsError):
        create_billing_rule(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=build_payload(charge_type_id),
            actor=actor,
        )


def test_create_billing_rule_rejects_invalid_charge_type() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    charge_type_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    session = FakeSession(scalar_results=[society, None, None])

    with pytest.raises(BillingRuleReferenceInvalidError):
        create_billing_rule(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=build_payload(charge_type_id),
            actor=actor,
        )


def test_create_billing_rule_accepts_wing_scope() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    charge_type_id = uuid.uuid4()
    building_id = uuid.uuid4()
    wing_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    charge_type = ChargeType(
        id=charge_type_id,
        tenant_id=tenant_id,
        society_id=society_id,
        name="Maintenance",
        status="active",
    )
    building = Building(
        id=building_id,
        tenant_id=tenant_id,
        society_id=society_id,
        name="Tower A",
        status="active",
    )
    wing = Wing(
        id=wing_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        name="A",
        status="active",
    )
    session = FakeSession(scalar_results=[society, None, charge_type, building, wing])

    rule = create_billing_rule(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=build_payload(
            charge_type_id,
            scope_type="wing",
            building_id=building_id,
            wing_id=wing_id,
        ),
        actor=actor,
    )

    assert rule.building_id == building_id
    assert rule.wing_id == wing_id


def test_update_billing_rule_changes_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    charge_type_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    rule = BillingRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        charge_type_id=charge_type_id,
        name="Monthly Maintenance",
        calculation_method="fixed",
        amount=Decimal("2500.00"),
        frequency="monthly",
        generation_day=1,
        due_day=10,
        billing_period_timing="current_period",
        next_generation_date=date(2026, 4, 1),
        scope_type="all_flats",
        effective_from=date(2026, 4, 1),
        status="active",
    )
    charge_type = ChargeType(
        id=charge_type_id,
        tenant_id=tenant_id,
        society_id=society_id,
        name="Maintenance",
        status="active",
    )
    session = FakeSession(scalar_results=[rule, None, charge_type])
    payload = BillingRuleUpdate(**build_payload(charge_type_id, name="Monthly Maintenance Updated").model_dump())

    updated = update_billing_rule(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        billing_rule_id=rule.id,
        payload=payload,
        actor=actor,
    )

    assert updated.name == "Monthly Maintenance Updated"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_billing_rule_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    charge_type_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    rule = BillingRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        charge_type_id=charge_type_id,
        name="Monthly Maintenance",
        calculation_method="fixed",
        amount=Decimal("2500.00"),
        frequency="monthly",
        generation_day=1,
        due_day=10,
        billing_period_timing="current_period",
        next_generation_date=date(2026, 4, 1),
        scope_type="all_flats",
        effective_from=date(2026, 4, 1),
        status="active",
    )
    session = FakeSession(existing_rule=rule)

    updated = change_billing_rule_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        billing_rule_id=rule.id,
        status="inactive",
        actor=actor,
    )

    assert updated.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1


def test_billing_rule_schema_rejects_area_rule_without_area_basis() -> None:
    with pytest.raises(ValueError, match="Area basis is required"):
        build_payload(uuid.uuid4(), calculation_method="area_based", area_basis=None)


def test_billing_rule_schema_rejects_invalid_scope_shape() -> None:
    with pytest.raises(ValueError, match="Building scope requires only building"):
        build_payload(uuid.uuid4(), scope_type="building", building_id=None)
