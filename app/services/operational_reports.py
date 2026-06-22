import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Building, Expense, ExpenseCategory, Flat, Invoice, Payment, Society, Vendor, Wing
from app.schemas.operational_report import (
    BillingReportRead,
    BillingReportRow,
    CollectionReportRead,
    CollectionReportRow,
    DefaulterReportRead,
    DefaulterReportRow,
    ExpenseReportRead,
    ExpenseReportRow,
)
from app.schemas.outstanding import OutstandingSummary
from app.services.outstanding import calculate_outstanding_summary
from app.services.report_exports import ExportTable, build_pdf, build_xlsx
from app.tenants.context import TenantContext


class OperationalReportSocietyNotFoundError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise OperationalReportSocietyNotFoundError("Society not found.")


def get_billing_report(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> BillingReportRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    records = session.execute(
        select(Invoice, Flat, Building, Wing)
        .join(Flat, Flat.id == Invoice.flat_id)
        .join(Building, Building.id == Flat.building_id)
        .outerjoin(Wing, Wing.id == Flat.wing_id)
        .where(
            Invoice.tenant_id == tenant_context.tenant_id,
            Invoice.society_id == society_id,
            Invoice.invoice_date >= period_start,
            Invoice.invoice_date <= period_end,
            Invoice.status != "cancelled",
        )
        .order_by(Invoice.invoice_date, Invoice.invoice_number)
    ).all()
    rows = [
        BillingReportRow(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            flat_number=flat.flat_number,
            building_name=building.name,
            wing_name=wing.name if wing else None,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            billing_period_start=invoice.billing_period_start,
            billing_period_end=invoice.billing_period_end,
            total_amount=money(invoice.total_amount),
            amount_paid=money(invoice.amount_paid),
            amount_due=money(invoice.amount_due),
            status=invoice.status,
        )
        for invoice, flat, building, wing in records
    ]
    return BillingReportRead(
        society_id=society_id,
        period_start=period_start,
        period_end=period_end,
        invoice_count=len(rows),
        total_billed=money(sum((row.total_amount for row in rows), Decimal("0.00"))),
        total_paid=money(sum((row.amount_paid for row in rows), Decimal("0.00"))),
        total_due=money(sum((row.amount_due for row in rows), Decimal("0.00"))),
        rows=rows,
    )


def get_collection_report(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> CollectionReportRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    records = session.execute(
        select(Payment, Flat, Building, Wing)
        .join(Flat, Flat.id == Payment.flat_id)
        .join(Building, Building.id == Flat.building_id)
        .outerjoin(Wing, Wing.id == Flat.wing_id)
        .where(
            Payment.tenant_id == tenant_context.tenant_id,
            Payment.society_id == society_id,
            Payment.payment_date >= period_start,
            Payment.payment_date <= period_end,
            Payment.status != "reversed",
        )
        .order_by(Payment.payment_date, Payment.created_at)
    ).all()
    rows = [
        CollectionReportRow(
            payment_id=payment.id,
            payment_date=payment.payment_date,
            flat_number=flat.flat_number,
            building_name=building.name,
            wing_name=wing.name if wing else None,
            payment_mode=payment.payment_mode,
            reference_number=payment.reference_number,
            amount=money(payment.amount),
            unapplied_amount=money(payment.unapplied_amount),
            status=payment.status,
        )
        for payment, flat, building, wing in records
    ]
    return CollectionReportRead(
        society_id=society_id,
        period_start=period_start,
        period_end=period_end,
        payment_count=len(rows),
        total_collected=money(sum((row.amount for row in rows), Decimal("0.00"))),
        total_unapplied=money(sum((row.unapplied_amount for row in rows), Decimal("0.00"))),
        rows=rows,
    )


def get_expense_report(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> ExpenseReportRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    records = session.execute(
        select(Expense, ExpenseCategory, Vendor)
        .join(ExpenseCategory, ExpenseCategory.id == Expense.expense_category_id)
        .outerjoin(Vendor, Vendor.id == Expense.vendor_id)
        .where(
            Expense.tenant_id == tenant_context.tenant_id,
            Expense.society_id == society_id,
            Expense.expense_date >= period_start,
            Expense.expense_date <= period_end,
            Expense.status != "cancelled",
        )
        .order_by(Expense.expense_date, Expense.created_at)
    ).all()
    rows = [
        ExpenseReportRow(
            expense_id=expense.id,
            expense_date=expense.expense_date,
            due_date=expense.due_date,
            category_name=category.name,
            vendor_name=vendor.vendor_name if vendor else None,
            expense_type=expense.expense_type,
            reference_number=expense.reference_number,
            vendor_bill_number=expense.vendor_bill_number,
            description=expense.description,
            amount=money(expense.amount),
            tax_amount=money(expense.tax_amount),
            total_amount=money(expense.total_amount),
            amount_paid=money(expense.amount_paid),
            amount_due=money(expense.amount_due),
            status=expense.status,
            payment_status=expense.payment_status,
        )
        for expense, category, vendor in records
    ]
    return ExpenseReportRead(
        society_id=society_id,
        period_start=period_start,
        period_end=period_end,
        expense_count=len(rows),
        total_expense=money(sum((row.total_amount for row in rows), Decimal("0.00"))),
        total_paid=money(sum((row.amount_paid for row in rows), Decimal("0.00"))),
        total_due=money(sum((row.amount_due for row in rows), Decimal("0.00"))),
        rows=rows,
    )


def get_defaulter_report(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> DefaulterReportRead:
    summary = calculate_outstanding_summary(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        as_of_date=as_of_date,
    )
    rows = [
        DefaulterReportRow(
            flat_id=row.flat_id,
            flat_number=row.flat_number,
            building_name=row.building_name,
            wing_name=row.wing_name,
            invoice_count=row.invoice_count,
            overdue_amount=row.overdue_amount,
            oldest_due_date=row.oldest_due_date,
            days_overdue=(as_of_date - row.oldest_due_date).days if row.oldest_due_date else 0,
        )
        for row in summary.rows
        if row.overdue_amount > 0
    ]
    rows.sort(key=lambda row: (row.oldest_due_date or as_of_date, row.building_name, row.flat_number))
    return DefaulterReportRead(
        society_id=society_id,
        as_of_date=as_of_date,
        defaulter_count=len(rows),
        total_overdue=money(sum((row.overdue_amount for row in rows), Decimal("0.00"))),
        rows=rows,
    )


def billing_export_table(report: BillingReportRead) -> ExportTable:
    return ExportTable(
        title="Billing Report",
        subtitle=f"{report.period_start.isoformat()} to {report.period_end.isoformat()}",
        headers=["Invoice", "Flat", "Building", "Wing", "Date", "Due", "Total", "Paid", "Due Amount", "Status"],
        rows=[
            [
                row.invoice_number,
                row.flat_number,
                row.building_name,
                row.wing_name or "",
                row.invoice_date.isoformat(),
                row.due_date.isoformat(),
                row.total_amount,
                row.amount_paid,
                row.amount_due,
                row.status,
            ]
            for row in report.rows
        ],
        footer_rows=[["Totals", "", "", "", "", "", report.total_billed, report.total_paid, report.total_due, ""]],
        sheet_name="Billing",
    )


def collection_export_table(report: CollectionReportRead) -> ExportTable:
    return ExportTable(
        title="Collection Report",
        subtitle=f"{report.period_start.isoformat()} to {report.period_end.isoformat()}",
        headers=["Date", "Flat", "Building", "Wing", "Mode", "Reference", "Amount", "Unapplied", "Status"],
        rows=[
            [
                row.payment_date.isoformat(),
                row.flat_number,
                row.building_name,
                row.wing_name or "",
                row.payment_mode,
                row.reference_number or "",
                row.amount,
                row.unapplied_amount,
                row.status,
            ]
            for row in report.rows
        ],
        footer_rows=[["Totals", "", "", "", "", "", report.total_collected, report.total_unapplied, ""]],
        sheet_name="Collection",
    )


def expense_export_table(report: ExpenseReportRead) -> ExportTable:
    return ExportTable(
        title="Expense Report",
        subtitle=f"{report.period_start.isoformat()} to {report.period_end.isoformat()}",
        headers=["Date", "Category", "Vendor", "Type", "Reference", "Description", "Total", "Paid", "Due", "Status"],
        rows=[
            [
                row.expense_date.isoformat(),
                row.category_name,
                row.vendor_name or "",
                row.expense_type,
                row.reference_number or row.vendor_bill_number or "",
                row.description,
                row.total_amount,
                row.amount_paid,
                row.amount_due,
                row.status,
            ]
            for row in report.rows
        ],
        footer_rows=[["Totals", "", "", "", "", "", report.total_expense, report.total_paid, report.total_due, ""]],
        sheet_name="Expenses",
    )


def defaulter_export_table(report: DefaulterReportRead) -> ExportTable:
    return ExportTable(
        title="Defaulter Report",
        subtitle=f"As of {report.as_of_date.isoformat()}",
        headers=["Flat", "Building", "Wing", "Invoices", "Overdue", "Oldest Due", "Days Overdue"],
        rows=[
            [
                row.flat_number,
                row.building_name,
                row.wing_name or "",
                str(row.invoice_count),
                row.overdue_amount,
                row.oldest_due_date.isoformat() if row.oldest_due_date else "",
                str(row.days_overdue),
            ]
            for row in report.rows
        ],
        footer_rows=[["Totals", "", "", str(report.defaulter_count), report.total_overdue, "", ""]],
        sheet_name="Defaulters",
    )


def outstanding_export_table(report: OutstandingSummary) -> ExportTable:
    return ExportTable(
        title="Outstanding Report",
        subtitle=f"As of {report.as_of_date.isoformat()}",
        headers=["Flat", "Building", "Wing", "Invoices", "Outstanding", "Overdue", "Oldest Due"],
        rows=[
            [
                row.flat_number,
                row.building_name,
                row.wing_name or "",
                str(row.invoice_count),
                row.total_outstanding,
                row.overdue_amount,
                row.oldest_due_date.isoformat() if row.oldest_due_date else "",
            ]
            for row in report.rows
        ],
        footer_rows=[
            [
                "Totals",
                "",
                "",
                str(report.invoice_count),
                report.total_outstanding,
                report.overdue_amount,
                "",
            ]
        ],
        sheet_name="Outstanding",
    )


def export_table(table: ExportTable, export_format: str) -> bytes:
    if export_format == "xlsx":
        return build_xlsx(table)
    return build_pdf(table)
