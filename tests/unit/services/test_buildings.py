import uuid

import pytest

from app.models import Building, User
from app.schemas.building import BuildingCreate, BuildingUpdate
from app.services.buildings import (
    BuildingAlreadyExistsError,
    change_building_status,
    create_building,
    update_building,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_building: Building | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_building = existing_building
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_building

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


def test_create_building_adds_building_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    session = FakeSession()
    payload = BuildingCreate(name="Tower A", code="A")

    building = create_building(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert building.tenant_id == tenant_id
    assert building.society_id == society_id
    assert building.name == "Tower A"
    assert building.code == "A"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_building_rejects_duplicate_name_or_code() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    session = FakeSession(
        existing_building=Building(
            tenant_id=tenant_id,
            society_id=society_id,
            name="Tower A",
            code="A",
        )
    )
    payload = BuildingCreate(name="Tower A", code="A")

    with pytest.raises(BuildingAlreadyExistsError):
        create_building(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_update_building_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        name="Tower A",
        code="A",
        status="active",
    )
    session = FakeSession(scalar_results=[building, None])
    payload = BuildingUpdate(name="Tower Alpha", code="ALPHA")

    updated = update_building(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building.id,
        payload=payload,
        actor=actor,
    )

    assert updated.name == "Tower Alpha"
    assert updated.code == "ALPHA"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_building_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        name="Tower A",
        status="active",
    )
    session = FakeSession(existing_building=building)

    updated = change_building_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building.id,
        status="suspended",
        actor=actor,
    )

    assert updated.status == "suspended"
    assert session.committed is True
    assert len(session.added) == 1
