from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import LeaseAgreement
from app.schemas.lease_agreement import (
    LeaseAgreementCreate,
    LeaseAgreementRead,
    LeaseAgreementTerminate,
    LeaseAgreementUpdate,
)
from app.services.lease_agreements import (
    LeaseAgreementAlreadyExistsError,
    LeaseAgreementFlatNotFoundError,
    LeaseAgreementInvalidDateError,
    LeaseAgreementNotFoundError,
    LeaseAgreementOwnerNotFoundError,
    LeaseAgreementResidentNotFoundError,
    create_lease_agreement,
    list_lease_agreements,
    terminate_lease_agreement,
    update_lease_agreement,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(
    prefix="/societies/{society_id}/buildings/{building_id}/flats/{flat_id}/lease-agreements"
)


def lease_agreement_to_read(lease: LeaseAgreement) -> LeaseAgreementRead:
    return LeaseAgreementRead.model_validate(lease)


@router.get("", response_model=list[LeaseAgreementRead])
def read_lease_agreements(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LeaseAgreementRead]:
    try:
        leases = list_lease_agreements(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
        )
    except LeaseAgreementFlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    return [lease_agreement_to_read(lease) for lease in leases]


@router.post("", response_model=LeaseAgreementRead, status_code=status.HTTP_201_CREATED)
def create_flat_lease_agreement(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: LeaseAgreementCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseAgreementRead:
    try:
        lease = create_lease_agreement(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except LeaseAgreementFlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
    except LeaseAgreementOwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    except LeaseAgreementResidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found.") from exc
    except LeaseAgreementAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active lease already exists for this flat.",
        ) from exc
    return lease_agreement_to_read(lease)


@router.patch("/{lease_agreement_id}", response_model=LeaseAgreementRead)
def update_flat_lease_agreement(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    lease_agreement_id: uuid.UUID,
    payload: LeaseAgreementUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseAgreementRead:
    try:
        lease = update_lease_agreement(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            lease_agreement_id=lease_agreement_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except LeaseAgreementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease agreement not found.") from exc
    except LeaseAgreementOwnerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found.") from exc
    except LeaseAgreementResidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found.") from exc
    except LeaseAgreementAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active lease already exists for this flat.",
        ) from exc
    return lease_agreement_to_read(lease)


@router.post("/{lease_agreement_id}/terminate", response_model=LeaseAgreementRead)
def terminate_flat_lease_agreement(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    lease_agreement_id: uuid.UUID,
    payload: LeaseAgreementTerminate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseAgreementRead:
    try:
        lease = terminate_lease_agreement(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            lease_agreement_id=lease_agreement_id,
            move_out_date=payload.move_out_date,
            reason=payload.reason,
            actor=tenant_context.user,
        )
    except LeaseAgreementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease agreement not found.") from exc
    except LeaseAgreementInvalidDateError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return lease_agreement_to_read(lease)
