from datetime import date
from decimal import Decimal
from io import BytesIO
import uuid
import zipfile

from app.models import ChartOfAccount
from app.services.balance_sheet import (
    balance_sheet_amount,
    build_balance_sheet_report,
    export_balance_sheet_report,
)


def build_account(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    code: str,
    account_type: str,
) -> ChartOfAccount:
    normal_balance = "debit" if account_type in {"asset", "expense"} else "credit"
    return ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code=code,
        account_name=f"Account {code}",
        account_type=account_type,
        normal_balance=normal_balance,
        status="active",
    )


def test_balance_sheet_amount_uses_debit_balance_for_assets() -> None:
    assert balance_sheet_amount("asset", Decimal("1000.00"), Decimal("250.00")) == Decimal("750.00")


def test_balance_sheet_amount_uses_credit_balance_for_liability_and_equity() -> None:
    assert balance_sheet_amount("liability", Decimal("250.00"), Decimal("1000.00")) == Decimal("750.00")


def test_build_balance_sheet_includes_current_surplus_and_balances() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    bank = build_account(tenant_id=tenant_id, society_id=society_id, code="1010", account_type="asset")
    equity = build_account(tenant_id=tenant_id, society_id=society_id, code="3000", account_type="equity")
    income = build_account(tenant_id=tenant_id, society_id=society_id, code="4010", account_type="income")
    expense = build_account(tenant_id=tenant_id, society_id=society_id, code="5010", account_type="expense")

    report = build_balance_sheet_report(
        tenant_id=tenant_id,
        society_id=society_id,
        as_of_date=date(2026, 6, 22),
        balance_sheet_accounts=[bank, equity],
        profit_loss_accounts=[income, expense],
        totals_by_account={
            bank.id: (Decimal("1000.00"), Decimal("0.00")),
            equity.id: (Decimal("0.00"), Decimal("700.00")),
            income.id: (Decimal("0.00"), Decimal("500.00")),
            expense.id: (Decimal("200.00"), Decimal("0.00")),
        },
    )

    assert report.total_assets == Decimal("1000.00")
    assert report.current_surplus == Decimal("300.00")
    assert report.total_equity == Decimal("1000.00")
    assert report.total_liabilities_and_equity == Decimal("1000.00")
    assert report.is_balanced is True


def test_export_balance_sheet_report_builds_xlsx_and_pdf_bytes() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    bank = build_account(tenant_id=tenant_id, society_id=society_id, code="1010", account_type="asset")
    equity = build_account(tenant_id=tenant_id, society_id=society_id, code="3000", account_type="equity")
    report = build_balance_sheet_report(
        tenant_id=tenant_id,
        society_id=society_id,
        as_of_date=date(2026, 6, 22),
        balance_sheet_accounts=[bank, equity],
        profit_loss_accounts=[],
        totals_by_account={
            bank.id: (Decimal("1000.00"), Decimal("0.00")),
            equity.id: (Decimal("0.00"), Decimal("1000.00")),
        },
    )

    xlsx_content = export_balance_sheet_report(report, "xlsx")
    pdf_content = export_balance_sheet_report(report, "pdf")

    assert zipfile.is_zipfile(BytesIO(xlsx_content))
    assert pdf_content.startswith(b"%PDF-")
