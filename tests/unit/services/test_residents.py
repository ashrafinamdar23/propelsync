import uuid
from datetime import date

import pytest

from app.models import Flat, Owner, Resident, User
from app.schemas.resident import ResidentCreate, ResidentUpdate
from app.services.residents import (
    ResidentAlreadyExistsError,
    ResidentFlatNotFoundError,
    ResidentInvalidDateError,
    ResidentOwnerNotFoundError,
    ResidentUserNotFoundError,
    activate_resident,
    create_resident,
    move_out_resident,
    update_resident,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_resident: Resident | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_resident = existing_resident
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_resident

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


def test_create_resident_adds_offline_tenant_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(
        id=flat_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
    )
    session = FakeSession(scalar_results=[flat])
    payload = ResidentCreate(
        resident_type="tenant",
        full_name="Neha Rao",
        mobile_number="+919812345678",
        move_in_date=date(2026, 6, 1),
    )

    resident = create_resident(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        payload=payload,
        actor=actor,
    )

    assert resident.tenant_id == tenant_id
    assert resident.society_id == society_id
    assert resident.flat_id == flat_id
    assert resident.owner_id is None
    assert resident.user_id is None
    assert resident.resident_type == "tenant"
    assert resident.status == "active"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_resident_adds_owner_occupier_linked_to_owner_and_user() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    user_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(
        id=flat_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
    )
    owner = Owner(id=owner_id, tenant_id=tenant_id, society_id=society_id, full_name="Asha")
    user = User(id=user_id, keycloak_subject="subject-2", email="owner@example.com", full_name="Asha")
    session = FakeSession(scalar_results=[flat, owner, user, None])
    payload = ResidentCreate(
        owner_id=owner_id,
        user_id=user_id,
        resident_type="owner_occupier",
        full_name="Asha Mehta",
        move_in_date=date(2026, 4, 1),
    )

    resident = create_resident(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        payload=payload,
        actor=actor,
    )

    assert resident.owner_id == owner_id
    assert resident.user_id == user_id
    assert resident.resident_type == "owner_occupier"


def test_create_resident_rejects_missing_flat() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(scalar_results=[None])
    payload = ResidentCreate(
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 6, 1),
    )

    with pytest.raises(ResidentFlatNotFoundError):
        create_resident(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            building_id=uuid.uuid4(),
            flat_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_resident_rejects_missing_owner() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(
        id=flat_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
    )
    session = FakeSession(scalar_results=[flat, None])
    payload = ResidentCreate(
        owner_id=uuid.uuid4(),
        resident_type="owner_occupier",
        full_name="Asha Mehta",
        move_in_date=date(2026, 4, 1),
    )

    with pytest.raises(ResidentOwnerNotFoundError):
        create_resident(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=actor,
        )


def test_create_resident_rejects_missing_user() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(
        id=flat_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
    )
    session = FakeSession(scalar_results=[flat, None])
    payload = ResidentCreate(
        user_id=uuid.uuid4(),
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 6, 1),
    )

    with pytest.raises(ResidentUserNotFoundError):
        create_resident(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=actor,
        )


def test_create_resident_rejects_duplicate_current_user_for_flat() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    user_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(
        id=flat_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
    )
    user = User(id=user_id, keycloak_subject="subject-2", email="resident@example.com", full_name="Neha")
    existing = Resident(
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        user_id=user_id,
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 6, 1),
    )
    session = FakeSession(scalar_results=[flat, user, existing])
    payload = ResidentCreate(
        user_id=user_id,
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 6, 1),
    )

    with pytest.raises(ResidentAlreadyExistsError):
        create_resident(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=actor,
        )


def test_update_resident_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    resident = Resident(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 6, 1),
        status="active",
    )
    session = FakeSession(scalar_results=[resident])
    payload = ResidentUpdate(
        resident_type="tenant",
        full_name="Neha Shah",
        email="neha@example.com",
        mobile_number="+919812345678",
        move_in_date=date(2026, 6, 1),
    )

    updated = update_resident(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        resident_id=resident.id,
        payload=payload,
        actor=actor,
    )

    assert updated.full_name == "Neha Shah"
    assert updated.email == "neha@example.com"
    assert updated.status == "active"
    assert session.committed is True
    assert len(session.added) == 1


def test_move_out_resident_sets_move_out_date_and_inactive() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    resident = Resident(
        id=uuid.uuid4(),
        tenant_id=context.tenant_id,
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 6, 1),
        status="active",
    )
    session = FakeSession(existing_resident=resident)

    moved_out = move_out_resident(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=resident.society_id,
        building_id=uuid.uuid4(),
        flat_id=resident.flat_id,
        resident_id=resident.id,
        move_out_date=date(2027, 3, 31),
        actor=actor,
    )

    assert moved_out.move_out_date == date(2027, 3, 31)
    assert moved_out.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1


def test_move_out_resident_rejects_invalid_move_out_date() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    resident = Resident(
        id=uuid.uuid4(),
        tenant_id=context.tenant_id,
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 6, 1),
    )
    session = FakeSession(existing_resident=resident)

    with pytest.raises(ResidentInvalidDateError):
        move_out_resident(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=resident.society_id,
            building_id=uuid.uuid4(),
            flat_id=resident.flat_id,
            resident_id=resident.id,
            move_out_date=date(2026, 5, 31),
            actor=actor,
        )


def test_activate_resident_reopens_record() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    resident = Resident(
        id=uuid.uuid4(),
        tenant_id=context.tenant_id,
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 6, 1),
        move_out_date=date(2027, 3, 31),
        status="inactive",
    )
    session = FakeSession(scalar_results=[resident])

    activated = activate_resident(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=resident.society_id,
        building_id=uuid.uuid4(),
        flat_id=resident.flat_id,
        resident_id=resident.id,
        actor=actor,
    )

    assert activated.move_out_date is None
    assert activated.status == "active"
    assert session.committed is True
    assert len(session.added) == 1
