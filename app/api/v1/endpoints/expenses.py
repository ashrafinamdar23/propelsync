from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Expense
from app.schemas.expense import ExpenseCancelRequest, ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.services.expenses import (
    ExpenseAlreadyExistsError,
    ExpenseCancellationInvalidError,
    ExpenseJournalPostingError,
    ExpenseNotFoundError,
    ExpenseReferenceInvalidError,
    ExpenseSocietyNotFoundError,
    approve_expense,
    cancel_expense,
    create_expense,
    list_expenses,
    update_expense,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/expenses")


def expense_to_read(expense: Expense) -> ExpenseRead:
    return ExpenseRead.model_validate(expense)


@router.get("", response_model=list[ExpenseRead])
def read_expenses(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ExpenseRead]:
    try:
        expenses = list_expenses(db, tenant_context=tenant_context, society_id=society_id)
    except ExpenseSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [expense_to_read(expense) for expense in expenses]


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_society_expense(
    society_id: uuid.UUID,
    payload: ExpenseCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    try:
        expense = create_expense(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ExpenseSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except ExpenseAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (ExpenseReferenceInvalidError, ExpenseJournalPostingError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return expense_to_read(expense)


@router.patch("/{expense_id}", response_model=ExpenseRead)
def update_society_expense(
    society_id: uuid.UUID,
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    try:
        expense = update_expense(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            expense_id=expense_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ExpenseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.") from exc
    except ExpenseAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (ExpenseReferenceInvalidError, ExpenseCancellationInvalidError, ExpenseJournalPostingError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return expense_to_read(expense)


@router.post("/{expense_id}/approve", response_model=ExpenseRead)
def approve_society_expense(
    society_id: uuid.UUID,
    expense_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    try:
        expense = approve_expense(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            expense_id=expense_id,
            actor=tenant_context.user,
        )
    except ExpenseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.") from exc
    except ExpenseCancellationInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return expense_to_read(expense)


@router.post("/{expense_id}/cancel", response_model=ExpenseRead)
def cancel_society_expense(
    society_id: uuid.UUID,
    expense_id: uuid.UUID,
    payload: ExpenseCancelRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    try:
        expense = cancel_expense(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            expense_id=expense_id,
            reason=payload.reason,
            actor=tenant_context.user,
        )
    except ExpenseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.") from exc
    except ExpenseCancellationInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return expense_to_read(expense)
