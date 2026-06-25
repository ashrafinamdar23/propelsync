from datetime import date
from decimal import Decimal
from io import BytesIO
import uuid
import zipfile

import pytest

from app.schemas.balance_sheet import BalanceSheetReportRead
from app.schemas.monthly_report import MonthlyReportSummary, MonthlySocietyReportRead
from app.services.monthly_reports import (
    MonthlyReportInvalidMonthError,
    export_monthly_society_report_xlsx,
    parse_report_month,
)


def empty_balance_sheet(*, tenant_id: uuid.UUID, society_id: uuid.UUID, as_of_date: date) -> BalanceSheetReportRead:
    return BalanceSheetReportRead(
        tenant_id=tenant_id,
        society_id=society_id,
        as_of_date=as_of_date,
        total_assets=Decimal("0.00"),
        total_liabilities=Decimal("0.00"),
        total_equity=Decimal("0.00"),
        current_surplus=Decimal("0.00"),
        total_liabilities_and_equity=Decimal("0.00"),
        is_balanced=True,
        asset_rows=[],
        liability_rows=[],
        equity_rows=[],
    )


def test_parse_report_month_uses_today_for_current_month() -> None:
    period_start, period_end = parse_report_month("2026-06", today=date(2026, 6, 25))

    assert period_start == date(2026, 6, 1)
    assert period_end == date(2026, 6, 25)


def test_parse_report_month_uses_last_day_for_past_month() -> None:
    period_start, period_end = parse_report_month("2026-05", today=date(2026, 6, 25))

    assert period_start == date(2026, 5, 1)
    assert period_end == date(2026, 5, 31)


def test_parse_report_month_rejects_invalid_month() -> None:
    with pytest.raises(MonthlyReportInvalidMonthError):
        parse_report_month("2026-13", today=date(2026, 6, 25))


def test_export_monthly_society_report_xlsx_builds_expected_sheets() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    report = MonthlySocietyReportRead(
        tenant_id=tenant_id,
        society_id=society_id,
        report_month="2026-06",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 25),
        summary=MonthlyReportSummary(
            opening_bank_balance=Decimal("100.00"),
            opening_cash_balance=Decimal("10.00"),
            opening_total_balance=Decimal("110.00"),
            bank_collection=Decimal("50.00"),
            cash_collection=Decimal("5.00"),
            total_collection=Decimal("55.00"),
            bank_expense=Decimal("20.00"),
            cash_expense=Decimal("2.00"),
            total_expense=Decimal("22.00"),
            closing_bank_balance=Decimal("130.00"),
            closing_cash_balance=Decimal("13.00"),
            closing_total_balance=Decimal("143.00"),
            pending_due_amount=Decimal("0.00"),
        ),
        collections=[],
        expenses=[],
        pending_dues=[],
        month_on_month=[],
        balance_sheet=empty_balance_sheet(
            tenant_id=tenant_id,
            society_id=society_id,
            as_of_date=date(2026, 6, 25),
        ),
    )

    content = export_monthly_society_report_xlsx(report)

    assert zipfile.is_zipfile(BytesIO(content))
    with zipfile.ZipFile(BytesIO(content)) as workbook:
        workbook_xml = workbook.read("xl/workbook.xml").decode()
        assert "AccountSummary" in workbook_xml
        assert "Income" in workbook_xml
        assert "Expense" in workbook_xml
        assert "BalanceSheet" in workbook_xml
        assert "Balance Snapshot" in workbook_xml
        assert "Pending Dues" in workbook_xml
