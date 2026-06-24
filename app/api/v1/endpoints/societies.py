from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Society
from app.schemas.society import SocietyCreate, SocietyRead, SocietyUpdate
from app.services.societies import (
    SocietyAlreadyExistsError,
    SocietyAccountInvalidError,
    SocietyNotFoundError,
    change_society_status,
    create_society,
    list_societies,
    update_society,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_tenant_admin_context


router = APIRouter(prefix="/societies")


def society_to_read(society: Society) -> SocietyRead:
    return SocietyRead(
        id=society.id,
        tenant_id=society.tenant_id,
        name=society.name,
        registration_number=society.registration_number,
        address_line1=society.address_line1,
        address_line2=society.address_line2,
        city=society.city,
        state=society.state,
        postal_code=society.postal_code,
        country=society.country,
        timezone=society.timezone,
        locale=society.locale,
        currency=society.currency,
        financial_year_start_month=society.financial_year_start_month,
        receivable_account_id=society.receivable_account_id,
        payable_account_id=society.payable_account_id,
        member_advance_account_id=society.member_advance_account_id,
        status=society.status,
        created_at=society.created_at,
        updated_at=society.updated_at,
    )


@router.get("", response_model=list[SocietyRead])
def read_societies(
    tenant_context: Annotated[TenantContext, Depends(require_tenant_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[SocietyRead]:
    return [society_to_read(society) for society in list_societies(db, tenant_context)]


@router.post("", response_model=SocietyRead, status_code=status.HTTP_201_CREATED)
def create_tenant_society(
    payload: SocietyCreate,
    tenant_context: Annotated[TenantContext, Depends(require_tenant_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> SocietyRead:
    try:
        society = create_society(
            db,
            tenant_context=tenant_context,
            payload=payload,
            actor=tenant_context.user,
        )
    except SocietyAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Society name or registration number already exists.",
        ) from exc
    except SocietyAccountInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return society_to_read(society)


@router.patch("/{society_id}", response_model=SocietyRead)
def update_tenant_society(
    society_id: uuid.UUID,
    payload: SocietyUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_tenant_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> SocietyRead:
    try:
        society = update_society(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except SocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except SocietyAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Society name or registration number already exists.",
        ) from exc
    except SocietyAccountInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return society_to_read(society)


@router.post("/{society_id}/suspend", response_model=SocietyRead)
def suspend_tenant_society(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_tenant_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> SocietyRead:
    try:
        society = change_society_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            status="suspended",
            actor=tenant_context.user,
        )
    except SocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return society_to_read(society)


@router.post("/{society_id}/activate", response_model=SocietyRead)
def activate_tenant_society(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_tenant_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> SocietyRead:
    try:
        society = change_society_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            status="active",
            actor=tenant_context.user,
        )
    except SocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return society_to_read(society)
