from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import ChargeType
from app.schemas.charge_type import ChargeTypeCreate, ChargeTypeRead, ChargeTypeUpdate
from app.services.charge_types import (
    ChargeTypeAlreadyExistsError,
    ChargeTypeNotFoundError,
    ChargeTypeRevenueAccountInvalidError,
    ChargeTypeSocietyNotFoundError,
    change_charge_type_status,
    create_charge_type,
    list_charge_types,
    update_charge_type,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/charge-types")


def charge_type_to_read(charge_type: ChargeType) -> ChargeTypeRead:
    return ChargeTypeRead.model_validate(charge_type)


@router.get("", response_model=list[ChargeTypeRead])
def read_charge_types(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ChargeTypeRead]:
    try:
        charge_types = list_charge_types(db, tenant_context=tenant_context, society_id=society_id)
    except ChargeTypeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [charge_type_to_read(charge_type) for charge_type in charge_types]


@router.post("", response_model=ChargeTypeRead, status_code=status.HTTP_201_CREATED)
def create_society_charge_type(
    society_id: uuid.UUID,
    payload: ChargeTypeCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChargeTypeRead:
    try:
        charge_type = create_charge_type(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ChargeTypeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except ChargeTypeAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ChargeTypeRevenueAccountInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return charge_type_to_read(charge_type)


@router.patch("/{charge_type_id}", response_model=ChargeTypeRead)
def update_society_charge_type(
    society_id: uuid.UUID,
    charge_type_id: uuid.UUID,
    payload: ChargeTypeUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChargeTypeRead:
    try:
        charge_type = update_charge_type(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            charge_type_id=charge_type_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ChargeTypeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge type not found.") from exc
    except ChargeTypeAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ChargeTypeRevenueAccountInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return charge_type_to_read(charge_type)


@router.post("/{charge_type_id}/inactivate", response_model=ChargeTypeRead)
def inactivate_society_charge_type(
    society_id: uuid.UUID,
    charge_type_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChargeTypeRead:
    try:
        charge_type = change_charge_type_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            charge_type_id=charge_type_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except ChargeTypeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge type not found.") from exc
    return charge_type_to_read(charge_type)


@router.post("/{charge_type_id}/activate", response_model=ChargeTypeRead)
def activate_society_charge_type(
    society_id: uuid.UUID,
    charge_type_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChargeTypeRead:
    try:
        charge_type = change_charge_type_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            charge_type_id=charge_type_id,
            status="active",
            actor=tenant_context.user,
        )
    except ChargeTypeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge type not found.") from exc
    return charge_type_to_read(charge_type)
