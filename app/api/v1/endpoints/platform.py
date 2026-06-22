from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_platform_superuser
from app.db.deps import get_db
from app.models import Tenant, User
from app.schemas.tenant import TenantCreate, TenantRead, TenantUpdate
from app.services.tenants import (
    TenantAlreadyExistsError,
    TenantNotFoundError,
    change_tenant_status,
    create_tenant,
    list_tenants,
    update_tenant,
)


router = APIRouter(prefix="/platform")


def tenant_to_read(tenant: Tenant) -> TenantRead:
    return TenantRead(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        subscription_plan=tenant.subscription_plan,
        billing_email=tenant.billing_email,
        phone=tenant.phone,
        timezone=tenant.timezone,
        locale=tenant.locale,
        currency=tenant.currency,
        metadata=tenant.metadata_,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.get("/tenants", response_model=list[TenantRead])
def read_tenants(
    _: Annotated[User, Depends(require_platform_superuser)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TenantRead]:
    return [tenant_to_read(tenant) for tenant in list_tenants(db)]


@router.post("/tenants", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def create_platform_tenant(
    payload: TenantCreate,
    current_user: Annotated[User, Depends(require_platform_superuser)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantRead:
    try:
        tenant = create_tenant(db, payload=payload, actor=current_user)
    except TenantAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant slug already exists.",
        ) from exc
    return tenant_to_read(tenant)


@router.patch("/tenants/{tenant_id}", response_model=TenantRead)
def update_platform_tenant(
    tenant_id: uuid.UUID,
    payload: TenantUpdate,
    current_user: Annotated[User, Depends(require_platform_superuser)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantRead:
    try:
        tenant = update_tenant(db, tenant_id=tenant_id, payload=payload, actor=current_user)
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.") from exc
    return tenant_to_read(tenant)


@router.post("/tenants/{tenant_id}/suspend", response_model=TenantRead)
def suspend_platform_tenant(
    tenant_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_platform_superuser)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantRead:
    try:
        tenant = change_tenant_status(db, tenant_id=tenant_id, status="suspended", actor=current_user)
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.") from exc
    return tenant_to_read(tenant)


@router.post("/tenants/{tenant_id}/activate", response_model=TenantRead)
def activate_platform_tenant(
    tenant_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_platform_superuser)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantRead:
    try:
        tenant = change_tenant_status(db, tenant_id=tenant_id, status="active", actor=current_user)
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.") from exc
    return tenant_to_read(tenant)
