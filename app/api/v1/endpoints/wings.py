from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Wing
from app.schemas.wing import WingCreate, WingRead, WingUpdate
from app.services.wings import (
    WingAlreadyExistsError,
    WingBuildingNotFoundError,
    WingNotFoundError,
    change_wing_status,
    create_wing,
    list_wings,
    update_wing,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/buildings/{building_id}/wings")


def wing_to_read(wing: Wing) -> WingRead:
    return WingRead(
        id=wing.id,
        tenant_id=wing.tenant_id,
        society_id=wing.society_id,
        building_id=wing.building_id,
        name=wing.name,
        code=wing.code,
        status=wing.status,
        created_at=wing.created_at,
        updated_at=wing.updated_at,
    )


@router.get("", response_model=list[WingRead])
def read_wings(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[WingRead]:
    try:
        wings = list_wings(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
        )
    except WingBuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    return [wing_to_read(wing) for wing in wings]


@router.post("", response_model=WingRead, status_code=status.HTTP_201_CREATED)
def create_building_wing(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: WingCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> WingRead:
    try:
        wing = create_wing(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except WingBuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    except WingAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Wing name or code already exists.",
        ) from exc
    return wing_to_read(wing)


@router.patch("/{wing_id}", response_model=WingRead)
def update_building_wing(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    wing_id: uuid.UUID,
    payload: WingUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> WingRead:
    try:
        wing = update_wing(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            wing_id=wing_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except WingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wing not found.") from exc
    except WingAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Wing name or code already exists.",
        ) from exc
    return wing_to_read(wing)


@router.post("/{wing_id}/suspend", response_model=WingRead)
def suspend_building_wing(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    wing_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> WingRead:
    try:
        wing = change_wing_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            wing_id=wing_id,
            status="suspended",
            actor=tenant_context.user,
        )
    except WingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wing not found.") from exc
    return wing_to_read(wing)


@router.post("/{wing_id}/activate", response_model=WingRead)
def activate_building_wing(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    wing_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> WingRead:
    try:
        wing = change_wing_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            wing_id=wing_id,
            status="active",
            actor=tenant_context.user,
        )
    except WingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wing not found.") from exc
    return wing_to_read(wing)
