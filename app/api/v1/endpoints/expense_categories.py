from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import ExpenseCategory
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryRead, ExpenseCategoryUpdate
from app.services.expense_categories import (
    ExpenseCategoryAccountInvalidError,
    ExpenseCategoryAlreadyExistsError,
    ExpenseCategoryNotFoundError,
    ExpenseCategorySocietyNotFoundError,
    change_expense_category_status,
    create_expense_category,
    list_expense_categories,
    update_expense_category,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/expense-categories")


def expense_category_to_read(category: ExpenseCategory) -> ExpenseCategoryRead:
    return ExpenseCategoryRead.model_validate(category)


@router.get("", response_model=list[ExpenseCategoryRead])
def read_expense_categories(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ExpenseCategoryRead]:
    try:
        categories = list_expense_categories(db, tenant_context=tenant_context, society_id=society_id)
    except ExpenseCategorySocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [expense_category_to_read(category) for category in categories]


@router.post("", response_model=ExpenseCategoryRead, status_code=status.HTTP_201_CREATED)
def create_society_expense_category(
    society_id: uuid.UUID,
    payload: ExpenseCategoryCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseCategoryRead:
    try:
        category = create_expense_category(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ExpenseCategorySocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except ExpenseCategoryAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ExpenseCategoryAccountInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return expense_category_to_read(category)


@router.patch("/{category_id}", response_model=ExpenseCategoryRead)
def update_society_expense_category(
    society_id: uuid.UUID,
    category_id: uuid.UUID,
    payload: ExpenseCategoryUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseCategoryRead:
    try:
        category = update_expense_category(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            category_id=category_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ExpenseCategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found.") from exc
    except ExpenseCategoryAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ExpenseCategoryAccountInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return expense_category_to_read(category)


@router.post("/{category_id}/inactivate", response_model=ExpenseCategoryRead)
def inactivate_society_expense_category(
    society_id: uuid.UUID,
    category_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseCategoryRead:
    try:
        category = change_expense_category_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            category_id=category_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except ExpenseCategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found.") from exc
    return expense_category_to_read(category)


@router.post("/{category_id}/activate", response_model=ExpenseCategoryRead)
def activate_society_expense_category(
    society_id: uuid.UUID,
    category_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseCategoryRead:
    try:
        category = change_expense_category_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            category_id=category_id,
            status="active",
            actor=tenant_context.user,
        )
    except ExpenseCategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found.") from exc
    return expense_category_to_read(category)
