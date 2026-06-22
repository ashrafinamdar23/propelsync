from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Flat
from app.schemas.flat import FlatCreate, FlatRead, FlatUpdate
from app.schemas.flat_import import (
    FlatImportConfirmRequest,
    FlatImportConfirmResponse,
    FlatImportPreviewRequest,
    FlatImportPreviewResponse,
)
from app.services.flat_imports import (
    FlatImportValidationError,
    confirm_flat_import,
    preview_flat_import,
)
from app.services.flats import (
    FlatAlreadyExistsError,
    FlatBuildingNotFoundError,
    FlatFloorNotFoundError,
    FlatNotFoundError,
    FlatTypeNotFoundError,
    FlatWingNotFoundError,
    change_flat_status,
    create_flat,
    list_flats,
    update_flat,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/buildings/{building_id}/flats")


def flat_to_read(flat: Flat) -> FlatRead:
    return FlatRead(
        id=flat.id,
        tenant_id=flat.tenant_id,
        society_id=flat.society_id,
        building_id=flat.building_id,
        wing_id=flat.wing_id,
        floor_id=flat.floor_id,
        flat_type_id=flat.flat_type_id,
        flat_number=flat.flat_number,
        floor_number=flat.floor_number,
        carpet_area_sqft=flat.carpet_area_sqft,
        built_up_area_sqft=flat.built_up_area_sqft,
        parking_count=flat.parking_count,
        status=flat.status,
        created_at=flat.created_at,
        updated_at=flat.updated_at,
    )


@router.get("", response_model=list[FlatRead])
def read_flats(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FlatRead]:
    try:
        flats = list_flats(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
        )
    except FlatBuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    return [flat_to_read(flat) for flat in flats]


@router.post("", response_model=FlatRead, status_code=status.HTTP_201_CREATED)
def create_building_flat(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: FlatCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatRead:
    try:
        flat = create_flat(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except FlatBuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    except FlatWingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wing not found.") from exc
    except FlatFloorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building floor not found.") from exc
    except FlatTypeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat type not found.") from exc
    except FlatAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Flat number already exists.",
        ) from exc
    return flat_to_read(flat)


@router.post("/import/preview", response_model=FlatImportPreviewResponse)
def preview_building_flat_import(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: FlatImportPreviewRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatImportPreviewResponse:
    try:
        return preview_flat_import(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            rows=payload.rows,
        )
    except FlatBuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc


@router.post("/import/confirm", response_model=FlatImportConfirmResponse, status_code=status.HTTP_201_CREATED)
def confirm_building_flat_import(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: FlatImportConfirmRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatImportConfirmResponse:
    try:
        return confirm_flat_import(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            rows=payload.rows,
            actor=tenant_context.user,
        )
    except FlatBuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found.") from exc
    except FlatImportValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.preview.model_dump(mode="json"),
        ) from exc


@router.patch("/{flat_id}", response_model=FlatRead)
def update_building_flat(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: FlatUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatRead:
    try:
        flat = update_flat(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except FlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    except FlatWingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wing not found.") from exc
    except FlatFloorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building floor not found.") from exc
    except FlatTypeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat type not found.") from exc
    except FlatAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Flat number already exists.",
        ) from exc
    return flat_to_read(flat)


@router.post("/{flat_id}/inactivate", response_model=FlatRead)
def inactivate_building_flat(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatRead:
    try:
        flat = change_flat_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except FlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    return flat_to_read(flat)


@router.post("/{flat_id}/activate", response_model=FlatRead)
def activate_building_flat(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatRead:
    try:
        flat = change_flat_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            status="active",
            actor=tenant_context.user,
        )
    except FlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    return flat_to_read(flat)
