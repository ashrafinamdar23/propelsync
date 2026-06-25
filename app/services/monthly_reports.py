import calendar
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Building,
    ChargeType,
    ChartOfAccount,
    Expense,
    ExpenseCategory,
    ExpensePayment,
    Flat,
    Invoice,
    InvoiceLineItem,
    JournalEntry,
    JournalLine,
    Payment,
    PaymentAllocation,
    Society,
    Vendor,
    Wing,
)
from app.schemas.monthly_report import (
    MonthlyBalanceRow,
    MonthlyCollectionRow,
    MonthlyExpenseRow,
    MonthlyPendingDueRow,
    MonthlyReportSummary,
    MonthlySocietyReportRead,
)
from app.services.balance_sheet import get_balance_sheet_report
from app.services.journals import money
from app.services.report_exports import ExportTable, build_multi_sheet_xlsx
from app.tenants.context import TenantContext


class MonthlyReportSocietyNotFoundError(Exception):
    pass


class MonthlyReportInvalidMonthError(Exception):
    pass


def parse_report_month(report_month: str, *, today: date | None = None) -> tuple[date, date]:
    try:
        year_text, month_text = report_month.split("-", maxsplit=1)
        year = int(year_text)
        month = int(month_text)
        if month < 1 or month > 12:
            raise ValueError
    except ValueError as exc:
        raise MonthlyReportInvalidMonthError("Report month must be in YYYY-MM format.") from exc

    period_start = date(year, month, 1)
    period_end = date(year, month, calendar.monthrange(year, month)[1])
    current_date = today or date.today()
    if period_start <= current_date <= period_end:
        period_end = current_date
    return period_start, period_end


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> Society:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise MonthlyReportSocietyNotFoundError("Society not found.")
    return society


def is_cash_account(account: ChartOfAccount | None) -> bool:
    if account is None:
        return False
    account_text = f"{account.account_code} {account.account_name}".lower()
    return "cash" in account_text


def is_bank_or_cash_account(account: ChartOfAccount) -> bool:
    account_text = f"{account.account_code} {account.account_name}".lower()
    return account.account_type == "asset" and ("bank" in account_text or "cash" in account_text)


def is_penalty_text(*values: str | None) -> bool:
    text = " ".join(value or "" for value in values).lower()
    return any(marker in text for marker in ["late", "penalty", "fine"])


def list_bank_cash_accounts(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[ChartOfAccount]:
    accounts = session.scalars(
        select(ChartOfAccount).where(
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "asset",
        )
    )
    return [account for account in accounts if is_bank_or_cash_account(account)]


def bank_cash_balance_as_of(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> tuple[Decimal, Decimal]:
    accounts = list_bank_cash_accounts(session, tenant_context=tenant_context, society_id=society_id)
    if not accounts:
        return Decimal("0.00"), Decimal("0.00")

    totals = session.execute(
        select(
            JournalLine.account_id,
            func.coalesce(func.sum(JournalLine.debit_amount), 0),
            func.coalesce(func.sum(JournalLine.credit_amount), 0),
        )
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .where(
            JournalLine.tenant_id == tenant_context.tenant_id,
            JournalLine.society_id == society_id,
            JournalLine.account_id.in_([account.id for account in accounts]),
            JournalEntry.tenant_id == tenant_context.tenant_id,
            JournalEntry.society_id == society_id,
            JournalEntry.status == "posted",
            JournalEntry.journal_date <= as_of_date,
        )
        .group_by(JournalLine.account_id)
    ).all()
    totals_by_account = {
        account_id: money(Decimal(debits) - Decimal(credits)) for account_id, debits, credits in totals
    }
    bank_total = Decimal("0.00")
    cash_total = Decimal("0.00")
    for account in accounts:
        amount = totals_by_account.get(account.id, Decimal("0.00"))
        if is_cash_account(account):
            cash_total = money(cash_total + amount)
        else:
            bank_total = money(bank_total + amount)
    return money(bank_total), money(cash_total)


def collection_bank_cash_totals(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> tuple[Decimal, Decimal]:
    records = session.execute(
        select(Payment, ChartOfAccount)
        .outerjoin(ChartOfAccount, ChartOfAccount.id == Payment.deposit_account_id)
        .where(
            Payment.tenant_id == tenant_context.tenant_id,
            Payment.society_id == society_id,
            Payment.payment_date >= period_start,
            Payment.payment_date <= period_end,
            Payment.status != "reversed",
        )
    ).all()
    bank_total = Decimal("0.00")
    cash_total = Decimal("0.00")
    for payment, account in records:
        if payment.payment_mode == "cash" or is_cash_account(account):
            cash_total = money(cash_total + payment.amount)
        else:
            bank_total = money(bank_total + payment.amount)
    return money(bank_total), money(cash_total)


def expense_payment_bank_cash_totals(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> tuple[Decimal, Decimal]:
    records = session.execute(
        select(ExpensePayment, ChartOfAccount)
        .join(ChartOfAccount, ChartOfAccount.id == ExpensePayment.payment_account_id)
        .where(
            ExpensePayment.tenant_id == tenant_context.tenant_id,
            ExpensePayment.society_id == society_id,
            ExpensePayment.payment_date >= period_start,
            ExpensePayment.payment_date <= period_end,
            ExpensePayment.status != "reversed",
        )
    ).all()
    bank_total = Decimal("0.00")
    cash_total = Decimal("0.00")
    for payment, account in records:
        if payment.payment_mode == "cash" or is_cash_account(account):
            cash_total = money(cash_total + payment.amount)
        else:
            bank_total = money(bank_total + payment.amount)
    return money(bank_total), money(cash_total)


def invoice_penalty_ratios(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice_ids: list[uuid.UUID],
) -> dict[uuid.UUID, Decimal]:
    if not invoice_ids:
        return {}
    records = session.execute(
        select(InvoiceLineItem, ChargeType)
        .join(ChargeType, ChargeType.id == InvoiceLineItem.charge_type_id)
        .where(
            InvoiceLineItem.tenant_id == tenant_context.tenant_id,
            InvoiceLineItem.society_id == society_id,
            InvoiceLineItem.invoice_id.in_(invoice_ids),
        )
    ).all()
    total_by_invoice: dict[uuid.UUID, Decimal] = {}
    penalty_by_invoice: dict[uuid.UUID, Decimal] = {}
    for line, charge_type in records:
        total_by_invoice[line.invoice_id] = money(
            total_by_invoice.get(line.invoice_id, Decimal("0.00")) + line.line_amount
        )
        if is_penalty_text(line.description, charge_type.name, charge_type.code):
            penalty_by_invoice[line.invoice_id] = money(
                penalty_by_invoice.get(line.invoice_id, Decimal("0.00")) + line.line_amount
            )
    ratios: dict[uuid.UUID, Decimal] = {}
    for invoice_id, total_amount in total_by_invoice.items():
        if total_amount > Decimal("0.00"):
            ratios[invoice_id] = penalty_by_invoice.get(invoice_id, Decimal("0.00")) / total_amount
    return ratios


def payment_penalty_totals(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payment_ids: list[uuid.UUID],
) -> dict[uuid.UUID, tuple[Decimal, Decimal]]:
    if not payment_ids:
        return {}
    allocations = list(
        session.scalars(
            select(PaymentAllocation).where(
                PaymentAllocation.tenant_id == tenant_context.tenant_id,
                PaymentAllocation.society_id == society_id,
                PaymentAllocation.payment_id.in_(payment_ids),
                PaymentAllocation.status == "active",
            )
        )
    )
    ratios = invoice_penalty_ratios(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        invoice_ids=list({allocation.invoice_id for allocation in allocations}),
    )
    totals: dict[uuid.UUID, tuple[Decimal, Decimal]] = {}
    for allocation in allocations:
        ratio = ratios.get(allocation.invoice_id, Decimal("0.00"))
        penalty_amount = money(allocation.allocated_amount * ratio)
        normal_amount = money(allocation.allocated_amount - penalty_amount)
        current_normal, current_penalty = totals.get(
            allocation.payment_id, (Decimal("0.00"), Decimal("0.00"))
        )
        totals[allocation.payment_id] = (
            money(current_normal + normal_amount),
            money(current_penalty + penalty_amount),
        )
    return totals


def list_monthly_collections(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> list[MonthlyCollectionRow]:
    records = session.execute(
        select(Payment, Flat, Building, Wing, ChartOfAccount)
        .join(Flat, Flat.id == Payment.flat_id)
        .join(Building, Building.id == Flat.building_id)
        .outerjoin(Wing, Wing.id == Flat.wing_id)
        .outerjoin(ChartOfAccount, ChartOfAccount.id == Payment.deposit_account_id)
        .where(
            Payment.tenant_id == tenant_context.tenant_id,
            Payment.society_id == society_id,
            Payment.payment_date >= period_start,
            Payment.payment_date <= period_end,
            Payment.status != "reversed",
        )
        .order_by(Payment.payment_date, Building.name, Flat.flat_number)
    ).all()
    allocation_totals = payment_penalty_totals(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payment_ids=[payment.id for payment, *_ in records],
    )
    rows: list[MonthlyCollectionRow] = []
    for payment, flat, building, wing, account in records:
        normal_amount, penalty_amount = allocation_totals.get(
            payment.id, (money(payment.amount - payment.unapplied_amount), Decimal("0.00"))
        )
        rows.append(
            MonthlyCollectionRow(
                payment_id=payment.id,
                payment_date=payment.payment_date,
                flat_number=flat.flat_number,
                building_name=building.name,
                wing_name=wing.name if wing else None,
                payment_mode=payment.payment_mode,
                account_name=account.account_name if account else None,
                reference_number=payment.reference_number,
                amount=money(payment.amount),
                normal_amount=money(normal_amount),
                penalty_amount=money(penalty_amount),
                unapplied_amount=money(payment.unapplied_amount),
                status=payment.status,
            )
        )
    return rows


def list_monthly_expenses(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> list[MonthlyExpenseRow]:
    records = session.execute(
        select(Expense, ExpenseCategory, Vendor, ChartOfAccount)
        .join(ExpenseCategory, ExpenseCategory.id == Expense.expense_category_id)
        .outerjoin(Vendor, Vendor.id == Expense.vendor_id)
        .outerjoin(ChartOfAccount, ChartOfAccount.id == Expense.payment_account_id)
        .where(
            Expense.tenant_id == tenant_context.tenant_id,
            Expense.society_id == society_id,
            Expense.expense_date >= period_start,
            Expense.expense_date <= period_end,
            Expense.status != "cancelled",
        )
        .order_by(Expense.expense_date, Expense.created_at)
    ).all()
    return [
        MonthlyExpenseRow(
            expense_id=expense.id,
            expense_date=expense.expense_date,
            due_date=expense.due_date,
            category_name=category.name,
            vendor_name=vendor.vendor_name if vendor else None,
            payment_account_name=account.account_name if account else None,
            expense_type=expense.expense_type,
            reference_number=expense.reference_number,
            vendor_bill_number=expense.vendor_bill_number,
            description=expense.description,
            total_amount=money(expense.total_amount),
            amount_paid=money(expense.amount_paid),
            amount_due=money(expense.amount_due),
            payment_status=expense.payment_status,
            status=expense.status,
        )
        for expense, category, vendor, account in records
    ]


def list_pending_dues(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> list[MonthlyPendingDueRow]:
    records = session.execute(
        select(Invoice, Flat, Building, Wing)
        .join(Flat, Flat.id == Invoice.flat_id)
        .join(Building, Building.id == Flat.building_id)
        .outerjoin(Wing, Wing.id == Flat.wing_id)
        .where(
            Invoice.tenant_id == tenant_context.tenant_id,
            Invoice.society_id == society_id,
            Invoice.status != "cancelled",
            Invoice.amount_due > 0,
            Invoice.invoice_date <= as_of_date,
        )
        .order_by(Invoice.due_date, Building.name, Flat.flat_number)
    ).all()
    return [
        MonthlyPendingDueRow(
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
            days_overdue=max((as_of_date - invoice.due_date).days, 0),
            status=invoice.status,
        )
        for invoice, flat, building, wing in records
    ]


def add_month(month_start: date) -> date:
    year = month_start.year + (1 if month_start.month == 12 else 0)
    month = 1 if month_start.month == 12 else month_start.month + 1
    return date(year, month, 1)


def first_journal_month(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    fallback: date,
) -> date:
    first_date = session.scalar(
        select(func.min(JournalEntry.journal_date)).where(
            JournalEntry.tenant_id == tenant_context.tenant_id,
            JournalEntry.society_id == society_id,
            JournalEntry.status == "posted",
        )
    )
    if first_date is None:
        first_date = fallback
    return date(first_date.year, first_date.month, 1)


def build_month_on_month_rows(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_end: date,
) -> list[MonthlyBalanceRow]:
    start_month = first_journal_month(
        session, tenant_context=tenant_context, society_id=society_id, fallback=period_end
    )
    rows: list[MonthlyBalanceRow] = []
    current_month = start_month
    while current_month <= date(period_end.year, period_end.month, 1):
        month_end = date(
            current_month.year,
            current_month.month,
            calendar.monthrange(current_month.year, current_month.month)[1],
        )
        if month_end > period_end:
            month_end = period_end
        opening_bank, opening_cash = bank_cash_balance_as_of(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=current_month - timedelta(days=1),
        )
        collection_bank, collection_cash = collection_bank_cash_totals(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=current_month,
            period_end=month_end,
        )
        expense_bank, expense_cash = expense_payment_bank_cash_totals(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=current_month,
            period_end=month_end,
        )
        closing_bank, closing_cash = bank_cash_balance_as_of(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=month_end,
        )
        rows.append(
            MonthlyBalanceRow(
                month_start=current_month,
                opening_bank_balance=opening_bank,
                opening_cash_balance=opening_cash,
                bank_collection=collection_bank,
                cash_collection=collection_cash,
                bank_expense=expense_bank,
                cash_expense=expense_cash,
                closing_bank_balance=closing_bank,
                closing_cash_balance=closing_cash,
                closing_total_balance=money(closing_bank + closing_cash),
            )
        )
        current_month = add_month(current_month)
    return rows


def get_monthly_society_report(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    report_month: str,
    today: date | None = None,
) -> MonthlySocietyReportRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    period_start, period_end = parse_report_month(report_month, today=today)
    opening_bank, opening_cash = bank_cash_balance_as_of(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        as_of_date=period_start - timedelta(days=1),
    )
    collection_bank, collection_cash = collection_bank_cash_totals(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        period_start=period_start,
        period_end=period_end,
    )
    expense_bank, expense_cash = expense_payment_bank_cash_totals(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        period_start=period_start,
        period_end=period_end,
    )
    closing_bank, closing_cash = bank_cash_balance_as_of(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        as_of_date=period_end,
    )
    pending_dues = list_pending_dues(
        session, tenant_context=tenant_context, society_id=society_id, as_of_date=period_end
    )
    return MonthlySocietyReportRead(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        report_month=report_month,
        period_start=period_start,
        period_end=period_end,
        summary=MonthlyReportSummary(
            opening_bank_balance=opening_bank,
            opening_cash_balance=opening_cash,
            opening_total_balance=money(opening_bank + opening_cash),
            bank_collection=collection_bank,
            cash_collection=collection_cash,
            total_collection=money(collection_bank + collection_cash),
            bank_expense=expense_bank,
            cash_expense=expense_cash,
            total_expense=money(expense_bank + expense_cash),
            closing_bank_balance=closing_bank,
            closing_cash_balance=closing_cash,
            closing_total_balance=money(closing_bank + closing_cash),
            pending_due_amount=money(sum((row.amount_due for row in pending_dues), Decimal("0.00"))),
        ),
        collections=list_monthly_collections(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=period_start,
            period_end=period_end,
        ),
        expenses=list_monthly_expenses(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=period_start,
            period_end=period_end,
        ),
        pending_dues=pending_dues,
        month_on_month=build_month_on_month_rows(
            session, tenant_context=tenant_context, society_id=society_id, period_end=period_end
        ),
        balance_sheet=get_balance_sheet_report(
            session, tenant_context=tenant_context, society_id=society_id, as_of_date=period_end
        ),
    )


def monthly_summary_table(report: MonthlySocietyReportRead) -> ExportTable:
    rows: list[list[str | Decimal]] = [
        ["Opening Balance", report.summary.opening_bank_balance, report.summary.opening_cash_balance, report.summary.opening_total_balance],
        ["Collection", report.summary.bank_collection, report.summary.cash_collection, report.summary.total_collection],
        ["Expenses", report.summary.bank_expense, report.summary.cash_expense, report.summary.total_expense],
        ["Closing Balance", report.summary.closing_bank_balance, report.summary.closing_cash_balance, report.summary.closing_total_balance],
        ["Pending Dues", "", "", report.summary.pending_due_amount],
    ]
    return ExportTable(
        title="Monthly Society Report",
        subtitle=f"{report.report_month}: {report.period_start.isoformat()} to {report.period_end.isoformat()}",
        headers=["Account", "Bank", "Cash", "Total"],
        rows=rows,
        footer_rows=[],
        sheet_name="AccountSummary",
    )


def monthly_collection_table(report: MonthlySocietyReportRead) -> ExportTable:
    return ExportTable(
        title="Monthly Collection",
        subtitle=f"{report.period_start.isoformat()} to {report.period_end.isoformat()}",
        headers=["Date", "Flat", "Building", "Wing", "Mode", "Account", "Reference", "Amount", "Normal", "Penalty", "Unapplied"],
        rows=[
            [
                row.payment_date.isoformat(),
                row.flat_number,
                row.building_name,
                row.wing_name or "",
                row.payment_mode,
                row.account_name or "",
                row.reference_number or "",
                row.amount,
                row.normal_amount,
                row.penalty_amount,
                row.unapplied_amount,
            ]
            for row in report.collections
        ],
        footer_rows=[
            [
                "Totals",
                "",
                "",
                "",
                "",
                "",
                "",
                sum((row.amount for row in report.collections), Decimal("0.00")),
                sum((row.normal_amount for row in report.collections), Decimal("0.00")),
                sum((row.penalty_amount for row in report.collections), Decimal("0.00")),
                sum((row.unapplied_amount for row in report.collections), Decimal("0.00")),
            ]
        ],
        sheet_name="Income",
    )


def monthly_expense_table(report: MonthlySocietyReportRead) -> ExportTable:
    return ExportTable(
        title="Monthly Expenses",
        subtitle=f"{report.period_start.isoformat()} to {report.period_end.isoformat()}",
        headers=["Date", "Vendor", "Category", "Description", "Type", "Reference", "Payment Account", "Total", "Paid", "Due", "Status"],
        rows=[
            [
                row.expense_date.isoformat(),
                row.vendor_name or "",
                row.category_name,
                row.description,
                row.expense_type,
                row.reference_number or row.vendor_bill_number or "",
                row.payment_account_name or "",
                row.total_amount,
                row.amount_paid,
                row.amount_due,
                row.payment_status,
            ]
            for row in report.expenses
        ],
        footer_rows=[
            [
                "Totals",
                "",
                "",
                "",
                "",
                "",
                "",
                sum((row.total_amount for row in report.expenses), Decimal("0.00")),
                sum((row.amount_paid for row in report.expenses), Decimal("0.00")),
                sum((row.amount_due for row in report.expenses), Decimal("0.00")),
                "",
            ]
        ],
        sheet_name="Expense",
    )


def monthly_pending_table(report: MonthlySocietyReportRead) -> ExportTable:
    return ExportTable(
        title="Pending Dues",
        subtitle=f"As of {report.period_end.isoformat()}",
        headers=["Flat", "Building", "Wing", "Invoice", "Invoice Date", "Due Date", "Period", "Total", "Paid", "Due", "Days Overdue", "Status"],
        rows=[
            [
                row.flat_number,
                row.building_name,
                row.wing_name or "",
                row.invoice_number,
                row.invoice_date.isoformat(),
                row.due_date.isoformat(),
                f"{row.billing_period_start.isoformat()} to {row.billing_period_end.isoformat()}",
                row.total_amount,
                row.amount_paid,
                row.amount_due,
                str(row.days_overdue),
                row.status,
            ]
            for row in report.pending_dues
        ],
        footer_rows=[
            [
                "Totals",
                "",
                "",
                "",
                "",
                "",
                "",
                sum((row.total_amount for row in report.pending_dues), Decimal("0.00")),
                sum((row.amount_paid for row in report.pending_dues), Decimal("0.00")),
                sum((row.amount_due for row in report.pending_dues), Decimal("0.00")),
                "",
                "",
            ]
        ],
        sheet_name="Pending Dues",
    )


def monthly_balance_table(report: MonthlySocietyReportRead) -> ExportTable:
    return ExportTable(
        title="Month On Month Balance",
        subtitle=f"Through {report.period_end.isoformat()}",
        headers=["Month", "Opening Bank", "Opening Cash", "Bank Collection", "Cash Collection", "Bank Expense", "Cash Expense", "Closing Bank", "Closing Cash", "Closing Total"],
        rows=[
            [
                row.month_start.isoformat(),
                row.opening_bank_balance,
                row.opening_cash_balance,
                row.bank_collection,
                row.cash_collection,
                row.bank_expense,
                row.cash_expense,
                row.closing_bank_balance,
                row.closing_cash_balance,
                row.closing_total_balance,
            ]
            for row in report.month_on_month
        ],
        footer_rows=[],
        sheet_name="BalanceSheet",
    )


def monthly_balance_sheet_table(report: MonthlySocietyReportRead) -> ExportTable:
    rows: list[list[str | Decimal]] = [["Assets", "", Decimal("0.00")]]
    rows.extend([row.account_code, row.account_name, row.amount] for row in report.balance_sheet.asset_rows)
    rows.append(["", "", Decimal("0.00")])
    rows.append(["Liabilities", "", Decimal("0.00")])
    rows.extend([row.account_code, row.account_name, row.amount] for row in report.balance_sheet.liability_rows)
    rows.append(["", "", Decimal("0.00")])
    rows.append(["Equity", "", Decimal("0.00")])
    rows.extend([row.account_code, row.account_name, row.amount] for row in report.balance_sheet.equity_rows)
    return ExportTable(
        title="Balance Sheet Snapshot",
        subtitle=f"As of {report.period_end.isoformat()}",
        headers=["Account Code", "Account Name", "Amount"],
        rows=rows,
        footer_rows=[
            ["Total Assets", "", report.balance_sheet.total_assets],
            ["Total Liabilities", "", report.balance_sheet.total_liabilities],
            ["Total Equity", "", report.balance_sheet.total_equity],
            ["Total Liabilities & Equity", "", report.balance_sheet.total_liabilities_and_equity],
        ],
        sheet_name="Balance Snapshot",
    )


def export_monthly_society_report_xlsx(report: MonthlySocietyReportRead) -> bytes:
    return build_multi_sheet_xlsx(
        [
            monthly_summary_table(report),
            monthly_collection_table(report),
            monthly_expense_table(report),
            monthly_balance_table(report),
            monthly_balance_sheet_table(report),
            monthly_pending_table(report),
        ]
    )
