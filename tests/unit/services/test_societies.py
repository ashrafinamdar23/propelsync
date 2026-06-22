import uuid

import pytest

from app.models import Society, User
from app.schemas.society import SocietyCreate, SocietyUpdate
from app.services.societies import (
    SocietyAlreadyExistsError,
    change_society_status,
    create_society,
    update_society,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_society: Society | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_society = existing_society
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_society

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


def build_context(tenant_id: uuid.UUID, actor: User) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant=None,  # type: ignore[arg-type]
        user=actor,
    )


def build_actor() -> User:
    return User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@example.com",
        full_name="Tenant Admin",
    )


def test_create_society_adds_society_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    session = FakeSession()
    payload = SocietyCreate(name="Green Heights CHS", registration_number="REG-001")

    society = create_society(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        payload=payload,
        actor=actor,
    )

    assert society.tenant_id == tenant_id
    assert society.name == "Green Heights CHS"
    assert society.registration_number == "REG-001"
    assert society.currency == "INR"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_society_rejects_duplicate_name_or_registration_number() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(existing_society=Society(name="Green Heights CHS", tenant_id=context.tenant_id))
    payload = SocietyCreate(name="Green Heights CHS")

    with pytest.raises(SocietyAlreadyExistsError):
        create_society(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            payload=payload,
            actor=actor,
        )


def test_update_society_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Old Name",
        status="active",
    )
    session = FakeSession(scalar_results=[society, None])
    payload = SocietyUpdate(
        name="Green Heights CHS",
        registration_number="REG-001",
        city="Mumbai",
        state="Maharashtra",
        currency="inr",
    )

    updated = update_society(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society.id,
        payload=payload,
        actor=actor,
    )

    assert updated.name == "Green Heights CHS"
    assert updated.city == "Mumbai"
    assert updated.currency == "INR"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_society_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Green Heights CHS",
        status="active",
    )
    session = FakeSession(existing_society=society)

    updated = change_society_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society.id,
        status="suspended",
        actor=actor,
    )

    assert updated.status == "suspended"
    assert session.committed is True
    assert len(session.added) == 1
