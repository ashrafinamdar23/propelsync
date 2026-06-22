import uuid

import pytest
from fastapi import HTTPException

from app.models import Society, SocietyMembership, TenantMembership, User
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context, require_tenant_admin_context


class FakeSession:
    def __init__(
        self,
        membership: TenantMembership | None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.membership = membership
        self.scalar_results = scalar_results

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.membership


def build_context(user: User) -> TenantContext:
    return TenantContext(
        tenant_id=uuid.uuid4(),
        tenant=None,  # type: ignore[arg-type]
        user=user,
    )


def test_require_tenant_admin_context_allows_platform_superuser() -> None:
    user = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="platform@example.com",
        full_name="Platform Admin",
        is_platform_superuser=True,
    )
    context = build_context(user)

    resolved = require_tenant_admin_context(context, FakeSession(None))  # type: ignore[arg-type]

    assert resolved == context


def test_require_tenant_admin_context_allows_active_tenant_admin() -> None:
    user = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="tenant@example.com",
        full_name="Tenant Admin",
        is_platform_superuser=False,
    )
    context = build_context(user)
    membership = TenantMembership(
        tenant_id=context.tenant_id,
        user_id=user.id,
        role="tenant_admin",
        status="active",
    )

    resolved = require_tenant_admin_context(
        context,
        FakeSession(membership),  # type: ignore[arg-type]
    )

    assert resolved == context


def test_require_tenant_admin_context_rejects_user_without_membership() -> None:
    user = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="user@example.com",
        full_name="Normal User",
        is_platform_superuser=False,
    )
    context = build_context(user)

    with pytest.raises(HTTPException) as exc_info:
        require_tenant_admin_context(context, FakeSession(None))  # type: ignore[arg-type]

    assert exc_info.value.status_code == 403


def test_require_society_admin_context_allows_active_society_admin() -> None:
    user = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="society@example.com",
        full_name="Society Admin",
        is_platform_superuser=False,
    )
    context = build_context(user)
    society_id = uuid.uuid4()
    society = Society(id=society_id, tenant_id=context.tenant_id, name="Green Heights")
    membership = SocietyMembership(
        tenant_id=context.tenant_id,
        society_id=society_id,
        user_id=user.id,
        role="society_admin",
        status="active",
    )

    resolved = require_society_admin_context(
        society_id,
        context,
        FakeSession(None, scalar_results=[society, None, membership]),  # type: ignore[arg-type]
    )

    assert resolved == context


def test_require_society_admin_context_rejects_user_without_admin_membership() -> None:
    user = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="user@example.com",
        full_name="Normal User",
        is_platform_superuser=False,
    )
    context = build_context(user)
    society_id = uuid.uuid4()
    society = Society(id=society_id, tenant_id=context.tenant_id, name="Green Heights")

    with pytest.raises(HTTPException) as exc_info:
        require_society_admin_context(
            society_id,
            context,
            FakeSession(None, scalar_results=[society, None, None]),  # type: ignore[arg-type]
        )

    assert exc_info.value.status_code == 403
