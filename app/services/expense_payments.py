import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, Expense, ExpensePayment, ExpensePaymentAllocation, JournalEntry, JournalLine, Society, User, Vendor
from app.schemas.expense_payment import ExpensePaymentAllocateRequest, ExpensePaymentCreate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class ExpensePaymentSocietyNotFoundError(Exception):
    pass


class ExpensePaymentReferenceInvalidError(Exception):
    pass


class ExpensePaymentAllocationInvalidError(Exception):
    pass


class ExpensePaymentJournalPostingError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def post_expense_payment_journal(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payment: ExpensePayment,
) -> JournalEntry:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise ExpensePaymentSocietyNotFoundError("Society not found.")
    if society.payable_account_id is None:
        raise ExpensePaymentJournalPostingError("Configure the society payable account before recording expense payments.")

    account_ids = [society.payable_account_id, payment.payment_account_id]
    accounts = {
        account.id: account
        for account in session.scalars(
            select(ChartOfAccount).where(
                ChartOfAccount.id.in_(account_ids),
                ChartOfAccount.tenant_id == tenant_context.tenant_id,
                ChartOfAccount.society_id == society_id,
                ChartOfAccount.status == "active",
            )
        )
    }
    if set(account_ids) != set(accounts):
        raise ExpensePaymentJournalPostingError("Payable and payment accounts must be active accounts in this society.")

    payable_account = accounts[society.payable_account_id]
    payment_account = accounts[payment.payment_account_id]
    if payable_account.account_type != "liability":
        raise ExpensePaymentJournalPostingError("Society payable account must be an active liability account.")
    if payment_account.account_type != "asset":
        raise ExpensePaymentJournalPostingError("Expense payment account must be an active asset account.")

    journal_entry = JournalEntry(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        journal_date=payment.payment_date,
        source_type="expense_payment",
        source_id=payment.id,
        reference_number=payment.reference_number,
        description=f"Expense payment recorded: {payment.amount}",
        status="posted",
        notes=payment.notes,
    )
    session.add(journal_entry)
    session.flush()

    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=payable_account.id,
            line_number=1,
            description=f"Payable settlement: {payable_account.account_name}",
            debit_amount=money(payment.amount),
            credit_amount=Decimal("0.00"),
        )
    )
    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=payment_account.id,
            line_number=2,
            description=f"Payment from {payment_account.account_name}",
            debit_amount=Decimal("0.00"),
            credit_amount=money(payment.amount),
        )
    )
    payment.journal_entry_id = journal_entry.id
    return journal_entry


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise ExpensePaymentSocietyNotFoundError("Society not found.")


def list_expense_payments(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[ExpensePayment]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(ExpensePayment)
            .where(
                ExpensePayment.tenant_id == tenant_context.tenant_id,
                ExpensePayment.society_id == society_id,
            )
            .order_by(ExpensePayment.payment_date.desc(), ExpensePayment.created_at.desc())
        )
    )


def list_expense_payment_allocations(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense_payment_id: uuid.UUID,
) -> list[ExpensePaymentAllocation]:
    return list(
        session.scalars(
            select(ExpensePaymentAllocation)
            .where(
                ExpensePaymentAllocation.tenant_id == tenant_context.tenant_id,
                ExpensePaymentAllocation.society_id == society_id,
                ExpensePaymentAllocation.expense_payment_id == expense_payment_id,
            )
            .order_by(ExpensePaymentAllocation.created_at)
        )
    )


def ensure_references(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ExpensePaymentCreate,
) -> None:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    if payload.vendor_id is not None:
        vendor = session.scalar(
            select(Vendor).where(
                Vendor.id == payload.vendor_id,
                Vendor.tenant_id == tenant_context.tenant_id,
                Vendor.society_id == society_id,
                Vendor.status == "active",
            )
        )
        if vendor is None:
            raise ExpensePaymentReferenceInvalidError("Vendor must be active and belong to this society.")
    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == payload.payment_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "asset",
            ChartOfAccount.status == "active",
        )
    )
    if account is None:
        raise ExpensePaymentReferenceInvalidError("Payment account must be an active asset account.")


def load_allocated_expenses(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ExpensePaymentCreate | ExpensePaymentAllocateRequest,
    vendor_id: uuid.UUID | None = None,
) -> dict[uuid.UUID, Expense]:
    expense_ids = [allocation.expense_id for allocation in payload.allocations]
    if not expense_ids:
        return {}
    expenses = {
        expense.id: expense
        for expense in session.scalars(
            select(Expense)
            .where(
                Expense.id.in_(expense_ids),
                Expense.tenant_id == tenant_context.tenant_id,
                Expense.society_id == society_id,
                Expense.status != "cancelled",
                Expense.payment_status != "paid",
            )
            .with_for_update()
        )
    }
    if set(expense_ids) != set(expenses):
        raise ExpensePaymentAllocationInvalidError("All allocated expenses must be open and belong to this society.")
    selected_vendor_id = getattr(payload, "vendor_id", vendor_id)
    if selected_vendor_id is not None:
        for expense in expenses.values():
            if expense.vendor_id != selected_vendor_id:
                raise ExpensePaymentAllocationInvalidError("Allocated expenses must belong to the selected vendor.")
    return expenses


def update_expense_after_payment(expense: Expense, allocated_amount: Decimal) -> None:
    if allocated_amount > expense.amount_due:
        raise ExpensePaymentAllocationInvalidError("Allocation cannot exceed expense balance.")
    expense.amount_paid = money(expense.amount_paid + allocated_amount)
    expense.amount_due = money(expense.amount_due - allocated_amount)
    if expense.amount_due == Decimal("0.00"):
        expense.payment_status = "paid"
    elif expense.amount_paid > Decimal("0.00"):
        expense.payment_status = "partially_paid"
    else:
        expense.payment_status = "unpaid"


def create_expense_payment(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ExpensePaymentCreate,
    actor: User,
) -> ExpensePayment:
    ensure_references(session, tenant_context=tenant_context, society_id=society_id, payload=payload)
    expenses = load_allocated_expenses(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    total_allocated = money(sum((allocation.allocated_amount for allocation in payload.allocations), Decimal("0.00")))
    payment_amount = money(payload.amount)
    payment = ExpensePayment(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        vendor_id=payload.vendor_id,
        payment_account_id=payload.payment_account_id,
        payment_date=payload.payment_date,
        amount=payment_amount,
        unapplied_amount=money(payment_amount - total_allocated),
        payment_mode=payload.payment_mode,
        reference_number=payload.reference_number,
        status="paid",
        notes=payload.notes,
    )
    session.add(payment)
    session.flush()
    for allocation in payload.allocations:
        allocated_amount = money(allocation.allocated_amount)
        expense = expenses[allocation.expense_id]
        update_expense_after_payment(expense, allocated_amount)
        session.add(
            ExpensePaymentAllocation(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                expense_payment_id=payment.id,
                expense_id=expense.id,
                allocated_amount=allocated_amount,
                status="active",
            )
        )
    post_expense_payment_journal(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payment=payment,
    )
    record_audit_log(
        session,
        action="expense_payment.created",
        entity_type="ExpensePayment",
        entity_id=payment.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense payment recorded: {payment.amount}",
        metadata={
            "society_id": str(society_id),
            "vendor_id": str(payment.vendor_id) if payment.vendor_id else None,
            "allocated_amount": str(total_allocated),
            "unapplied_amount": str(payment.unapplied_amount),
        },
    )
    session.commit()
    session.refresh(payment)
    return payment


def allocate_existing_expense_payment(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    expense_payment_id: uuid.UUID,
    payload: ExpensePaymentAllocateRequest,
    actor: User,
) -> ExpensePayment:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    payment = session.scalar(
        select(ExpensePayment)
        .where(
            ExpensePayment.id == expense_payment_id,
            ExpensePayment.tenant_id == tenant_context.tenant_id,
            ExpensePayment.society_id == society_id,
            ExpensePayment.status == "paid",
        )
        .with_for_update()
    )
    if payment is None:
        raise ExpensePaymentReferenceInvalidError("Expense payment not found.")
    if payment.unapplied_amount <= Decimal("0.00"):
        raise ExpensePaymentAllocationInvalidError("Expense payment has no unapplied amount.")

    expenses = load_allocated_expenses(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        vendor_id=payment.vendor_id,
    )
    total_allocated = money(sum((allocation.allocated_amount for allocation in payload.allocations), Decimal("0.00")))
    if total_allocated <= Decimal("0.00"):
        raise ExpensePaymentAllocationInvalidError("Allocation amount must be greater than zero.")
    if total_allocated > payment.unapplied_amount:
        raise ExpensePaymentAllocationInvalidError("Allocation cannot exceed unapplied payment amount.")

    for allocation in payload.allocations:
        allocated_amount = money(allocation.allocated_amount)
        expense = expenses[allocation.expense_id]
        update_expense_after_payment(expense, allocated_amount)
        session.add(
            ExpensePaymentAllocation(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                expense_payment_id=payment.id,
                expense_id=expense.id,
                allocated_amount=allocated_amount,
                status="active",
            )
        )
    payment.unapplied_amount = money(payment.unapplied_amount - total_allocated)
    record_audit_log(
        session,
        action="expense_payment.allocated",
        entity_type="ExpensePayment",
        entity_id=payment.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Expense payment allocated: {total_allocated}",
        metadata={
            "society_id": str(society_id),
            "allocated_amount": str(total_allocated),
            "unapplied_amount": str(payment.unapplied_amount),
        },
    )
    session.commit()
    session.refresh(payment)
    return payment
