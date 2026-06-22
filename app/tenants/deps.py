import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.deps import get_db
from app.models import Society, SocietyMembership, Tenant, TenantMembership, User
from app.tenants.context import TenantContext


TENANT_HEADER_NAME = "X-Tenant-Id"


def get_tenant_context(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    tenant_id_header: Annotated[str | None, Header(alias=TENANT_HEADER_NAME)] = None,
) -> TenantContext:
    if not tenant_id_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{TENANT_HEADER_NAME} header is required.",
        )

    try:
        tenant_id = uuid.UUID(tenant_id_header)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{TENANT_HEADER_NAME} must be a valid UUID.",
        ) from exc

    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None or tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    return TenantContext(
        tenant_id=tenant.id,
        tenant=tenant,
        user=current_user,
    )


def require_tenant_admin_context(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantContext:
    if tenant_context.user.is_platform_superuser:
        return tenant_context

    membership = db.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_context.tenant_id,
            TenantMembership.user_id == tenant_context.user.id,
            TenantMembership.role == "tenant_admin",
            TenantMembership.status == "active",
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access is required.",
        )

    return tenant_context


def require_society_admin_context(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantContext:
    society = db.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
            Society.status == "active",
        )
    )
    if society is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Society not found.",
        )

    if tenant_context.user.is_platform_superuser:
        return tenant_context

    tenant_membership = db.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_context.tenant_id,
            TenantMembership.user_id == tenant_context.user.id,
            TenantMembership.role == "tenant_admin",
            TenantMembership.status == "active",
        )
    )
    if tenant_membership is not None:
        return tenant_context

    society_membership = db.scalar(
        select(SocietyMembership).where(
            SocietyMembership.tenant_id == tenant_context.tenant_id,
            SocietyMembership.society_id == society_id,
            SocietyMembership.user_id == tenant_context.user.id,
            SocietyMembership.role == "society_admin",
            SocietyMembership.status == "active",
        )
    )
    if society_membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Society admin access is required.",
        )

    return tenant_context
