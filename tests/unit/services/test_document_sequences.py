from datetime import date

from app.models import DocumentSequence
from app.services.document_sequences import financial_year_token, format_document_number, reset_key_for


def test_financial_year_token_uses_society_start_month() -> None:
    assert financial_year_token(date(2026, 3, 31), 4) == "FY2526"
    assert financial_year_token(date(2026, 4, 1), 4) == "FY2627"


def test_format_document_number_uses_configured_parts() -> None:
    sequence = DocumentSequence(
        prefix="DSINV",
        include_financial_year=True,
        include_period=True,
        separator="-",
        next_sequence=12,
        padding=5,
        reset_policy="financial_year",
        current_reset_key="FY2627",
        document_type="invoice",
    )

    number = format_document_number(
        sequence,
        invoice_date=date(2026, 4, 1),
        billing_period_start=date(2026, 4, 1),
        financial_year_start_month=4,
    )

    assert number == "DSINV-FY2627-202604-00012"


def test_reset_key_for_monthly_financial_year_and_never() -> None:
    sequence = DocumentSequence(
        prefix="INV",
        include_financial_year=False,
        include_period=True,
        separator="-",
        next_sequence=1,
        padding=5,
        reset_policy="monthly",
        current_reset_key="GLOBAL",
        document_type="invoice",
    )
    assert reset_key_for(sequence, date(2026, 4, 21), 4) == "202604"

    sequence.reset_policy = "financial_year"
    assert reset_key_for(sequence, date(2026, 4, 21), 4) == "FY2627"

    sequence.reset_policy = "never"
    assert reset_key_for(sequence, date(2026, 4, 21), 4) == "GLOBAL"
