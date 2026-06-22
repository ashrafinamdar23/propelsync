from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Society, SocietyMembership, Tenant, TenantMembership, User
from app.schemas.access import AccessSociety, AccessTenant, MyAccessRead


def get_my_access(session: Session, user: User) -> MyAccessRead:
    tenant_roles: dict[str, set[str]] = defaultdict(set)
    society_roles: dict[str, set[str]] = defaultdict(set)
    tenants_by_id: dict[str, Tenant] = {}
    societies_by_id: dict[str, Society] = {}

    is_platform_superuser = bool(user.is_platform_superuser)

    if is_platform_superuser:
        for tenant in session.scalars(select(Tenant).order_by(Tenant.name)):
            tenants_by_id[str(tenant.id)] = tenant
            tenant_roles[str(tenant.id)].add("platform_superuser")
    else:
        tenant_rows = session.execute(
            select(TenantMembership, Tenant)
            .join(Tenant, Tenant.id == TenantMembership.tenant_id)
            .where(
                TenantMembership.user_id == user.id,
                TenantMembership.status == "active",
                Tenant.status == "active",
            )
            .order_by(Tenant.name)
        )
        for membership, tenant in tenant_rows:
            tenants_by_id[str(tenant.id)] = tenant
            tenant_roles[str(tenant.id)].add(membership.role)

    society_rows = session.execute(
        select(SocietyMembership, Society, Tenant)
        .join(Society, Society.id == SocietyMembership.society_id)
        .join(Tenant, Tenant.id == SocietyMembership.tenant_id)
        .where(
            SocietyMembership.user_id == user.id,
            SocietyMembership.status == "active",
            Society.status == "active",
            Tenant.status == "active",
        )
        .order_by(Tenant.name, Society.name)
    )
    for membership, society, tenant in society_rows:
        tenants_by_id[str(tenant.id)] = tenant
        societies_by_id[str(society.id)] = society
        society_roles[str(society.id)].add(membership.role)

    tenants = [
        AccessTenant(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            status=tenant.status,
            roles=sorted(tenant_roles[str(tenant.id)]),
        )
        for tenant in sorted(tenants_by_id.values(), key=lambda item: item.name)
    ]
    societies = [
        AccessSociety(
            id=society.id,
            tenant_id=society.tenant_id,
            name=society.name,
            status=society.status,
            roles=sorted(society_roles[str(society.id)]),
        )
        for society in sorted(societies_by_id.values(), key=lambda item: item.name)
    ]

    return MyAccessRead(
        is_platform_superuser=is_platform_superuser,
        tenants=tenants,
        societies=societies,
    )
