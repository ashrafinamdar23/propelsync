from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Payment
from app.schemas.payment import (
    PaymentAllocationRead,
    PaymentCreate,
    PaymentDetailRead,
    PaymentRead,
    PaymentReverseRequest,
)
from app.services.payments import (
    PaymentAllocationInvalidError,
    PaymentInvalidStateError,
    PaymentJournalPostingError,
    PaymentReferenceInvalidError,
    PaymentSocietyNotFoundError,
    create_payment,
    list_payment_allocations,
    list_payments,
    reverse_payment,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/payments")


def payment_to_read(payment: Payment) -> PaymentRead:
    return PaymentRead.model_validate(payment)


@router.get("", response_model=list[PaymentRead])
def read_payments(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PaymentRead]:
    try:
        payments = list_payments(db, tenant_context=tenant_context, society_id=society_id)
    except PaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [payment_to_read(payment) for payment in payments]


@router.post("", response_model=PaymentDetailRead, status_code=status.HTTP_201_CREATED)
def create_society_payment(
    society_id: uuid.UUID,
    payload: PaymentCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> PaymentDetailRead:
    try:
        payment = create_payment(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except PaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except (PaymentReferenceInvalidError, PaymentAllocationInvalidError, PaymentJournalPostingError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    allocations = list_payment_allocations(
        db,
        tenant_context=tenant_context,
        society_id=society_id,
        payment_id=payment.id,
    )
    data = PaymentRead.model_validate(payment).model_dump()
    data["allocations"] = [PaymentAllocationRead.model_validate(allocation) for allocation in allocations]
    return PaymentDetailRead.model_validate(data)


@router.post("/{payment_id}/reverse", response_model=PaymentDetailRead)
def reverse_society_payment(
    society_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: PaymentReverseRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> PaymentDetailRead:
    try:
        payment = reverse_payment(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payment_id=payment_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except PaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except PaymentReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PaymentInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PaymentAllocationInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    allocations = list_payment_allocations(
        db,
        tenant_context=tenant_context,
        society_id=society_id,
        payment_id=payment.id,
    )
    data = PaymentRead.model_validate(payment).model_dump()
    data["allocations"] = [PaymentAllocationRead.model_validate(allocation) for allocation in allocations]
    return PaymentDetailRead.model_validate(data)
