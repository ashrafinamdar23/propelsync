from datetime import date
from decimal import Decimal
import uuid
import zipfile
from io import BytesIO

from app.models import ChartOfAccount
from app.services.income_expense import (
    build_income_expense_report,
    export_income_expense_report,
    income_expense_amount,
)


def build_account(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    code: str,
    account_type: str,
) -> ChartOfAccount:
    return ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code=code,
        account_name=f"Account {code}",
        account_type=account_type,
        normal_balance="credit" if account_type == "income" else "debit",
        status="active",
    )


def test_income_expense_amount_uses_credit_minus_debit_for_income() -> None:
    assert income_expense_amount("income", Decimal("100.00"), Decimal("750.00")) == Decimal("650.00")


def test_income_expense_amount_uses_debit_minus_credit_for_expense() -> None:
    assert income_expense_amount("expense", Decimal("750.00"), Decimal("100.00")) == Decimal("650.00")


def test_build_income_expense_report_calculates_surplus() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    income = build_account(tenant_id=tenant_id, society_id=society_id, code="4010", account_type="income")
    expense = build_account(tenant_id=tenant_id, society_id=society_id, code="5010", account_type="expense")

    report = build_income_expense_report(
        tenant_id=tenant_id,
        society_id=society_id,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        accounts=[income, expense],
        totals_by_account={
            income.id: (Decimal("0.00"), Decimal("1000.00")),
            expense.id: (Decimal("250.00"), Decimal("0.00")),
        },
    )

    assert report.total_income == Decimal("1000.00")
    assert report.total_expense == Decimal("250.00")
    assert report.net_surplus == Decimal("750.00")


def test_export_income_expense_report_builds_xlsx_and_pdf_bytes() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    income = build_account(tenant_id=tenant_id, society_id=society_id, code="4010", account_type="income")
    report = build_income_expense_report(
        tenant_id=tenant_id,
        society_id=society_id,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        accounts=[income],
        totals_by_account={income.id: (Decimal("0.00"), Decimal("1000.00"))},
    )

    xlsx_content = export_income_expense_report(report, "xlsx")
    pdf_content = export_income_expense_report(report, "pdf")

    assert zipfile.is_zipfile(BytesIO(xlsx_content))
    assert pdf_content.startswith(b"%PDF-")
