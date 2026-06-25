from typing import Annotated
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import ExpensePayment
from app.schemas.pagination import PaginatedResponse
from app.schemas.expense_payment import (
    ExpensePaymentAllocateRequest,
    ExpensePaymentAllocationRead,
    ExpensePaymentCreate,
    ExpensePaymentDetailRead,
    ExpensePaymentRead,
)
from app.services.expense_payments import (
    ExpensePaymentAllocationInvalidError,
    ExpensePaymentJournalPostingError,
    ExpensePaymentReferenceInvalidError,
    ExpensePaymentSocietyNotFoundError,
    allocate_existing_expense_payment,
    create_expense_payment,
    list_expense_payment_allocations,
    list_expense_payments_paginated,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/expense-payments")


def expense_payment_to_read(payment: ExpensePayment) -> ExpensePaymentRead:
    return ExpensePaymentRead.model_validate(payment)


@router.get("", response_model=PaginatedResponse[ExpensePaymentRead])
def read_expense_payments(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    vendor_id: Annotated[uuid.UUID | None, Query()] = None,
    payment_account_id: Annotated[uuid.UUID | None, Query()] = None,
    payment_mode: Annotated[str | None, Query()] = None,
    payment_status: Annotated[str | None, Query(alias="status")] = None,
    unapplied_only: Annotated[bool, Query()] = False,
    payment_date_from: Annotated[date | None, Query()] = None,
    payment_date_to: Annotated[date | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "payment_date",
    sort_direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> PaginatedResponse[ExpensePaymentRead]:
    try:
        payments, total_items = list_expense_payments_paginated(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            vendor_id=vendor_id,
            payment_account_id=payment_account_id,
            payment_mode=payment_mode,
            status=payment_status,
            unapplied_only=unapplied_only,
            payment_date_from=payment_date_from,
            payment_date_to=payment_date_to,
            sort_by=sort_by,
            sort_direction=sort_direction,
            page=page,
            page_size=page_size,
        )
    except ExpensePaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return PaginatedResponse[ExpensePaymentRead](
        items=[expense_payment_to_read(payment) for payment in payments],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=(total_items + page_size - 1) // page_size,
    )


@router.post("", response_model=ExpensePaymentDetailRead, status_code=status.HTTP_201_CREATED)
def create_society_expense_payment(
    society_id: uuid.UUID,
    payload: ExpensePaymentCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpensePaymentDetailRead:
    try:
        payment = create_expense_payment(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ExpensePaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except (
        ExpensePaymentReferenceInvalidError,
        ExpensePaymentAllocationInvalidError,
        ExpensePaymentJournalPostingError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    allocations = list_expense_payment_allocations(
        db,
        tenant_context=tenant_context,
        society_id=society_id,
        expense_payment_id=payment.id,
    )
    data = ExpensePaymentRead.model_validate(payment).model_dump()
    data["allocations"] = [ExpensePaymentAllocationRead.model_validate(allocation) for allocation in allocations]
    return ExpensePaymentDetailRead.model_validate(data)


@router.post("/{expense_payment_id}/allocate", response_model=ExpensePaymentDetailRead)
def allocate_society_expense_payment(
    society_id: uuid.UUID,
    expense_payment_id: uuid.UUID,
    payload: ExpensePaymentAllocateRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpensePaymentDetailRead:
    try:
        payment = allocate_existing_expense_payment(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            expense_payment_id=expense_payment_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ExpensePaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except ExpensePaymentReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExpensePaymentAllocationInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    allocations = list_expense_payment_allocations(
        db,
        tenant_context=tenant_context,
        society_id=society_id,
        expense_payment_id=payment.id,
    )
    data = ExpensePaymentRead.model_validate(payment).model_dump()
    data["allocations"] = [ExpensePaymentAllocationRead.model_validate(allocation) for allocation in allocations]
    return ExpensePaymentDetailRead.model_validate(data)
