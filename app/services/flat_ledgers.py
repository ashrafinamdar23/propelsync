import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Flat, Invoice, Payment
from app.schemas.flat_ledger import FlatLedgerLineRead, FlatLedgerRead
from app.tenants.context import TenantContext


class FlatLedgerSocietyNotFoundError(Exception):
    pass


class FlatLedgerFlatNotFoundError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def get_flat_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
) -> Flat:
    flat = session.scalar(
        select(Flat).where(
            Flat.id == flat_id,
            Flat.tenant_id == tenant_context.tenant_id,
            Flat.society_id == society_id,
        )
    )
    if flat is None:
        raise FlatLedgerFlatNotFoundError("Flat not found.")
    return flat


def load_flat_events(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    before_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[tuple[date, int, str, Invoice | Payment]]:
    invoice_query = select(Invoice).where(
        Invoice.tenant_id == tenant_context.tenant_id,
        Invoice.society_id == society_id,
        Invoice.flat_id == flat_id,
        Invoice.status != "cancelled",
    )
    payment_query = select(Payment).where(
        Payment.tenant_id == tenant_context.tenant_id,
        Payment.society_id == society_id,
        Payment.flat_id == flat_id,
        Payment.status == "received",
    )
    if before_date is not None:
        invoice_query = invoice_query.where(Invoice.invoice_date < before_date)
        payment_query = payment_query.where(Payment.payment_date < before_date)
    if date_from is not None:
        invoice_query = invoice_query.where(Invoice.invoice_date >= date_from)
        payment_query = payment_query.where(Payment.payment_date >= date_from)
    if date_to is not None:
        invoice_query = invoice_query.where(Invoice.invoice_date <= date_to)
        payment_query = payment_query.where(Payment.payment_date <= date_to)

    events: list[tuple[date, int, str, Invoice | Payment]] = []
    events.extend((invoice.invoice_date, 0, invoice.invoice_number, invoice) for invoice in session.scalars(invoice_query))
    events.extend(
        (
            payment.payment_date,
            1,
            payment.reference_number or "",
            payment,
        )
        for payment in session.scalars(payment_query)
    )
    return sorted(events, key=lambda item: (item[0], item[1], item[2]))


def event_amounts(event: Invoice | Payment) -> tuple[Decimal, Decimal]:
    if isinstance(event, Invoice):
        return money(event.total_amount), Decimal("0.00")
    return Decimal("0.00"), money(event.amount)


def build_flat_ledger(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    flat: Flat,
    date_from: date | None,
    date_to: date | None,
    opening_events: list[tuple[date, int, str, Invoice | Payment]],
    movement_events: list[tuple[date, int, str, Invoice | Payment]],
) -> FlatLedgerRead:
    opening_balance = money(
        sum((event_amounts(event)[0] - event_amounts(event)[1] for *_prefix, event in opening_events), Decimal("0.00"))
    )
    running_balance = opening_balance
    total_debits = Decimal("0.00")
    total_credits = Decimal("0.00")
    lines: list[FlatLedgerLineRead] = []

    for line_date, _order, _key, event in movement_events:
        debit_amount, credit_amount = event_amounts(event)
        total_debits = money(total_debits + debit_amount)
        total_credits = money(total_credits + credit_amount)
        running_balance = money(running_balance + debit_amount - credit_amount)
        if isinstance(event, Invoice):
            source_type = "invoice"
            reference_number = event.invoice_number
            description = f"Invoice {event.invoice_number}"
        else:
            source_type = "payment"
            reference_number = event.reference_number
            description = f"Payment received by {event.payment_mode}"
        lines.append(
            FlatLedgerLineRead(
                line_date=line_date,
                source_type=source_type,
                source_id=event.id,
                reference_number=reference_number,
                description=description,
                debit_amount=debit_amount,
                credit_amount=credit_amount,
                running_balance=running_balance,
                status=event.status,
            )
        )

    return FlatLedgerRead(
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat.id,
        flat_number=flat.flat_number,
        date_from=date_from,
        date_to=date_to,
        opening_balance=opening_balance,
        total_debits=total_debits,
        total_credits=total_credits,
        closing_balance=running_balance,
        lines=lines,
    )


def get_flat_ledger(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    date_from: date | None,
    date_to: date | None,
) -> FlatLedgerRead:
    flat = get_flat_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
    )
    opening_events = (
        load_flat_events(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_id=flat_id,
            before_date=date_from,
        )
        if date_from is not None
        else []
    )
    movement_events = load_flat_events(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        date_from=date_from,
        date_to=date_to,
    )
    return build_flat_ledger(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        flat=flat,
        date_from=date_from,
        date_to=date_to,
        opening_events=opening_events,
        movement_events=movement_events,
    )
