import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import (
    ChartOfAccount,
    Expense,
    ExpenseCategory,
    ExpensePayment,
    ExpensePaymentAllocation,
    JournalEntry,
    JournalLine,
    Society,
    User,
    Vendor,
)
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class ExpenseAlreadyExistsError(Exception):
    pass


class ExpenseNotFoundError(Exception):
    pass


class ExpenseReferenceInvalidError(Exception):
    pass


class ExpenseSocietyNotFoundError(Exception):
    pass


class ExpenseCancellationInvalidError(Exception):
    pass


class ExpenseJournalPostingError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def reverse_existing_expense_journal(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense: Expense,
) -> None:
    if expense.journal_entry_id is None:
        return
    journal_entry = session.scalar(
        select(JournalEntry).where(
            JournalEntry.id == expense.journal_entry_id,
            JournalEntry.tenant_id == tenant_context.tenant_id,
            JournalEntry.society_id == society_id,
        )
    )
    if journal_entry is not None:
        journal_entry.status = "reversed"


def post_expense_journal(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense: Expense,
) -> JournalEntry:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise ExpenseSocietyNotFoundError("Society not found.")

    expense_account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == expense.expense_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "expense",
            ChartOfAccount.status == "active",
        )
    )
    if expense_account is None:
        raise ExpenseJournalPostingError("Expense account must be an active expense account.")

    credit_account_id: uuid.UUID | None = None
    if expense.expense_type == "cash_expense" or (
        expense.expense_type == "other" and expense.payment_account_id is not None
    ):
        credit_account_id = expense.payment_account_id
        if credit_account_id is None:
            raise ExpenseJournalPostingError("Cash expenses require a payment account.")
        credit_account_type = "asset"
    else:
        credit_account_id = society.payable_account_id
        if credit_account_id is None:
            raise ExpenseJournalPostingError("Configure the society payable account before recording vendor bills.")
        credit_account_type = "liability"

    credit_account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == credit_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == credit_account_type,
            ChartOfAccount.status == "active",
        )
    )
    if credit_account is None:
        raise ExpenseJournalPostingError(
            "Expense credit account must be an active "
            f"{credit_account_type} account."
        )

    journal_entry = JournalEntry(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        journal_date=expense.expense_date,
        source_type="expense",
        source_id=expense.id,
        reference_number=expense.reference_number or expense.vendor_bill_number,
        description=f"Expense recorded: {expense.description}",
        status="posted",
        notes=expense.notes,
    )
    session.add(journal_entry)
    session.flush()

    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=expense_account.id,
            line_number=1,
            description=f"Expense: {expense_account.account_name}",
            debit_amount=money(expense.total_amount),
            credit_amount=Decimal("0.00"),
        )
    )
    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=credit_account.id,
            line_number=2,
            description=f"Credit: {credit_account.account_name}",
            debit_amount=Decimal("0.00"),
            credit_amount=money(expense.total_amount),
        )
    )
    expense.journal_entry_id = journal_entry.id
    return journal_entry


def create_immediate_expense_payment_record(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense: Expense,
) -> ExpensePayment:
    if expense.payment_account_id is None:
        raise ExpenseJournalPostingError("Cash expenses require a payment account.")
    if expense.journal_entry_id is None:
        raise ExpenseJournalPostingError("Cash expense journal must be posted before recording payment.")

    payment = ExpensePayment(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        vendor_id=expense.vendor_id,
        payment_account_id=expense.payment_account_id,
        journal_entry_id=expense.journal_entry_id,
        payment_date=expense.expense_date,
        amount=money(expense.total_amount),
        unapplied_amount=Decimal("0.00"),
        payment_mode="cash" if expense.expense_type == "cash_expense" else "other",
        reference_number=expense.reference_number,
        status="paid",
        notes=expense.notes,
    )
    session.add(payment)
    session.flush()
    session.add(
        ExpensePaymentAllocation(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            expense_payment_id=payment.id,
            expense_id=expense.id,
            allocated_amount=money(expense.total_amount),
            status="active",
        )
    )
    return payment


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
        raise ExpenseSocietyNotFoundError("Society not found.")


def get_active_category(
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
            ExpenseCategory.status == "active",
        )
    )
    if category is None:
        raise ExpenseReferenceInvalidError("Expense category must be active and belong to this society.")
    return category


def ensure_vendor_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_id: uuid.UUID | None,
) -> None:
    if vendor_id is None:
        return
    vendor = session.scalar(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.tenant_id == tenant_context.tenant_id,
            Vendor.society_id == society_id,
            Vendor.status == "active",
        )
    )
    if vendor is None:
        raise ExpenseReferenceInvalidError("Vendor must be active and belong to this society.")


def ensure_payment_account_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payment_account_id: uuid.UUID | None,
) -> None:
    if payment_account_id is None:
        return
    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == payment_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "asset",
            ChartOfAccount.status == "active",
        )
    )
    if account is None:
        raise ExpenseReferenceInvalidError("Payment account must be an active asset account.")


def ensure_vendor_bill_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_id: uuid.UUID | None,
    vendor_bill_number: str | None,
    existing_expense_id: uuid.UUID | None = None,
) -> None:
    if vendor_id is None or vendor_bill_number is None:
        return
    statement = select(Expense).where(
        Expense.tenant_id == tenant_context.tenant_id,
        Expense.society_id == society_id,
        Expense.vendor_id == vendor_id,
        Expense.vendor_bill_number == vendor_bill_number,
    )
    if existing_expense_id is not None:
        statement = statement.where(Expense.id != existing_expense_id)
    if session.scalar(statement) is not None:
        raise ExpenseAlreadyExistsError("Vendor bill number already exists for this vendor.")


def list_expenses(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_id: uuid.UUID | None = None,
    expense_category_id: uuid.UUID | None = None,
    expense_type: str | None = None,
    status: str | None = None,
    payment_status: str | None = None,
    expense_date_from: date | None = None,
    expense_date_to: date | None = None,
) -> list[Expense]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    statement = build_expense_list_statement(
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_id=vendor_id,
        expense_category_id=expense_category_id,
        expense_type=expense_type,
        status=status,
        payment_status=payment_status,
        expense_date_from=expense_date_from,
        expense_date_to=expense_date_to,
    )
    return list(session.scalars(apply_expense_sort(statement, sort_by="expense_date", sort_direction="desc")))


def build_expense_list_statement(
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_id: uuid.UUID | None = None,
    expense_category_id: uuid.UUID | None = None,
    expense_type: str | None = None,
    status: str | None = None,
    payment_status: str | None = None,
    expense_date_from: date | None = None,
    expense_date_to: date | None = None,
) -> Select[tuple[Expense]]:
    statement = select(Expense).where(
        Expense.tenant_id == tenant_context.tenant_id,
        Expense.society_id == society_id,
    )
    if vendor_id is not None:
        statement = statement.where(Expense.vendor_id == vendor_id)
    if expense_category_id is not None:
        statement = statement.where(Expense.expense_category_id == expense_category_id)
    if expense_type:
        statement = statement.where(Expense.expense_type == expense_type)
    if status:
        statement = statement.where(Expense.status == status)
    if payment_status:
        statement = statement.where(Expense.payment_status == payment_status)
    if expense_date_from is not None:
        statement = statement.where(Expense.expense_date >= expense_date_from)
    if expense_date_to is not None:
        statement = statement.where(Expense.expense_date <= expense_date_to)
    return statement


def apply_expense_sort(
    statement: Select[tuple[Expense]],
    *,
    sort_by: str,
    sort_direction: str,
) -> Select[tuple[Expense]]:
    sortable_columns = {
        "expense_date": Expense.expense_date,
        "due_date": Expense.due_date,
        "description": Expense.description,
        "total_amount": Expense.total_amount,
        "amount_due": Expense.amount_due,
        "status": Expense.status,
        "payment_status": Expense.payment_status,
        "created_at": Expense.created_at,
    }
    sort_column = sortable_columns.get(sort_by, Expense.expense_date)
    ordered_column = sort_column.asc() if sort_direction == "asc" else sort_column.desc()
    return statement.order_by(ordered_column, Expense.created_at.desc())


def list_expenses_paginated(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_id: uuid.UUID | None = None,
    expense_category_id: uuid.UUID | None = None,
    expense_type: str | None = None,
    status: str | None = None,
    payment_status: str | None = None,
    expense_date_from: date | None = None,
    expense_date_to: date | None = None,
    sort_by: str = "expense_date",
    sort_direction: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Expense], int]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    statement = build_expense_list_statement(
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_id=vendor_id,
        expense_category_id=expense_category_id,
        expense_type=expense_type,
        status=status,
        payment_status=payment_status,
        expense_date_from=expense_date_from,
        expense_date_to=expense_date_to,
    )
    total_items = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = list(
        session.scalars(
            apply_expense_sort(statement, sort_by=sort_by, sort_direction=sort_direction)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return rows, total_items


def get_expense_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense_id: uuid.UUID,
) -> Expense:
    expense = session.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.tenant_id == tenant_context.tenant_id,
            Expense.society_id == society_id,
        )
    )
    if expense is None:
        raise ExpenseNotFoundError("Expense not found.")
    return expense


def create_expense(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ExpenseCreate,
    actor: User,
) -> Expense:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    category = get_active_category(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        category_id=payload.expense_category_id,
    )
    ensure_vendor_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_id=payload.vendor_id,
    )
    ensure_payment_account_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payment_account_id=payload.payment_account_id,
    )
    if payload.expense_type == "cash_expense" and payload.payment_account_id is None:
        raise ExpenseReferenceInvalidError("Cash expenses require a payment account.")
    ensure_vendor_bill_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_id=payload.vendor_id,
        vendor_bill_number=payload.vendor_bill_number,
    )
    total_amount = money(payload.amount + payload.tax_amount)
    is_cash_posted = payload.expense_type == "cash_expense" or (
        payload.expense_type == "other" and payload.payment_account_id is not None
    )
    expense = Expense(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        vendor_id=payload.vendor_id,
        expense_category_id=category.id,
        expense_account_id=category.expense_account_id,
        payment_account_id=payload.payment_account_id,
        expense_type=payload.expense_type,
        vendor_bill_number=payload.vendor_bill_number,
        reference_number=payload.reference_number,
        expense_date=payload.expense_date,
        due_date=payload.due_date,
        description=payload.description,
        amount=money(payload.amount),
        tax_amount=money(payload.tax_amount),
        total_amount=total_amount,
        amount_paid=total_amount if is_cash_posted else Decimal("0.00"),
        amount_due=Decimal("0.00") if is_cash_posted else total_amount,
        status="recorded",
        payment_status="paid" if is_cash_posted else "unpaid",
        notes=payload.notes,
    )
    session.add(expense)
    session.flush()
    post_expense_journal(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense=expense,
    )
    if is_cash_posted:
        create_immediate_expense_payment_record(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            expense=expense,
        )
    record_audit_log(
        session,
        action="expense.created",
        entity_type="Expense",
        entity_id=expense.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense recorded: {expense.description}",
        metadata={
            "society_id": str(society_id),
            "vendor_id": str(expense.vendor_id) if expense.vendor_id else None,
            "expense_category_id": str(expense.expense_category_id),
            "total_amount": str(expense.total_amount),
        },
    )
    session.commit()
    session.refresh(expense)
    return expense


def update_expense(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    actor: User,
) -> Expense:
    expense = get_expense_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense_id=expense_id,
    )
    if expense.status == "cancelled" or expense.amount_paid > 0:
        raise ExpenseCancellationInvalidError("Only unpaid, non-cancelled expenses can be edited.")
    category = get_active_category(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        category_id=payload.expense_category_id,
    )
    ensure_vendor_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_id=payload.vendor_id,
    )
    ensure_payment_account_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payment_account_id=payload.payment_account_id,
    )
    ensure_vendor_bill_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_id=payload.vendor_id,
        vendor_bill_number=payload.vendor_bill_number,
        existing_expense_id=expense.id,
    )
    previous_values = {
        "vendor_id": str(expense.vendor_id) if expense.vendor_id else None,
        "expense_category_id": str(expense.expense_category_id),
        "total_amount": str(expense.total_amount),
        "status": expense.status,
    }
    total_amount = money(payload.amount + payload.tax_amount)
    reverse_existing_expense_journal(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense=expense,
    )
    is_cash_posted = payload.expense_type == "cash_expense" or (
        payload.expense_type == "other" and payload.payment_account_id is not None
    )
    expense.vendor_id = payload.vendor_id
    expense.expense_category_id = category.id
    expense.expense_account_id = category.expense_account_id
    expense.payment_account_id = payload.payment_account_id
    expense.expense_type = payload.expense_type
    expense.vendor_bill_number = payload.vendor_bill_number
    expense.reference_number = payload.reference_number
    expense.expense_date = payload.expense_date
    expense.due_date = payload.due_date
    expense.description = payload.description
    expense.amount = money(payload.amount)
    expense.tax_amount = money(payload.tax_amount)
    expense.total_amount = total_amount
    expense.amount_paid = total_amount if is_cash_posted else Decimal("0.00")
    expense.amount_due = Decimal("0.00") if is_cash_posted else total_amount
    expense.payment_status = "paid" if is_cash_posted else "unpaid"
    expense.notes = payload.notes
    post_expense_journal(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense=expense,
    )
    if is_cash_posted:
        create_immediate_expense_payment_record(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            expense=expense,
        )
    record_audit_log(
        session,
        action="expense.updated",
        entity_type="Expense",
        entity_id=expense.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense updated: {expense.description}",
        metadata={
            "society_id": str(society_id),
            "previous": previous_values,
            "current": {
                "vendor_id": str(expense.vendor_id) if expense.vendor_id else None,
                "expense_category_id": str(expense.expense_category_id),
                "total_amount": str(expense.total_amount),
                "status": expense.status,
            },
        },
    )
    session.commit()
    session.refresh(expense)
    return expense


def approve_expense(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense_id: uuid.UUID,
    actor: User,
) -> Expense:
    expense = get_expense_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense_id=expense_id,
    )
    if expense.status == "cancelled":
        raise ExpenseCancellationInvalidError("Cancelled expenses cannot be approved.")
    expense.status = "approved"
    record_audit_log(
        session,
        action="expense.approved",
        entity_type="Expense",
        entity_id=expense.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense approved: {expense.description}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(expense)
    return expense


def cancel_expense(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense_id: uuid.UUID,
    reason: str,
    actor: User,
) -> Expense:
    expense = get_expense_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense_id=expense_id,
    )
    if expense.amount_paid > 0:
        raise ExpenseCancellationInvalidError("Paid expenses cannot be cancelled directly.")
    reverse_existing_expense_journal(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        expense=expense,
    )
    expense.status = "cancelled"
    expense.amount_due = Decimal("0.00")
    expense.payment_status = "paid"
    record_audit_log(
        session,
        action="expense.cancelled",
        entity_type="Expense",
        entity_id=expense.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense cancelled: {expense.description}",
        metadata={"society_id": str(society_id), "reason": reason},
    )
    session.commit()
    session.refresh(expense)
    return expense
