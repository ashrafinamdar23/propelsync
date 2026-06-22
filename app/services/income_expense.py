import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, JournalEntry, JournalLine, Society
from app.schemas.income_expense import IncomeExpenseReportRead, IncomeExpenseRowRead
from app.services.journals import money
from app.services.report_exports import ExportTable, build_pdf, build_xlsx
from app.tenants.context import TenantContext


class IncomeExpenseSocietyNotFoundError(Exception):
    pass


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise IncomeExpenseSocietyNotFoundError("Society not found.")


def list_income_expense_accounts(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[ChartOfAccount]:
    return list(
        session.scalars(
            select(ChartOfAccount)
            .where(
                ChartOfAccount.tenant_id == tenant_context.tenant_id,
                ChartOfAccount.society_id == society_id,
                ChartOfAccount.account_type.in_(["income", "expense"]),
            )
            .order_by(ChartOfAccount.account_type, ChartOfAccount.account_code)
        )
    )


def account_period_totals(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> dict[uuid.UUID, tuple[Decimal, Decimal]]:
    rows = session.execute(
        select(
            JournalLine.account_id,
            func.coalesce(func.sum(JournalLine.debit_amount), 0),
            func.coalesce(func.sum(JournalLine.credit_amount), 0),
        )
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .where(
            JournalLine.tenant_id == tenant_context.tenant_id,
            JournalLine.society_id == society_id,
            JournalEntry.tenant_id == tenant_context.tenant_id,
            JournalEntry.society_id == society_id,
            JournalEntry.status == "posted",
            JournalEntry.journal_date >= period_start,
            JournalEntry.journal_date <= period_end,
        )
        .group_by(JournalLine.account_id)
    ).all()
    return {account_id: (money(Decimal(debits)), money(Decimal(credits))) for account_id, debits, credits in rows}


def income_expense_amount(account_type: str, debit_amount: Decimal, credit_amount: Decimal) -> Decimal:
    if account_type == "income":
        return money(credit_amount - debit_amount)
    return money(debit_amount - credit_amount)


def build_income_expense_report(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
    accounts: list[ChartOfAccount],
    totals_by_account: dict[uuid.UUID, tuple[Decimal, Decimal]],
) -> IncomeExpenseReportRead:
    income_rows: list[IncomeExpenseRowRead] = []
    expense_rows: list[IncomeExpenseRowRead] = []
    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")

    for account in accounts:
        debit_amount, credit_amount = totals_by_account.get(account.id, (Decimal("0.00"), Decimal("0.00")))
        amount = income_expense_amount(account.account_type, debit_amount, credit_amount)
        row = IncomeExpenseRowRead(
            account_id=account.id,
            account_code=account.account_code,
            account_name=account.account_name,
            account_type=account.account_type,
            amount=amount,
        )
        if account.account_type == "income":
            income_rows.append(row)
            total_income = money(total_income + amount)
        else:
            expense_rows.append(row)
            total_expense = money(total_expense + amount)

    return IncomeExpenseReportRead(
        tenant_id=tenant_id,
        society_id=society_id,
        period_start=period_start,
        period_end=period_end,
        total_income=money(total_income),
        total_expense=money(total_expense),
        net_surplus=money(total_income - total_expense),
        income_rows=income_rows,
        expense_rows=expense_rows,
    )


def get_income_expense_report(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> IncomeExpenseReportRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    accounts = list_income_expense_accounts(session, tenant_context=tenant_context, society_id=society_id)
    totals_by_account = account_period_totals(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        period_start=period_start,
        period_end=period_end,
    )
    return build_income_expense_report(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        period_start=period_start,
        period_end=period_end,
        accounts=accounts,
        totals_by_account=totals_by_account,
    )


def income_expense_export_table(report: IncomeExpenseReportRead) -> ExportTable:
    rows: list[list[str | Decimal]] = []
    rows.append(["Income", "", Decimal("0.00")])
    rows.extend([row.account_code, row.account_name, row.amount] for row in report.income_rows)
    rows.append(["", "", Decimal("0.00")])
    rows.append(["Expenses", "", Decimal("0.00")])
    rows.extend([row.account_code, row.account_name, row.amount] for row in report.expense_rows)
    return ExportTable(
        title="Income vs Expense",
        subtitle=f"{report.period_start.isoformat()} to {report.period_end.isoformat()}",
        headers=["Account Code", "Account Name", "Amount"],
        rows=rows,
        footer_rows=[
            ["Total Income", "", report.total_income],
            ["Total Expense", "", report.total_expense],
            ["Net Surplus / Deficit", "", report.net_surplus],
        ],
    )


def export_income_expense_report(report: IncomeExpenseReportRead, export_format: str) -> bytes:
    table = income_expense_export_table(report)
    if export_format == "xlsx":
        return build_xlsx(table)
    return build_pdf(table)
