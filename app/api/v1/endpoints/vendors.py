from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Vendor
from app.schemas.vendor import VendorCreate, VendorRead, VendorUpdate
from app.services.vendors import (
    VendorAlreadyExistsError,
    VendorNotFoundError,
    VendorSocietyNotFoundError,
    change_vendor_status,
    create_vendor,
    list_vendors,
    update_vendor,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/vendors")


def vendor_to_read(vendor: Vendor) -> VendorRead:
    return VendorRead.model_validate(vendor)


@router.get("", response_model=list[VendorRead])
def read_vendors(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[VendorRead]:
    try:
        vendors = list_vendors(db, tenant_context=tenant_context, society_id=society_id)
    except VendorSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [vendor_to_read(vendor) for vendor in vendors]


@router.post("", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def create_society_vendor(
    society_id: uuid.UUID,
    payload: VendorCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> VendorRead:
    try:
        vendor = create_vendor(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except VendorSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except VendorAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vendor code already exists in this society.",
        ) from exc
    return vendor_to_read(vendor)


@router.patch("/{vendor_id}", response_model=VendorRead)
def update_society_vendor(
    society_id: uuid.UUID,
    vendor_id: uuid.UUID,
    payload: VendorUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> VendorRead:
    try:
        vendor = update_vendor(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            vendor_id=vendor_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except VendorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.") from exc
    except VendorAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vendor code already exists in this society.",
        ) from exc
    return vendor_to_read(vendor)


@router.post("/{vendor_id}/inactivate", response_model=VendorRead)
def inactivate_society_vendor(
    society_id: uuid.UUID,
    vendor_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> VendorRead:
    try:
        vendor = change_vendor_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            vendor_id=vendor_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except VendorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.") from exc
    return vendor_to_read(vendor)


@router.post("/{vendor_id}/activate", response_model=VendorRead)
def activate_society_vendor(
    society_id: uuid.UUID,
    vendor_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> VendorRead:
    try:
        vendor = change_vendor_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            vendor_id=vendor_id,
            status="active",
            actor=tenant_context.user,
        )
    except VendorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.") from exc
    return vendor_to_read(vendor)
