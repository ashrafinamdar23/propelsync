import uuid

from app.models import Society, SocietyMembership, Tenant, TenantMembership, User
from app.services.access import get_my_access


class FakeSession:
    def __init__(
        self,
        tenants: list[Tenant] | None = None,
        tenant_rows: list[tuple[TenantMembership, Tenant]] | None = None,
        society_rows: list[tuple[SocietyMembership, Society, Tenant]] | None = None,
    ) -> None:
        self.tenants = tenants or []
        self.tenant_rows = tenant_rows or []
        self.society_rows = society_rows or []

    def scalars(self, *_: object) -> list[Tenant]:
        return self.tenants

    def execute(self, *_: object) -> list[tuple[object, ...]]:
        if self.tenant_rows:
            rows = self.tenant_rows
            self.tenant_rows = []
            return rows  # type: ignore[return-value]
        return self.society_rows  # type: ignore[return-value]


def test_get_my_access_returns_all_tenants_for_platform_superuser() -> None:
    tenant = Tenant(id=uuid.uuid4(), name="Green Heights", slug="green-heights", status="active")
    user = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="platform@example.com",
        full_name="Platform Admin",
        is_platform_superuser=True,
    )
    session = FakeSession(tenants=[tenant])

    access = get_my_access(session, user)  # type: ignore[arg-type]

    assert access.is_platform_superuser is True
    assert access.tenants[0].id == tenant.id
    assert access.tenants[0].roles == ["platform_superuser"]


def test_get_my_access_returns_tenant_and_society_memberships() -> None:
    tenant = Tenant(id=uuid.uuid4(), name="Green Heights", slug="green-heights", status="active")
    society = Society(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Green Heights CHS",
        status="active",
    )
    user = User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@example.com",
        full_name="Tenant Admin",
    )
    tenant_membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role="tenant_admin",
        status="active",
    )
    society_membership = SocietyMembership(
        tenant_id=tenant.id,
        society_id=society.id,
        user_id=user.id,
        role="society_admin",
        status="active",
    )
    session = FakeSession(
        tenant_rows=[(tenant_membership, tenant)],
        society_rows=[(society_membership, society, tenant)],
    )

    access = get_my_access(session, user)  # type: ignore[arg-type]

    assert access.is_platform_superuser is False
    assert access.tenants[0].id == tenant.id
    assert access.tenants[0].roles == ["tenant_admin"]
    assert access.societies[0].id == society.id
    assert access.societies[0].roles == ["society_admin"]
