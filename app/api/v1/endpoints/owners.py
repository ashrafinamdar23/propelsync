from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Owner
from app.schemas.owner import OwnerCreate, OwnerRead, OwnerUpdate
from app.services.owners import (
    OwnerAlreadyExistsError,
    OwnerNotFoundError,
    OwnerSocietyNotFoundError,
    OwnerUserNotFoundError,
    change_owner_status,
    create_owner,
    list_owners,
    update_owner,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/owners")


def owner_to_read(owner: Owner) -> OwnerRead:
    return OwnerRead(
        id=owner.id,
        tenant_id=owner.tenant_id,
        society_id=owner.society_id,
        user_id=owner.user_id,
        owner_type=owner.owner_type,
        full_name=owner.full_name,
        email=owner.email,
        mobile_number=owner.mobile_number,
        tax_identifier=owner.tax_identifier,
        billing_address=owner.billing_address,
        status=owner.status,
        created_at=owner.created_at,
        updated_at=owner.updated_at,
    )


@router.get("", response_model=list[OwnerRead])
def read_owners(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[OwnerRead]:
    try:
        owners = list_owners(db, tenant_context=tenant_context, society_id=society_id)
    except OwnerSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [owner_to_read(owner) for owner in owners]


@router.post("", response_model=OwnerRead, status_code=status.HTTP_201_CREATED)
def create_society_owner(
    society_id: uuid.UUID,
    payload: OwnerCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> OwnerRead:
    try:
        owner = create_owner(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except OwnerSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except OwnerUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.") from exc
    except OwnerAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Owner user already exists in this society.",
        ) from exc
    return owner_to_read(owner)


@router.patch("/{owner_id}", response_model=OwnerRead)
def update_society_owner(
    society_id: uuid.UUID,
    owner_id: uuid.UUID,
    payload: OwnerUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> OwnerRead:
    try:
        owner = update_owner(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            owner_id=owner_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except OwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    except OwnerUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.") from exc
    except OwnerAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Owner user already exists in this society.",
        ) from exc
    return owner_to_read(owner)


@router.post("/{owner_id}/inactivate", response_model=OwnerRead)
def inactivate_society_owner(
    society_id: uuid.UUID,
    owner_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> OwnerRead:
    try:
        owner = change_owner_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            owner_id=owner_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except OwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    return owner_to_read(owner)


@router.post("/{owner_id}/activate", response_model=OwnerRead)
def activate_society_owner(
    society_id: uuid.UUID,
    owner_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> OwnerRead:
    try:
        owner = change_owner_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            owner_id=owner_id,
            status="active",
            actor=tenant_context.user,
        )
    except OwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    return owner_to_read(owner)
