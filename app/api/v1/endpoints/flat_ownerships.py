from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import FlatOwnership
from app.schemas.flat_ownership import (
    FlatOwnershipClose,
    FlatOwnershipCreate,
    FlatOwnershipRead,
    FlatOwnershipUpdate,
)
from app.services.flat_ownerships import (
    FlatOwnershipAlreadyExistsError,
    FlatOwnershipCurrentPrimaryExistsError,
    FlatOwnershipFlatNotFoundError,
    FlatOwnershipInvalidDateError,
    FlatOwnershipNotFoundError,
    FlatOwnershipOwnerNotFoundError,
    activate_flat_ownership,
    close_flat_ownership,
    create_flat_ownership,
    list_flat_ownerships,
    update_flat_ownership,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(
    prefix="/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/ownerships"
)


def flat_ownership_to_read(ownership: FlatOwnership) -> FlatOwnershipRead:
    return FlatOwnershipRead(
        id=ownership.id,
        tenant_id=ownership.tenant_id,
        society_id=ownership.society_id,
        flat_id=ownership.flat_id,
        owner_id=ownership.owner_id,
        ownership_type=ownership.ownership_type,
        ownership_percentage=ownership.ownership_percentage,
        effective_from=ownership.effective_from,
        effective_to=ownership.effective_to,
        status=ownership.status,
        created_at=ownership.created_at,
        updated_at=ownership.updated_at,
    )


@router.get("", response_model=list[FlatOwnershipRead])
def read_flat_ownerships(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FlatOwnershipRead]:
    try:
        ownerships = list_flat_ownerships(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
        )
    except FlatOwnershipFlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    return [flat_ownership_to_read(ownership) for ownership in ownerships]


@router.post("", response_model=FlatOwnershipRead, status_code=status.HTTP_201_CREATED)
def create_flat_ownership_assignment(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: FlatOwnershipCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatOwnershipRead:
    try:
        ownership = create_flat_ownership(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except FlatOwnershipFlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    except FlatOwnershipOwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    except FlatOwnershipAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Flat ownership already exists.",
        ) from exc
    except FlatOwnershipCurrentPrimaryExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current primary owner already exists.",
        ) from exc
    return flat_ownership_to_read(ownership)


@router.patch("/{ownership_id}", response_model=FlatOwnershipRead)
def update_flat_ownership_assignment(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    ownership_id: uuid.UUID,
    payload: FlatOwnershipUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatOwnershipRead:
    try:
        ownership = update_flat_ownership(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            ownership_id=ownership_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except FlatOwnershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flat ownership not found.",
        ) from exc
    except FlatOwnershipOwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    except FlatOwnershipAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Flat ownership already exists.",
        ) from exc
    except FlatOwnershipCurrentPrimaryExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current primary owner already exists.",
        ) from exc
    return flat_ownership_to_read(ownership)


@router.post("/{ownership_id}/close", response_model=FlatOwnershipRead)
def close_flat_ownership_assignment(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    ownership_id: uuid.UUID,
    payload: FlatOwnershipClose,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatOwnershipRead:
    try:
        ownership = close_flat_ownership(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            ownership_id=ownership_id,
            effective_to=payload.effective_to,
            actor=tenant_context.user,
        )
    except FlatOwnershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flat ownership not found.",
        ) from exc
    except FlatOwnershipInvalidDateError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="effective_to must be on or after effective_from.",
        ) from exc
    return flat_ownership_to_read(ownership)


@router.post("/{ownership_id}/activate", response_model=FlatOwnershipRead)
def activate_flat_ownership_assignment(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    ownership_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatOwnershipRead:
    try:
        ownership = activate_flat_ownership(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            ownership_id=ownership_id,
            actor=tenant_context.user,
        )
    except FlatOwnershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flat ownership not found.",
        ) from exc
    except FlatOwnershipCurrentPrimaryExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current primary owner already exists.",
        ) from exc
    return flat_ownership_to_read(ownership)
