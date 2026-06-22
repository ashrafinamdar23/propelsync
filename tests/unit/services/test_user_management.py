from datetime import UTC, datetime
import uuid

import pytest

from app.models import Society, SocietyMembership, Tenant, TenantMembership, User
from app.schemas.user_management import ManagedUserCreate, SocietyRoleAssignment
from app.services.user_management import (
    SocietyAccessInvalidError,
    UserManagementPermissionError,
    UserRoleInvalidError,
    change_managed_user_membership_status,
    ensure_actor_can_assign_roles,
    ensure_society_membership,
    ensure_tenant_membership,
    validate_roles,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        *,
        scalar_results: list[object | None] | None = None,
        scalars_results: list[list[object]] | None = None,
        execute_results: list[list[tuple[object, ...]]] | None = None,
    ) -> None:
        self.scalar_results = scalar_results or []
        self.scalars_results = scalars_results or []
        self.execute_results = execute_results or []
        self.added: list[object] = []
        self.committed = False
        self.refreshed: object | None = None

    def scalar(self, *_: object) -> object | None:
        return self.scalar_results.pop(0) if self.scalar_results else None

    def scalars(self, *_: object) -> list[object]:
        return self.scalars_results.pop(0) if self.scalars_results else []

    def execute(self, *_: object) -> list[tuple[object, ...]]:
        return self.execute_results.pop(0) if self.execute_results else []

    def add(self, instance: object) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        for instance in self.added:
            if getattr(instance, "id", None) is None:
                instance.id = uuid.uuid4()

    def commit(self) -> None:
        self.committed = True

    def refresh(self, instance: object) -> None:
        self.refreshed = instance


def build_user(*, platform: bool = False) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid.uuid4(),
        keycloak_subject=str(uuid.uuid4()),
        email="admin@example.com",
        full_name="Admin User",
        status="active",
        is_platform_superuser=platform,
        created_at=now,
        updated_at=now,
    )


def build_context(tenant_id: uuid.UUID, user: User) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant=Tenant(id=tenant_id, name="Dream Savera", slug="dream-savera"),
        user=user,
    )


def test_validate_roles_rejects_unknown_roles() -> None:
    payload = ManagedUserCreate(
        full_name="Test User",
        email="test@example.com",
        temporary_password="Password123",
        tenant_roles=["owner"],
        society_roles=[SocietyRoleAssignment(society_id=uuid.uuid4(), role="manager")],
    )

    with pytest.raises(UserRoleInvalidError):
        validate_roles(payload)


def test_society_admin_cannot_assign_tenant_role() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_user()
    context = build_context(tenant_id, actor)
    actor_membership = SocietyMembership(
        tenant_id=tenant_id,
        society_id=society_id,
        user_id=actor.id,
        role="society_admin",
        status="active",
    )
    session = FakeSession(scalar_results=[None], scalars_results=[[actor_membership]])
    payload = ManagedUserCreate(
        full_name="Tenant Admin",
        email="tenant-admin@example.com",
        temporary_password="Password123",
        tenant_roles=["tenant_admin"],
    )

    with pytest.raises(UserManagementPermissionError):
        ensure_actor_can_assign_roles(session, tenant_context=context, payload=payload)  # type: ignore[arg-type]


def test_society_admin_can_assign_role_in_own_society() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_user()
    context = build_context(tenant_id, actor)
    actor_membership = SocietyMembership(
        tenant_id=tenant_id,
        society_id=society_id,
        user_id=actor.id,
        role="society_admin",
        status="active",
    )
    session = FakeSession(scalar_results=[None], scalars_results=[[actor_membership]])
    payload = ManagedUserCreate(
        full_name="Accountant",
        email="accountant@example.com",
        temporary_password="Password123",
        society_roles=[SocietyRoleAssignment(society_id=society_id, role="accountant")],
    )

    scope = ensure_actor_can_assign_roles(session, tenant_context=context, payload=payload)  # type: ignore[arg-type]

    assert scope == {society_id}


def test_ensure_tenant_membership_reactivates_existing_membership() -> None:
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership = TenantMembership(
        tenant_id=tenant_id,
        user_id=user_id,
        role="tenant_admin",
        status="suspended",
    )
    session = FakeSession(scalar_results=[membership])

    result = ensure_tenant_membership(
        session,  # type: ignore[arg-type]
        tenant_id=tenant_id,
        user_id=user_id,
        role="tenant_admin",
    )

    assert result is membership
    assert result.status == "active"
    assert session.added == []


def test_ensure_society_membership_rejects_society_outside_tenant() -> None:
    session = FakeSession(scalar_results=[None])

    with pytest.raises(SocietyAccessInvalidError):
        ensure_society_membership(
            session,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            society_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="society_admin",
        )


def test_suspend_managed_user_updates_only_visible_scope() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_user()
    target = build_user()
    context = build_context(tenant_id, actor)
    actor_membership = SocietyMembership(
        tenant_id=tenant_id,
        society_id=society_id,
        user_id=actor.id,
        role="society_admin",
        status="active",
    )
    target_membership = SocietyMembership(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        user_id=target.id,
        role="treasurer",
        status="active",
    )
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera", status="active")
    session = FakeSession(
        scalar_results=[None, target],
        scalars_results=[[actor_membership]],
        execute_results=[[(target_membership, society)]],
    )

    result = change_managed_user_membership_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        user_id=target.id,
        status="suspended",
        actor=actor,
    )

    assert target_membership.status == "suspended"
    assert result.society_memberships[0].status == "suspended"
    assert session.committed is True
    assert len(session.added) == 1
