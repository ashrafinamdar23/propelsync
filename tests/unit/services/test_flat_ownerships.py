import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.models import Flat, FlatOwnership, Owner, User
from app.schemas.flat_ownership import FlatOwnershipCreate, FlatOwnershipUpdate
from app.services.flat_ownerships import (
    FlatOwnershipAlreadyExistsError,
    FlatOwnershipCurrentPrimaryExistsError,
    FlatOwnershipFlatNotFoundError,
    FlatOwnershipInvalidDateError,
    activate_flat_ownership,
    close_flat_ownership,
    create_flat_ownership,
    update_flat_ownership,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_ownership: FlatOwnership | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_ownership = existing_ownership
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_ownership

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


def test_create_flat_ownership_adds_primary_owner_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(id=flat_id, tenant_id=tenant_id, society_id=society_id, building_id=building_id, flat_number="101")
    owner = Owner(id=owner_id, tenant_id=tenant_id, society_id=society_id, full_name="Asha Mehta")
    session = FakeSession(scalar_results=[flat, owner, None, None])
    payload = FlatOwnershipCreate(
        owner_id=owner_id,
        ownership_type="primary_owner",
        ownership_percentage=Decimal("100.00"),
        effective_from=date(2026, 4, 1),
    )

    ownership = create_flat_ownership(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        payload=payload,
        actor=actor,
    )

    assert ownership.tenant_id == tenant_id
    assert ownership.society_id == society_id
    assert ownership.flat_id == flat_id
    assert ownership.owner_id == owner_id
    assert ownership.ownership_type == "primary_owner"
    assert ownership.effective_to is None
    assert session.committed is True
    assert len(session.added) == 2


def test_create_flat_ownership_rejects_missing_flat() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(scalar_results=[None])
    payload = FlatOwnershipCreate(
        owner_id=uuid.uuid4(),
        ownership_type="primary_owner",
        effective_from=date(2026, 4, 1),
    )

    with pytest.raises(FlatOwnershipFlatNotFoundError):
        create_flat_ownership(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            building_id=uuid.uuid4(),
            flat_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_flat_ownership_rejects_duplicate_owner_start() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(id=flat_id, tenant_id=tenant_id, society_id=society_id, building_id=building_id, flat_number="101")
    owner = Owner(id=owner_id, tenant_id=tenant_id, society_id=society_id, full_name="Asha Mehta")
    existing = FlatOwnership(
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        owner_id=owner_id,
        ownership_type="primary_owner",
        effective_from=date(2026, 4, 1),
    )
    session = FakeSession(scalar_results=[flat, owner, existing])
    payload = FlatOwnershipCreate(
        owner_id=owner_id,
        ownership_type="primary_owner",
        effective_from=date(2026, 4, 1),
    )

    with pytest.raises(FlatOwnershipAlreadyExistsError):
        create_flat_ownership(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=actor,
        )


def test_create_flat_ownership_rejects_second_current_primary_owner() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(id=flat_id, tenant_id=tenant_id, society_id=society_id, building_id=building_id, flat_number="101")
    owner = Owner(id=owner_id, tenant_id=tenant_id, society_id=society_id, full_name="Asha Mehta")
    existing_primary = FlatOwnership(
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        owner_id=uuid.uuid4(),
        ownership_type="primary_owner",
        effective_from=date(2026, 1, 1),
    )
    session = FakeSession(scalar_results=[flat, owner, None, existing_primary])
    payload = FlatOwnershipCreate(
        owner_id=owner_id,
        ownership_type="primary_owner",
        effective_from=date(2026, 4, 1),
    )

    with pytest.raises(FlatOwnershipCurrentPrimaryExistsError):
        create_flat_ownership(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=actor,
        )


def test_update_flat_ownership_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    ownership = FlatOwnership(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        owner_id=owner_id,
        ownership_type="co_owner",
        effective_from=date(2026, 4, 1),
        status="active",
    )
    owner = Owner(id=owner_id, tenant_id=tenant_id, society_id=society_id, full_name="Asha Mehta")
    session = FakeSession(scalar_results=[ownership, owner, None])
    payload = FlatOwnershipUpdate(
        owner_id=owner_id,
        ownership_type="co_owner",
        ownership_percentage=Decimal("50.00"),
        effective_from=date(2026, 4, 1),
        effective_to=date(2027, 3, 31),
    )

    updated = update_flat_ownership(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        ownership_id=ownership.id,
        payload=payload,
        actor=actor,
    )

    assert updated.ownership_percentage == Decimal("50.00")
    assert updated.effective_to == date(2027, 3, 31)
    assert session.committed is True
    assert len(session.added) == 1


def test_close_flat_ownership_sets_effective_to_and_inactive() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    ownership = FlatOwnership(
        id=uuid.uuid4(),
        tenant_id=context.tenant_id,
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        ownership_type="primary_owner",
        effective_from=date(2026, 4, 1),
        status="active",
    )
    session = FakeSession(existing_ownership=ownership)

    closed = close_flat_ownership(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=ownership.society_id,
        building_id=uuid.uuid4(),
        flat_id=ownership.flat_id,
        ownership_id=ownership.id,
        effective_to=date(2027, 3, 31),
        actor=actor,
    )

    assert closed.effective_to == date(2027, 3, 31)
    assert closed.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1


def test_close_flat_ownership_rejects_invalid_effective_to() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    ownership = FlatOwnership(
        id=uuid.uuid4(),
        tenant_id=context.tenant_id,
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        ownership_type="primary_owner",
        effective_from=date(2026, 4, 1),
    )
    session = FakeSession(existing_ownership=ownership)

    with pytest.raises(FlatOwnershipInvalidDateError):
        close_flat_ownership(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=ownership.society_id,
            building_id=uuid.uuid4(),
            flat_id=ownership.flat_id,
            ownership_id=ownership.id,
            effective_to=date(2026, 3, 31),
            actor=actor,
        )


def test_activate_flat_ownership_reopens_record() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    ownership = FlatOwnership(
        id=uuid.uuid4(),
        tenant_id=context.tenant_id,
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        ownership_type="co_owner",
        effective_from=date(2026, 4, 1),
        effective_to=date(2027, 3, 31),
        status="inactive",
    )
    session = FakeSession(scalar_results=[ownership])

    activated = activate_flat_ownership(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=ownership.society_id,
        building_id=uuid.uuid4(),
        flat_id=ownership.flat_id,
        ownership_id=ownership.id,
        actor=actor,
    )

    assert activated.effective_to is None
    assert activated.status == "active"
    assert session.committed is True
    assert len(session.added) == 1
