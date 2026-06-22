from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Building
from app.schemas.building import BuildingCreate, BuildingRead, BuildingUpdate
from app.services.buildings import (
    BuildingAlreadyExistsError,
    BuildingNotFoundError,
    change_building_status,
    create_building,
    list_buildings,
    update_building,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/buildings")


def building_to_read(building: Building) -> BuildingRead:
    return BuildingRead(
        id=building.id,
        tenant_id=building.tenant_id,
        society_id=building.society_id,
        name=building.name,
        code=building.code,
        status=building.status,
        created_at=building.created_at,
        updated_at=building.updated_at,
    )


@router.get("", response_model=list[BuildingRead])
def read_buildings(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[BuildingRead]:
    return [
        building_to_read(building)
        for building in list_buildings(db, tenant_context=tenant_context, society_id=society_id)
    ]


@router.post("", response_model=BuildingRead, status_code=status.HTTP_201_CREATED)
def create_society_building(
    society_id: uuid.UUID,
    payload: BuildingCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingRead:
    try:
        building = create_building(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except BuildingAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Building name or code already exists.",
        ) from exc
    return building_to_read(building)


@router.patch("/{building_id}", response_model=BuildingRead)
def update_society_building(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: BuildingUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingRead:
    try:
        building = update_building(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except BuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    except BuildingAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Building name or code already exists.",
        ) from exc
    return building_to_read(building)


@router.post("/{building_id}/suspend", response_model=BuildingRead)
def suspend_society_building(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingRead:
    try:
        building = change_building_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            status="suspended",
            actor=tenant_context.user,
        )
    except BuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    return building_to_read(building)


@router.post("/{building_id}/activate", response_model=BuildingRead)
def activate_society_building(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingRead:
    try:
        building = change_building_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            status="active",
            actor=tenant_context.user,
        )
    except BuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    return building_to_read(building)
