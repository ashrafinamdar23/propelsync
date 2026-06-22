import uuid

import pytest

from app.models import Tenant, User
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.services.tenants import TenantAlreadyExistsError, change_tenant_status, create_tenant, update_tenant


class FakeScalarResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def __iter__(self):
        return iter(self.values)


class FakeSession:
    def __init__(self, existing_tenant: Tenant | None = None) -> None:
        self.existing_tenant = existing_tenant
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        return self.existing_tenant

    def get(self, *_: object) -> object | None:
        return self.existing_tenant

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


def test_create_tenant_adds_tenant_and_audit_log() -> None:
    session = FakeSession()
    actor = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@propelsync.local",
        full_name="Platform Admin",
        is_platform_superuser=True,
    )
    payload = TenantCreate(name="Green Heights", slug="green-heights")

    tenant = create_tenant(session, payload=payload, actor=actor)  # type: ignore[arg-type]

    assert tenant.name == "Green Heights"
    assert tenant.slug == "green-heights"
    assert tenant.currency == "INR"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_tenant_rejects_duplicate_slug() -> None:
    session = FakeSession(existing_tenant=Tenant(name="Green Heights", slug="green-heights"))
    actor = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@propelsync.local",
        full_name="Platform Admin",
        is_platform_superuser=True,
    )
    payload = TenantCreate(name="Green Heights", slug="green-heights")

    with pytest.raises(TenantAlreadyExistsError):
        create_tenant(session, payload=payload, actor=actor)  # type: ignore[arg-type]


def test_update_tenant_changes_editable_fields_and_adds_audit_log() -> None:
    tenant = Tenant(id=uuid.uuid4(), name="Old Name", slug="green-heights", status="active")
    session = FakeSession(existing_tenant=tenant)
    actor = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@propelsync.local",
        full_name="Platform Admin",
        is_platform_superuser=True,
    )
    payload = TenantUpdate(
        name="Green Heights",
        subscription_plan="enterprise",
        billing_email="treasurer@example.com",
        phone="+919876543210",
        timezone="Asia/Kolkata",
        locale="en-IN",
        currency="inr",
    )

    updated = update_tenant(
        session,  # type: ignore[arg-type]
        tenant_id=tenant.id,
        payload=payload,
        actor=actor,
    )

    assert updated.name == "Green Heights"
    assert updated.subscription_plan == "enterprise"
    assert updated.currency == "INR"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_tenant_status_updates_status_and_adds_audit_log() -> None:
    tenant = Tenant(id=uuid.uuid4(), name="Green Heights", slug="green-heights", status="active")
    session = FakeSession(existing_tenant=tenant)
    actor = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@propelsync.local",
        full_name="Platform Admin",
        is_platform_superuser=True,
    )

    updated = change_tenant_status(
        session,  # type: ignore[arg-type]
        tenant_id=tenant.id,
        status="suspended",
        actor=actor,
    )

    assert updated.status == "suspended"
    assert session.committed is True
    assert len(session.added) == 1
