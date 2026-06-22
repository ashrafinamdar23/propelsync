from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Resident
from app.schemas.resident import ResidentCreate, ResidentMoveOut, ResidentRead, ResidentUpdate
from app.services.residents import (
    ResidentAlreadyExistsError,
    ResidentFlatNotFoundError,
    ResidentInvalidDateError,
    ResidentNotFoundError,
    ResidentOwnerNotFoundError,
    ResidentUserNotFoundError,
    activate_resident,
    create_resident,
    list_residents,
    move_out_resident,
    update_resident,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/residents")


def resident_to_read(resident: Resident) -> ResidentRead:
    return ResidentRead(
        id=resident.id,
        tenant_id=resident.tenant_id,
        society_id=resident.society_id,
        flat_id=resident.flat_id,
        owner_id=resident.owner_id,
        user_id=resident.user_id,
        resident_type=resident.resident_type,
        full_name=resident.full_name,
        email=resident.email,
        mobile_number=resident.mobile_number,
        move_in_date=resident.move_in_date,
        move_out_date=resident.move_out_date,
        status=resident.status,
        created_at=resident.created_at,
        updated_at=resident.updated_at,
    )


@router.get("", response_model=list[ResidentRead])
def read_residents(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ResidentRead]:
    try:
        residents = list_residents(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
        )
    except ResidentFlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    return [resident_to_read(resident) for resident in residents]


@router.post("", response_model=ResidentRead, status_code=status.HTTP_201_CREATED)
def create_flat_resident(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: ResidentCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ResidentRead:
    try:
        resident = create_resident(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ResidentFlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    except ResidentOwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    except ResidentUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.") from exc
    except ResidentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current resident user already exists for this flat.",
        ) from exc
    return resident_to_read(resident)


@router.patch("/{resident_id}", response_model=ResidentRead)
def update_flat_resident(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    resident_id: uuid.UUID,
    payload: ResidentUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ResidentRead:
    try:
        resident = update_resident(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            resident_id=resident_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ResidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found.") from exc
    except ResidentOwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    except ResidentUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.") from exc
    except ResidentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current resident user already exists for this flat.",
        ) from exc
    return resident_to_read(resident)


@router.post("/{resident_id}/move-out", response_model=ResidentRead)
def move_out_flat_resident(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    resident_id: uuid.UUID,
    payload: ResidentMoveOut,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ResidentRead:
    try:
        resident = move_out_resident(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            resident_id=resident_id,
            move_out_date=payload.move_out_date,
            actor=tenant_context.user,
        )
    except ResidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found.") from exc
    except ResidentInvalidDateError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="move_out_date must be on or after move_in_date.",
        ) from exc
    return resident_to_read(resident)


@router.post("/{resident_id}/activate", response_model=ResidentRead)
def activate_flat_resident(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    resident_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ResidentRead:
    try:
        resident = activate_resident(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            resident_id=resident_id,
            actor=tenant_context.user,
        )
    except ResidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found.") from exc
    except ResidentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current resident user already exists for this flat.",
        ) from exc
    return resident_to_read(resident)
