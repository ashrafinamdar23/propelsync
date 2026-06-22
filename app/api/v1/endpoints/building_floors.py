from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import BuildingFloor
from app.schemas.building_floor import BuildingFloorCreate, BuildingFloorRead, BuildingFloorUpdate
from app.services.building_floors import (
    BuildingFloorAlreadyExistsError,
    BuildingFloorBuildingNotFoundError,
    BuildingFloorNotFoundError,
    change_building_floor_status,
    create_building_floor,
    list_building_floors,
    update_building_floor,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/buildings/{building_id}/floors")


def building_floor_to_read(floor: BuildingFloor) -> BuildingFloorRead:
    return BuildingFloorRead.model_validate(floor)


@router.get("", response_model=list[BuildingFloorRead])
def read_building_floors(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[BuildingFloorRead]:
    try:
        floors = list_building_floors(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
        )
    except BuildingFloorBuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    return [building_floor_to_read(floor) for floor in floors]


@router.post("", response_model=BuildingFloorRead, status_code=status.HTTP_201_CREATED)
def create_building_floor_record(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: BuildingFloorCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingFloorRead:
    try:
        floor = create_building_floor(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except BuildingFloorBuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    except BuildingFloorAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return building_floor_to_read(floor)


@router.patch("/{floor_id}", response_model=BuildingFloorRead)
def update_building_floor_record(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    payload: BuildingFloorUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingFloorRead:
    try:
        floor = update_building_floor(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            floor_id=floor_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except BuildingFloorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building floor not found.") from exc
    except BuildingFloorAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return building_floor_to_read(floor)


@router.post("/{floor_id}/inactivate", response_model=BuildingFloorRead)
def inactivate_building_floor_record(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingFloorRead:
    try:
        floor = change_building_floor_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            floor_id=floor_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except BuildingFloorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building floor not found.") from exc
    return building_floor_to_read(floor)


@router.post("/{floor_id}/activate", response_model=BuildingFloorRead)
def activate_building_floor_record(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingFloorRead:
    try:
        floor = change_building_floor_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            floor_id=floor_id,
            status="active",
            actor=tenant_context.user,
        )
    except BuildingFloorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building floor not found.") from exc
    return building_floor_to_read(floor)
