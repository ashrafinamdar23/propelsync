import uuid

import pytest

from app.models import Owner, Society, User
from app.schemas.owner import OwnerCreate, OwnerUpdate
from app.services.owners import (
    OwnerAlreadyExistsError,
    OwnerSocietyNotFoundError,
    OwnerUserNotFoundError,
    change_owner_status,
    create_owner,
    update_owner,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_owner: Owner | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_owner = existing_owner
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_owner

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


def test_create_owner_adds_offline_owner_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    session = FakeSession(scalar_results=[society])
    payload = OwnerCreate(
        full_name="Asha Mehta",
        email="asha@example.com",
        mobile_number="+919876543210",
    )

    owner = create_owner(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert owner.tenant_id == tenant_id
    assert owner.society_id == society_id
    assert owner.user_id is None
    assert owner.owner_type == "individual"
    assert owner.full_name == "Asha Mehta"
    assert owner.email == "asha@example.com"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_owner_adds_owner_linked_to_user() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    user_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    user = User(id=user_id, keycloak_subject="subject-2", email="owner@example.com", full_name="Owner")
    session = FakeSession(scalar_results=[society, user, None])
    payload = OwnerCreate(user_id=user_id, full_name="Rahul Shah")

    owner = create_owner(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert owner.user_id == user_id
    assert owner.full_name == "Rahul Shah"


def test_create_owner_rejects_missing_society() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(scalar_results=[None])
    payload = OwnerCreate(full_name="Asha Mehta")

    with pytest.raises(OwnerSocietyNotFoundError):
        create_owner(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_owner_rejects_missing_user() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    session = FakeSession(scalar_results=[society, None])
    payload = OwnerCreate(user_id=uuid.uuid4(), full_name="Asha Mehta")

    with pytest.raises(OwnerUserNotFoundError):
        create_owner(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_create_owner_rejects_duplicate_user_link() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    user_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    user = User(id=user_id, keycloak_subject="subject-2", email="owner@example.com", full_name="Owner")
    existing_owner = Owner(
        tenant_id=tenant_id,
        society_id=society_id,
        user_id=user_id,
        full_name="Existing Owner",
    )
    session = FakeSession(scalar_results=[society, user, existing_owner])
    payload = OwnerCreate(user_id=user_id, full_name="Asha Mehta")

    with pytest.raises(OwnerAlreadyExistsError):
        create_owner(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_update_owner_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    owner = Owner(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        full_name="Asha Mehta",
        status="active",
    )
    session = FakeSession(scalar_results=[owner])
    payload = OwnerUpdate(
        owner_type="individual",
        full_name="Asha Shah",
        email="asha.shah@example.com",
        mobile_number="+919876543210",
    )

    updated = update_owner(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        owner_id=owner.id,
        payload=payload,
        actor=actor,
    )

    assert updated.full_name == "Asha Shah"
    assert updated.email == "asha.shah@example.com"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_owner_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    owner = Owner(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        full_name="Asha Mehta",
        status="active",
    )
    session = FakeSession(existing_owner=owner)

    updated = change_owner_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        owner_id=owner.id,
        status="inactive",
        actor=actor,
    )

    assert updated.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1
