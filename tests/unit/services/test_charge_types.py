import uuid

import pytest

from app.models import ChargeType, ChartOfAccount, Society, User
from app.schemas.charge_type import ChargeTypeCreate, ChargeTypeUpdate
from app.services.charge_types import (
    ChargeTypeAlreadyExistsError,
    change_charge_type_status,
    create_charge_type,
    update_charge_type,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_charge_type: ChargeType | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_charge_type = existing_charge_type
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_charge_type

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


def test_create_charge_type_adds_charge_type_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    revenue_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4000",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
        status="active",
    )
    session = FakeSession(scalar_results=[society, None, None, revenue_account])
    payload = ChargeTypeCreate(
        name="Maintenance",
        code="MAINT",
        description="Monthly maintenance",
        revenue_account_id=revenue_account.id,
    )

    charge_type = create_charge_type(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert charge_type.tenant_id == tenant_id
    assert charge_type.society_id == society_id
    assert charge_type.name == "Maintenance"
    assert charge_type.code == "MAINT"
    assert charge_type.revenue_account_id == revenue_account.id
    assert session.committed is True
    assert len(session.added) == 2


def test_create_charge_type_rejects_duplicate_name() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    existing = ChargeType(
        tenant_id=tenant_id,
        society_id=society_id,
        name="Maintenance",
        code="MAINT",
        revenue_account_id=uuid.uuid4(),
    )
    session = FakeSession(scalar_results=[society, existing])
    payload = ChargeTypeCreate(
        name="Maintenance",
        code="OTHER",
        revenue_account_id=uuid.uuid4(),
    )

    with pytest.raises(ChargeTypeAlreadyExistsError):
        create_charge_type(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_update_charge_type_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    charge_type = ChargeType(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        name="Maintenance",
        code="MAINT",
        revenue_account_id=uuid.uuid4(),
        status="active",
    )
    revenue_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4010",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
        status="active",
    )
    session = FakeSession(scalar_results=[charge_type, None, None, revenue_account])
    payload = ChargeTypeUpdate(
        name="Maintenance Charges",
        code="MAINT",
        description="Monthly charges",
        revenue_account_id=revenue_account.id,
    )

    updated = update_charge_type(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        charge_type_id=charge_type.id,
        payload=payload,
        actor=actor,
    )

    assert updated.name == "Maintenance Charges"
    assert updated.description == "Monthly charges"
    assert updated.revenue_account_id == revenue_account.id
    assert session.committed is True
    assert len(session.added) == 1


def test_change_charge_type_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    charge_type = ChargeType(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        name="Maintenance",
        revenue_account_id=uuid.uuid4(),
        status="active",
    )
    session = FakeSession(existing_charge_type=charge_type)

    updated = change_charge_type_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        charge_type_id=charge_type.id,
        status="inactive",
        actor=actor,
    )

    assert updated.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1
