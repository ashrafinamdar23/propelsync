from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import FlatType
from app.schemas.flat_type import FlatTypeCreate, FlatTypeRead, FlatTypeUpdate
from app.services.flat_types import (
    FlatTypeAlreadyExistsError,
    FlatTypeNotFoundError,
    FlatTypeSocietyNotFoundError,
    change_flat_type_status,
    create_flat_type,
    list_flat_types,
    update_flat_type,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/flat-types")


def flat_type_to_read(flat_type: FlatType) -> FlatTypeRead:
    return FlatTypeRead.model_validate(flat_type)


@router.get("", response_model=list[FlatTypeRead])
def read_flat_types(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FlatTypeRead]:
    try:
        flat_types = list_flat_types(db, tenant_context=tenant_context, society_id=society_id)
    except FlatTypeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [flat_type_to_read(flat_type) for flat_type in flat_types]


@router.post("", response_model=FlatTypeRead, status_code=status.HTTP_201_CREATED)
def create_society_flat_type(
    society_id: uuid.UUID,
    payload: FlatTypeCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatTypeRead:
    try:
        flat_type = create_flat_type(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except FlatTypeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except FlatTypeAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return flat_type_to_read(flat_type)


@router.patch("/{flat_type_id}", response_model=FlatTypeRead)
def update_society_flat_type(
    society_id: uuid.UUID,
    flat_type_id: uuid.UUID,
    payload: FlatTypeUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatTypeRead:
    try:
        flat_type = update_flat_type(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_type_id=flat_type_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except FlatTypeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat type not found.") from exc
    except FlatTypeAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return flat_type_to_read(flat_type)


@router.post("/{flat_type_id}/inactivate", response_model=FlatTypeRead)
def inactivate_society_flat_type(
    society_id: uuid.UUID,
    flat_type_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatTypeRead:
    try:
        flat_type = change_flat_type_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_type_id=flat_type_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except FlatTypeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat type not found.") from exc
    return flat_type_to_read(flat_type)


@router.post("/{flat_type_id}/activate", response_model=FlatTypeRead)
def activate_society_flat_type(
    society_id: uuid.UUID,
    flat_type_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> FlatTypeRead:
    try:
        flat_type = change_flat_type_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_type_id=flat_type_id,
            status="active",
            actor=tenant_context.user,
        )
    except FlatTypeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat type not found.") from exc
    return flat_type_to_read(flat_type)
