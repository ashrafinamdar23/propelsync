import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, JournalEntry, JournalLine, Society
from app.schemas.balance_sheet import BalanceSheetReportRead, BalanceSheetRowRead
from app.services.income_expense import income_expense_amount
from app.services.journals import money
from app.services.report_exports import ExportTable, build_pdf, build_xlsx
from app.tenants.context import TenantContext


class BalanceSheetSocietyNotFoundError(Exception):
    pass


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise BalanceSheetSocietyNotFoundError("Society not found.")


def list_balance_sheet_accounts(
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
                ChartOfAccount.account_type.in_(["asset", "liability", "equity"]),
            )
            .order_by(ChartOfAccount.account_type, ChartOfAccount.account_code)
        )
    )


def account_totals_as_of(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
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
            JournalEntry.journal_date <= as_of_date,
        )
        .group_by(JournalLine.account_id)
    ).all()
    return {account_id: (money(Decimal(debits)), money(Decimal(credits))) for account_id, debits, credits in rows}


def list_profit_loss_accounts(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[ChartOfAccount]:
    return list(
        session.scalars(
            select(ChartOfAccount).where(
                ChartOfAccount.tenant_id == tenant_context.tenant_id,
                ChartOfAccount.society_id == society_id,
                ChartOfAccount.account_type.in_(["income", "expense"]),
            )
        )
    )


def balance_sheet_amount(account_type: str, debit_amount: Decimal, credit_amount: Decimal) -> Decimal:
    if account_type == "asset":
        return money(debit_amount - credit_amount)
    return money(credit_amount - debit_amount)


def build_balance_sheet_report(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    as_of_date: date,
    balance_sheet_accounts: list[ChartOfAccount],
    profit_loss_accounts: list[ChartOfAccount],
    totals_by_account: dict[uuid.UUID, tuple[Decimal, Decimal]],
) -> BalanceSheetReportRead:
    asset_rows: list[BalanceSheetRowRead] = []
    liability_rows: list[BalanceSheetRowRead] = []
    equity_rows: list[BalanceSheetRowRead] = []
    total_assets = Decimal("0.00")
    total_liabilities = Decimal("0.00")
    total_equity = Decimal("0.00")
    current_surplus = Decimal("0.00")

    for account in balance_sheet_accounts:
        debit_amount, credit_amount = totals_by_account.get(account.id, (Decimal("0.00"), Decimal("0.00")))
        amount = balance_sheet_amount(account.account_type, debit_amount, credit_amount)
        row = BalanceSheetRowRead(
            account_id=account.id,
            account_code=account.account_code,
            account_name=account.account_name,
            account_type=account.account_type,
            amount=amount,
        )
        if account.account_type == "asset":
            asset_rows.append(row)
            total_assets = money(total_assets + amount)
        elif account.account_type == "liability":
            liability_rows.append(row)
            total_liabilities = money(total_liabilities + amount)
        else:
            equity_rows.append(row)
            total_equity = money(total_equity + amount)

    for account in profit_loss_accounts:
        debit_amount, credit_amount = totals_by_account.get(account.id, (Decimal("0.00"), Decimal("0.00")))
        amount = income_expense_amount(account.account_type, debit_amount, credit_amount)
        if account.account_type == "income":
            current_surplus = money(current_surplus + amount)
        else:
            current_surplus = money(current_surplus - amount)

    equity_rows.append(
        BalanceSheetRowRead(
            account_code="CURRENT",
            account_name="Current Surplus / Deficit",
            account_type="equity",
            amount=current_surplus,
        )
    )
    total_equity = money(total_equity + current_surplus)
    total_liabilities_and_equity = money(total_liabilities + total_equity)

    return BalanceSheetReportRead(
        tenant_id=tenant_id,
        society_id=society_id,
        as_of_date=as_of_date,
        total_assets=money(total_assets),
        total_liabilities=money(total_liabilities),
        total_equity=money(total_equity),
        current_surplus=current_surplus,
        total_liabilities_and_equity=total_liabilities_and_equity,
        is_balanced=money(total_assets) == total_liabilities_and_equity,
        asset_rows=asset_rows,
        liability_rows=liability_rows,
        equity_rows=equity_rows,
    )


def get_balance_sheet_report(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> BalanceSheetReportRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return build_balance_sheet_report(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        as_of_date=as_of_date,
        balance_sheet_accounts=list_balance_sheet_accounts(
            session, tenant_context=tenant_context, society_id=society_id
        ),
        profit_loss_accounts=list_profit_loss_accounts(
            session, tenant_context=tenant_context, society_id=society_id
        ),
        totals_by_account=account_totals_as_of(
            session, tenant_context=tenant_context, society_id=society_id, as_of_date=as_of_date
        ),
    )


def balance_sheet_export_table(report: BalanceSheetReportRead) -> ExportTable:
    rows: list[list[str | Decimal]] = [["Assets", "", Decimal("0.00")]]
    rows.extend([row.account_code, row.account_name, row.amount] for row in report.asset_rows)
    rows.append(["", "", Decimal("0.00")])
    rows.append(["Liabilities", "", Decimal("0.00")])
    rows.extend([row.account_code, row.account_name, row.amount] for row in report.liability_rows)
    rows.append(["", "", Decimal("0.00")])
    rows.append(["Equity", "", Decimal("0.00")])
    rows.extend([row.account_code, row.account_name, row.amount] for row in report.equity_rows)
    return ExportTable(
        title="Balance Sheet",
        subtitle=f"As of {report.as_of_date.isoformat()}",
        headers=["Account Code", "Account Name", "Amount"],
        rows=rows,
        footer_rows=[
            ["Total Assets", "", report.total_assets],
            ["Total Liabilities", "", report.total_liabilities],
            ["Total Equity", "", report.total_equity],
            ["Total Liabilities & Equity", "", report.total_liabilities_and_equity],
        ],
        sheet_name="Balance Sheet",
    )


def export_balance_sheet_report(report: BalanceSheetReportRead, export_format: str) -> bytes:
    table = balance_sheet_export_table(report)
    if export_format == "xlsx":
        return build_xlsx(table)
    return build_pdf(table)
