import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ChartOfAccount,
    Flat,
    Invoice,
    JournalEntry,
    JournalLine,
    LateFeeApplication,
    Owner,
    Payment,
    PaymentAllocation,
    Society,
    User,
)
from app.schemas.payment import PaymentAllocationCreate, PaymentCreate, PaymentReverseRequest
from app.services.audit import record_audit_log
from app.services.late_fees import auto_cancel_invalid_unpaid_penalties
from app.tenants.context import TenantContext


class PaymentSocietyNotFoundError(Exception):
    pass


class PaymentReferenceInvalidError(Exception):
    pass


class PaymentAllocationInvalidError(Exception):
    pass


class PaymentInvalidStateError(Exception):
    pass


class PaymentJournalPostingError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def post_payment_journal(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payment: Payment,
) -> JournalEntry:
    if payment.deposit_account_id is None:
        raise PaymentJournalPostingError("Deposit account is required before posting a payment journal.")
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise PaymentSocietyNotFoundError("Society not found.")
    allocated_amount = money(payment.amount - payment.unapplied_amount)
    unapplied_amount = money(payment.unapplied_amount)
    if allocated_amount > Decimal("0.00") and society.receivable_account_id is None:
        raise PaymentJournalPostingError("Configure the society receivable account before recording payments.")
    if unapplied_amount > Decimal("0.00") and society.member_advance_account_id is None:
        raise PaymentJournalPostingError(
            "Configure the society member advance account before recording advance payments."
        )

    account_ids = [payment.deposit_account_id]
    if allocated_amount > Decimal("0.00") and society.receivable_account_id is not None:
        account_ids.append(society.receivable_account_id)
    if unapplied_amount > Decimal("0.00") and society.member_advance_account_id is not None:
        account_ids.append(society.member_advance_account_id)
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
        raise PaymentJournalPostingError("Payment posting accounts must be active chart accounts.")
    if accounts[payment.deposit_account_id].account_type != "asset":
        raise PaymentJournalPostingError("Payment deposit account must be an active asset account.")
    if (
        allocated_amount > Decimal("0.00")
        and society.receivable_account_id is not None
        and accounts[society.receivable_account_id].account_type != "asset"
    ):
        raise PaymentJournalPostingError("Society receivable account must be an active asset account.")
    if (
        unapplied_amount > Decimal("0.00")
        and society.member_advance_account_id is not None
        and accounts[society.member_advance_account_id].account_type != "liability"
    ):
        raise PaymentJournalPostingError("Society member advance account must be an active liability account.")

    journal_entry = JournalEntry(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        journal_date=payment.payment_date,
        source_type="payment",
        source_id=payment.id,
        reference_number=payment.reference_number,
        description=f"Payment received: {payment.amount}",
        status="posted",
        notes=payment.notes,
    )
    session.add(journal_entry)
    session.flush()

    deposit_account = accounts[payment.deposit_account_id]
    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=deposit_account.id,
            line_number=1,
            description=f"Deposit to {deposit_account.account_name}",
            debit_amount=money(payment.amount),
            credit_amount=Decimal("0.00"),
        )
    )
    line_number = 2
    if allocated_amount > Decimal("0.00") and society.receivable_account_id is not None:
        receivable_account = accounts[society.receivable_account_id]
        session.add(
            JournalLine(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                journal_entry_id=journal_entry.id,
                account_id=receivable_account.id,
                line_number=line_number,
                description=f"Receivable settlement: {receivable_account.account_name}",
                debit_amount=Decimal("0.00"),
                credit_amount=allocated_amount,
            )
        )
        line_number += 1
    if unapplied_amount > Decimal("0.00") and society.member_advance_account_id is not None:
        member_advance_account = accounts[society.member_advance_account_id]
        session.add(
            JournalLine(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                journal_entry_id=journal_entry.id,
                account_id=member_advance_account.id,
                line_number=line_number,
                description=f"Member advance: {member_advance_account.account_name}",
                debit_amount=Decimal("0.00"),
                credit_amount=unapplied_amount,
            )
        )
    payment.journal_entry_id = journal_entry.id
    return journal_entry


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
        raise PaymentSocietyNotFoundError("Society not found.")


def list_payments(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[Payment]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(Payment)
            .where(
                Payment.tenant_id == tenant_context.tenant_id,
                Payment.society_id == society_id,
            )
            .order_by(Payment.payment_date.desc(), Payment.created_at.desc())
        )
    )


def list_payment_allocations(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payment_id: uuid.UUID,
) -> list[PaymentAllocation]:
    return list(
        session.scalars(
            select(PaymentAllocation)
            .where(
                PaymentAllocation.tenant_id == tenant_context.tenant_id,
                PaymentAllocation.society_id == society_id,
                PaymentAllocation.payment_id == payment_id,
            )
            .order_by(PaymentAllocation.created_at)
        )
    )


def ensure_payment_references(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: PaymentCreate,
) -> None:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    flat = session.scalar(
        select(Flat).where(
            Flat.id == payload.flat_id,
            Flat.tenant_id == tenant_context.tenant_id,
            Flat.society_id == society_id,
            Flat.status == "active",
        )
    )
    if flat is None:
        raise PaymentReferenceInvalidError("Flat must be active and belong to this society.")

    if payload.owner_id is not None:
        owner = session.scalar(
            select(Owner).where(
                Owner.id == payload.owner_id,
                Owner.tenant_id == tenant_context.tenant_id,
                Owner.society_id == society_id,
                Owner.status == "active",
            )
        )
        if owner is None:
            raise PaymentReferenceInvalidError("Owner must be active and belong to this society.")

    if payload.deposit_account_id is None:
        raise PaymentReferenceInvalidError("Deposit account is required.")

    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == payload.deposit_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "asset",
            ChartOfAccount.status == "active",
        )
    )
    if account is None:
        raise PaymentReferenceInvalidError("Deposit account must be an active asset account.")


def load_allocated_invoices(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    allocations: list[PaymentAllocationCreate],
) -> dict[uuid.UUID, Invoice]:
    invoice_ids = [allocation.invoice_id for allocation in allocations]
    if not invoice_ids:
        return {}
    invoices = {
        invoice.id: invoice
        for invoice in session.scalars(
            select(Invoice)
            .where(
                Invoice.id.in_(invoice_ids),
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
                Invoice.flat_id == flat_id,
                Invoice.status.not_in(["cancelled", "paid"]),
            )
            .with_for_update()
        )
    }
    if set(invoice_ids) != set(invoices):
        raise PaymentAllocationInvalidError("All allocated invoices must be open and belong to the selected flat.")
    return invoices


def build_oldest_first_allocations(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    amount: Decimal,
    payment_date: date,
) -> list[PaymentAllocationCreate]:
    remaining_amount = money(amount)
    if remaining_amount <= Decimal("0.00"):
        return []

    open_invoices = list(
        session.scalars(
            select(Invoice)
            .where(
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
                Invoice.flat_id == flat_id,
                Invoice.status.not_in(["cancelled", "paid"]),
                Invoice.amount_due > 0,
            )
            .order_by(Invoice.due_date, Invoice.invoice_date, Invoice.invoice_number)
            .with_for_update()
        )
    )

    if not open_invoices:
        return []

    open_invoice_ids = {invoice.id for invoice in open_invoices}
    penalty_applications = {
        application.penalty_invoice_id: application
        for application in session.scalars(
            select(LateFeeApplication).where(
                LateFeeApplication.tenant_id == tenant_context.tenant_id,
                LateFeeApplication.society_id == society_id,
                LateFeeApplication.penalty_invoice_id.in_(open_invoice_ids),
                LateFeeApplication.status == "active",
            )
        )
    }
    original_invoices = {invoice.id: invoice for invoice in open_invoices}
    missing_original_invoice_ids = {
        application.original_invoice_id
        for application in penalty_applications.values()
        if application.original_invoice_id not in original_invoices
    }
    if missing_original_invoice_ids:
        original_invoices.update(
            {
                invoice.id: invoice
                for invoice in session.scalars(
                    select(Invoice).where(
                        Invoice.id.in_(missing_original_invoice_ids),
                        Invoice.tenant_id == tenant_context.tenant_id,
                        Invoice.society_id == society_id,
                    )
                )
            }
        )

    allocations: list[PaymentAllocationCreate] = []
    simulated_allocations: dict[uuid.UUID, Decimal] = {}

    def allocate_invoice(invoice: Invoice) -> None:
        nonlocal remaining_amount
        if remaining_amount <= Decimal("0.00"):
            return
        allocated_amount = min(remaining_amount, money(invoice.amount_due))
        allocations.append(
            PaymentAllocationCreate(
                invoice_id=invoice.id,
                allocated_amount=allocated_amount,
            )
        )
        simulated_allocations[invoice.id] = money(
            simulated_allocations.get(invoice.id, Decimal("0.00")) + allocated_amount
        )
        remaining_amount = money(remaining_amount - allocated_amount)

    for invoice in open_invoices:
        if invoice.id not in penalty_applications:
            allocate_invoice(invoice)

    for invoice in open_invoices:
        application = penalty_applications.get(invoice.id)
        if application is None:
            continue
        original_invoice = original_invoices.get(application.original_invoice_id)
        original_paid_after_this_payment = money(
            (original_invoice.amount_paid if original_invoice is not None else Decimal("0.00"))
            + simulated_allocations.get(application.original_invoice_id, Decimal("0.00"))
        )
        if (
            original_invoice is not None
            and payment_date < application.applied_as_of_date
            and original_paid_after_this_payment >= original_invoice.total_amount
        ):
            continue
        allocate_invoice(invoice)
    return allocations


def update_invoice_after_allocation(invoice: Invoice, allocated_amount: Decimal) -> None:
    if allocated_amount > invoice.amount_due:
        raise PaymentAllocationInvalidError("Allocation cannot exceed invoice balance.")
    invoice.amount_paid = money(invoice.amount_paid + allocated_amount)
    invoice.amount_due = money(invoice.amount_due - allocated_amount)
    invoice.status = "paid" if invoice.amount_due == Decimal("0.00") else "partially_paid"


def update_invoice_after_payment_reversal(invoice: Invoice, reversed_amount: Decimal) -> None:
    if reversed_amount > invoice.amount_paid:
        raise PaymentAllocationInvalidError("Reversal cannot exceed invoice paid amount.")
    invoice.amount_paid = money(invoice.amount_paid - reversed_amount)
    invoice.amount_due = money(invoice.amount_due + reversed_amount)
    if invoice.amount_paid == Decimal("0.00"):
        invoice.status = "issued"
    elif invoice.amount_due == Decimal("0.00"):
        invoice.status = "paid"
    else:
        invoice.status = "partially_paid"


def create_payment(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: PaymentCreate,
    actor: User,
) -> Payment:
    ensure_payment_references(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    payment_amount = money(payload.amount)
    allocations = payload.allocations or build_oldest_first_allocations(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=payload.flat_id,
        amount=payment_amount,
        payment_date=payload.payment_date,
    )
    invoices = load_allocated_invoices(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=payload.flat_id,
        allocations=allocations,
    )
    total_allocated = money(sum((allocation.allocated_amount for allocation in allocations), Decimal("0.00")))

    payment = Payment(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        flat_id=payload.flat_id,
        owner_id=payload.owner_id,
        deposit_account_id=payload.deposit_account_id,
        payment_date=payload.payment_date,
        amount=payment_amount,
        unapplied_amount=money(payment_amount - total_allocated),
        payment_mode=payload.payment_mode,
        reference_number=payload.reference_number,
        status="received",
        notes=payload.notes,
    )
    session.add(payment)
    session.flush()

    for allocation in allocations:
        allocated_amount = money(allocation.allocated_amount)
        invoice = invoices[allocation.invoice_id]
        update_invoice_after_allocation(invoice, allocated_amount)
        session.add(
            PaymentAllocation(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                payment_id=payment.id,
                invoice_id=invoice.id,
                allocated_amount=allocated_amount,
                status="active",
            )
        )

    session.flush()
    auto_cancelled_penalty_invoice_ids = auto_cancel_invalid_unpaid_penalties(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        original_invoice_ids=list(invoices),
        actor=actor,
    )

    post_payment_journal(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payment=payment,
    )

    record_audit_log(
        session,
        action="payment.received",
        entity_type="Payment",
        entity_id=payment.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Payment received: {payment.amount}",
        metadata={
            "society_id": str(society_id),
            "flat_id": str(payload.flat_id),
            "allocated_amount": str(total_allocated),
            "unapplied_amount": str(payment.unapplied_amount),
            "auto_cancelled_penalty_invoice_ids": [
                str(invoice_id) for invoice_id in auto_cancelled_penalty_invoice_ids
            ],
        },
    )
    session.commit()
    session.refresh(payment)
    return payment


def reverse_payment(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: PaymentReverseRequest,
    actor: User,
) -> Payment:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    payment = session.scalar(
        select(Payment)
        .where(
            Payment.id == payment_id,
            Payment.tenant_id == tenant_context.tenant_id,
            Payment.society_id == society_id,
        )
        .with_for_update()
    )
    if payment is None:
        raise PaymentReferenceInvalidError("Payment not found.")
    if payment.status == "reversed":
        raise PaymentInvalidStateError("Payment is already reversed.")

    allocations = list(
        session.scalars(
            select(PaymentAllocation)
            .where(
                PaymentAllocation.tenant_id == tenant_context.tenant_id,
                PaymentAllocation.society_id == society_id,
                PaymentAllocation.payment_id == payment.id,
                PaymentAllocation.status == "active",
            )
            .with_for_update()
        )
    )
    invoice_ids = [allocation.invoice_id for allocation in allocations]
    invoices = {
        invoice.id: invoice
        for invoice in session.scalars(
            select(Invoice)
            .where(
                Invoice.id.in_(invoice_ids),
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
            )
            .with_for_update()
        )
    }

    for allocation in allocations:
        invoice = invoices.get(allocation.invoice_id)
        if invoice is None or invoice.status == "cancelled":
            raise PaymentAllocationInvalidError("Allocated invoice is not available for reversal.")
        update_invoice_after_payment_reversal(invoice, money(allocation.allocated_amount))
        allocation.status = "reversed"

    payment.status = "reversed"
    payment.unapplied_amount = Decimal("0.00")
    if payment.journal_entry_id is not None:
        journal_entry = session.scalar(
            select(JournalEntry).where(
                JournalEntry.id == payment.journal_entry_id,
                JournalEntry.tenant_id == tenant_context.tenant_id,
                JournalEntry.society_id == society_id,
            )
        )
        if journal_entry is not None:
            journal_entry.status = "reversed"
    record_audit_log(
        session,
        action="payment.reversed",
        entity_type="Payment",
        entity_id=payment.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Payment reversed: {payment.amount}",
        metadata={
            "society_id": str(society_id),
            "flat_id": str(payment.flat_id),
            "reason": payload.reason,
            "reversed_allocations": [
                {
                    "invoice_id": str(allocation.invoice_id),
                    "allocated_amount": str(allocation.allocated_amount),
                }
                for allocation in allocations
            ],
        },
    )
    session.commit()
    session.refresh(payment)
    return payment
