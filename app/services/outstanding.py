import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Building, Flat, Invoice, Society, Wing
from app.schemas.outstanding import AgeingBuckets, OutstandingFlatRow, OutstandingSummary
from app.tenants.context import TenantContext


class OutstandingSocietyNotFoundError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def empty_ageing() -> dict[str, Decimal]:
    return {
        "current": Decimal("0.00"),
        "days_1_30": Decimal("0.00"),
        "days_31_60": Decimal("0.00"),
        "days_61_90": Decimal("0.00"),
        "days_90_plus": Decimal("0.00"),
    }


def ageing_bucket_for_due_date(due_date: date, *, as_of_date: date) -> str:
    days_overdue = (as_of_date - due_date).days
    if days_overdue <= 0:
        return "current"
    if days_overdue <= 30:
        return "days_1_30"
    if days_overdue <= 60:
        return "days_31_60"
    if days_overdue <= 90:
        return "days_61_90"
    return "days_90_plus"


def calculate_outstanding_summary(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> OutstandingSummary:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise OutstandingSocietyNotFoundError("Society not found.")

    flat_rows = session.execute(
        select(Flat, Building, Wing)
        .join(Building, Building.id == Flat.building_id)
        .outerjoin(Wing, Wing.id == Flat.wing_id)
        .where(
            Flat.tenant_id == tenant_context.tenant_id,
            Flat.society_id == society_id,
            Flat.status == "active",
        )
        .order_by(Building.name, Wing.name, Flat.flat_number)
    ).all()
    invoices = list(
        session.scalars(
            select(Invoice)
            .where(
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
                Invoice.status != "cancelled",
                Invoice.amount_due > 0,
            )
            .order_by(Invoice.due_date, Invoice.invoice_number)
        )
    )

    invoices_by_flat: dict[uuid.UUID, list[Invoice]] = defaultdict(list)
    for invoice in invoices:
        invoices_by_flat[invoice.flat_id].append(invoice)

    summary_ageing = empty_ageing()
    rows: list[OutstandingFlatRow] = []
    invoice_count = 0
    total_outstanding = Decimal("0.00")
    overdue_amount = Decimal("0.00")

    for flat, building, wing in flat_rows:
        flat_invoices = invoices_by_flat.get(flat.id, [])
        flat_ageing = empty_ageing()
        flat_total = Decimal("0.00")
        flat_overdue = Decimal("0.00")
        oldest_due_date: date | None = None

        for invoice in flat_invoices:
            amount_due = money(invoice.amount_due)
            bucket = ageing_bucket_for_due_date(invoice.due_date, as_of_date=as_of_date)
            flat_ageing[bucket] = money(flat_ageing[bucket] + amount_due)
            summary_ageing[bucket] = money(summary_ageing[bucket] + amount_due)
            flat_total = money(flat_total + amount_due)
            if invoice.due_date < as_of_date:
                flat_overdue = money(flat_overdue + amount_due)
            if oldest_due_date is None or invoice.due_date < oldest_due_date:
                oldest_due_date = invoice.due_date

        total_outstanding = money(total_outstanding + flat_total)
        overdue_amount = money(overdue_amount + flat_overdue)
        invoice_count += len(flat_invoices)
        if flat_total == Decimal("0.00"):
            continue

        rows.append(
            OutstandingFlatRow(
                flat_id=flat.id,
                flat_number=flat.flat_number,
                building_id=building.id,
                building_name=building.name,
                wing_id=wing.id if wing else None,
                wing_name=wing.name if wing else None,
                invoice_count=len(flat_invoices),
                total_outstanding=flat_total,
                overdue_amount=flat_overdue,
                oldest_due_date=oldest_due_date,
                ageing=AgeingBuckets(**flat_ageing),
            )
        )

    return OutstandingSummary(
        society_id=society_id,
        as_of_date=as_of_date,
        flat_count=len(flat_rows),
        flats_with_outstanding=len(rows),
        invoice_count=invoice_count,
        total_outstanding=total_outstanding,
        overdue_amount=overdue_amount,
        ageing=AgeingBuckets(**summary_ageing),
        rows=rows,
    )
