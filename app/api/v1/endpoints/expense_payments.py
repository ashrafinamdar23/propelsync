from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import ExpensePayment
from app.schemas.expense_payment import (
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
    create_expense_payment,
    list_expense_payment_allocations,
    list_expense_payments,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/expense-payments")


def expense_payment_to_read(payment: ExpensePayment) -> ExpensePaymentRead:
    return ExpensePaymentRead.model_validate(payment)


@router.get("", response_model=list[ExpensePaymentRead])
def read_expense_payments(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ExpensePaymentRead]:
    try:
        payments = list_expense_payments(db, tenant_context=tenant_context, society_id=society_id)
    except ExpensePaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [expense_payment_to_read(payment) for payment in payments]


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
