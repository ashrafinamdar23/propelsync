import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, ExpenseCategory, Society, User
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class ExpenseCategoryAlreadyExistsError(Exception):
    pass


class ExpenseCategoryNotFoundError(Exception):
    pass


class ExpenseCategorySocietyNotFoundError(Exception):
    pass


class ExpenseCategoryAccountInvalidError(Exception):
    pass


def ensure_society_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> None:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise ExpenseCategorySocietyNotFoundError("Society not found.")


def ensure_expense_category_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ExpenseCategoryCreate | ExpenseCategoryUpdate,
    existing_category_id: uuid.UUID | None = None,
) -> None:
    statement = select(ExpenseCategory).where(
        ExpenseCategory.tenant_id == tenant_context.tenant_id,
        ExpenseCategory.society_id == society_id,
        ExpenseCategory.name == payload.name,
    )
    if existing_category_id is not None:
        statement = statement.where(ExpenseCategory.id != existing_category_id)
    if session.scalar(statement) is not None:
        raise ExpenseCategoryAlreadyExistsError("Expense category name already exists.")

    if payload.code is None:
        return

    statement = select(ExpenseCategory).where(
        ExpenseCategory.tenant_id == tenant_context.tenant_id,
        ExpenseCategory.society_id == society_id,
        ExpenseCategory.code == payload.code,
    )
    if existing_category_id is not None:
        statement = statement.where(ExpenseCategory.id != existing_category_id)
    if session.scalar(statement) is not None:
        raise ExpenseCategoryAlreadyExistsError("Expense category code already exists.")


def ensure_expense_account_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense_account_id: uuid.UUID,
) -> None:
    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == expense_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "expense",
            ChartOfAccount.status == "active",
        )
    )
    if account is None:
        raise ExpenseCategoryAccountInvalidError("Expense account must be an active expense account.")


def list_expense_categories(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[ExpenseCategory]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(ExpenseCategory)
            .where(
                ExpenseCategory.tenant_id == tenant_context.tenant_id,
                ExpenseCategory.society_id == society_id,
            )
            .order_by(ExpenseCategory.name)
        )
    )


def get_expense_category_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    category_id: uuid.UUID,
) -> ExpenseCategory:
    category = session.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.id == category_id,
            ExpenseCategory.tenant_id == tenant_context.tenant_id,
            ExpenseCategory.society_id == society_id,
        )
    )
    if category is None:
        raise ExpenseCategoryNotFoundError("Expense category not found.")
    return category


def create_expense_category(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ExpenseCategoryCreate,
    actor: User,
) -> ExpenseCategory:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    ensure_expense_category_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    ensure_expense_account_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense_account_id=payload.expense_account_id,
    )
    category = ExpenseCategory(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        expense_account_id=payload.expense_account_id,
        status="active",
    )
    session.add(category)
    session.flush()
    record_audit_log(
        session,
        action="expense_category.created",
        entity_type="ExpenseCategory",
        entity_id=category.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense category created: {category.name}",
        metadata={"society_id": str(society_id), "expense_account_id": str(category.expense_account_id)},
    )
    session.commit()
    session.refresh(category)
    return category


def update_expense_category(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    category_id: uuid.UUID,
    payload: ExpenseCategoryUpdate,
    actor: User,
) -> ExpenseCategory:
    category = get_expense_category_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        category_id=category_id,
    )
    ensure_expense_category_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        existing_category_id=category.id,
    )
    ensure_expense_account_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense_account_id=payload.expense_account_id,
    )
    previous_values = {
        "name": category.name,
        "code": category.code,
        "description": category.description,
        "expense_account_id": str(category.expense_account_id),
    }
    category.name = payload.name
    category.code = payload.code
    category.description = payload.description
    category.expense_account_id = payload.expense_account_id
    record_audit_log(
        session,
        action="expense_category.updated",
        entity_type="ExpenseCategory",
        entity_id=category.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense category updated: {category.name}",
        metadata={
            "society_id": str(society_id),
            "previous": previous_values,
            "current": {
                "name": category.name,
                "code": category.code,
                "description": category.description,
                "expense_account_id": str(category.expense_account_id),
            },
        },
    )
    session.commit()
    session.refresh(category)
    return category


def change_expense_category_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    category_id: uuid.UUID,
    status: str,
    actor: User,
) -> ExpenseCategory:
    category = get_expense_category_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        category_id=category_id,
    )
    previous_status = category.status
    category.status = status
    record_audit_log(
        session,
        action="expense_category.inactivated" if status == "inactive" else "expense_category.activated",
        entity_type="ExpenseCategory",
        entity_id=category.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense category {status}: {category.name}",
        metadata={
            "society_id": str(society_id),
            "previous_status": previous_status,
            "current_status": status,
        },
    )
    session.commit()
    session.refresh(category)
    return category
