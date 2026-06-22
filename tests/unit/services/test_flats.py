import uuid
from decimal import Decimal

import pytest

from app.models import Building, Flat, User, Wing
from app.schemas.flat import FlatCreate, FlatUpdate
from app.services.flats import (
    FlatAlreadyExistsError,
    FlatBuildingNotFoundError,
    FlatWingNotFoundError,
    change_flat_status,
    create_flat,
    update_flat,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_flat: Flat | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_flat = existing_flat
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_flat

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


def test_create_flat_adds_flat_without_wing_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(id=building_id, tenant_id=tenant_id, society_id=society_id, name="Tower A")
    session = FakeSession(scalar_results=[building, None])
    payload = FlatCreate(
        flat_number="101",
        floor_number=1,
        carpet_area_sqft=Decimal("725.50"),
        built_up_area_sqft=Decimal("900.00"),
        parking_count=1,
    )

    flat = create_flat(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
        actor=actor,
    )

    assert flat.tenant_id == tenant_id
    assert flat.society_id == society_id
    assert flat.building_id == building_id
    assert flat.wing_id is None
    assert flat.flat_number == "101"
    assert flat.carpet_area_sqft == Decimal("725.50")
    assert flat.parking_count == 1
    assert session.committed is True
    assert len(session.added) == 2


def test_create_flat_adds_flat_with_wing() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    wing_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(id=building_id, tenant_id=tenant_id, society_id=society_id, name="Tower A")
    wing = Wing(
        id=wing_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        name="A Wing",
    )
    session = FakeSession(scalar_results=[building, wing, None])
    payload = FlatCreate(wing_id=wing_id, flat_number="A-101")

    flat = create_flat(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
        actor=actor,
    )

    assert flat.wing_id == wing_id
    assert flat.flat_number == "A-101"


def test_create_flat_rejects_missing_building() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(scalar_results=[None])
    payload = FlatCreate(flat_number="101")

    with pytest.raises(FlatBuildingNotFoundError):
        create_flat(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            building_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_flat_rejects_invalid_wing() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(id=building_id, tenant_id=tenant_id, society_id=society_id, name="Tower A")
    session = FakeSession(scalar_results=[building, None])
    payload = FlatCreate(wing_id=uuid.uuid4(), flat_number="A-101")

    with pytest.raises(FlatWingNotFoundError):
        create_flat(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            payload=payload,
            actor=actor,
        )


def test_create_flat_rejects_duplicate_number_in_scope() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    building = Building(id=building_id, tenant_id=tenant_id, society_id=society_id, name="Tower A")
    existing_flat = Flat(
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
    )
    session = FakeSession(scalar_results=[building, existing_flat])
    payload = FlatCreate(flat_number="101")

    with pytest.raises(FlatAlreadyExistsError):
        create_flat(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            payload=payload,
            actor=actor,
        )


def test_update_flat_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
        status="active",
    )
    session = FakeSession(scalar_results=[flat, None])
    payload = FlatUpdate(flat_number="102", floor_number=1, parking_count=2)

    updated = update_flat(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat.id,
        payload=payload,
        actor=actor,
    )

    assert updated.flat_number == "102"
    assert updated.floor_number == 1
    assert updated.parking_count == 2
    assert session.committed is True
    assert len(session.added) == 1


def test_change_flat_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
        status="active",
    )
    session = FakeSession(existing_flat=flat)

    updated = change_flat_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat.id,
        status="inactive",
        actor=actor,
    )

    assert updated.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1
