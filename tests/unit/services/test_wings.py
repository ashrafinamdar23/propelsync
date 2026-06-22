import uuid

import pytest

from app.models import Building, User, Wing
from app.schemas.wing import WingCreate, WingUpdate
from app.services.wings import (
    WingAlreadyExistsError,
    WingBuildingNotFoundError,
    change_wing_status,
    create_wing,
    update_wing,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_wing: Wing | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_wing = existing_wing
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_wing

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


def test_create_wing_adds_wing_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(id=building_id, tenant_id=tenant_id, society_id=society_id, name="Tower A")
    session = FakeSession(scalar_results=[building, None])
    payload = WingCreate(name="A Wing", code="A")

    wing = create_wing(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
        actor=actor,
    )

    assert wing.tenant_id == tenant_id
    assert wing.society_id == society_id
    assert wing.building_id == building_id
    assert wing.name == "A Wing"
    assert wing.code == "A"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_wing_rejects_missing_building() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(scalar_results=[None])
    payload = WingCreate(name="A Wing", code="A")

    with pytest.raises(WingBuildingNotFoundError):
        create_wing(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            building_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_wing_rejects_duplicate_name_or_code() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(id=building_id, tenant_id=tenant_id, society_id=society_id, name="Tower A")
    existing_wing = Wing(
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        name="A Wing",
        code="A",
    )
    session = FakeSession(scalar_results=[building, existing_wing])
    payload = WingCreate(name="A Wing", code="A")

    with pytest.raises(WingAlreadyExistsError):
        create_wing(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            payload=payload,
            actor=actor,
        )


def test_update_wing_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    wing = Wing(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        name="A Wing",
        code="A",
        status="active",
    )
    session = FakeSession(scalar_results=[wing, None])
    payload = WingUpdate(name="Alpha Wing", code="ALPHA")

    updated = update_wing(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        wing_id=wing.id,
        payload=payload,
        actor=actor,
    )

    assert updated.name == "Alpha Wing"
    assert updated.code == "ALPHA"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_wing_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    wing = Wing(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        name="A Wing",
        status="active",
    )
    session = FakeSession(existing_wing=wing)

    updated = change_wing_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        wing_id=wing.id,
        status="suspended",
        actor=actor,
    )

    assert updated.status == "suspended"
    assert session.committed is True
    assert len(session.added) == 1
