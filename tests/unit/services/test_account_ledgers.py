from datetime import date
from decimal import Decimal
import uuid

from app.models import ChartOfAccount, JournalEntry, JournalLine
from app.services.account_ledgers import build_account_ledger, signed_amount


def build_account(normal_balance: str = "debit") -> ChartOfAccount:
    return ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        account_code="1010",
        account_name="Bank Account",
        account_type="asset" if normal_balance == "debit" else "income",
        normal_balance=normal_balance,
        status="active",
    )


def build_row(
    account: ChartOfAccount,
    *,
    journal_date: date,
    line_number: int,
    debit: str = "0.00",
    credit: str = "0.00",
) -> tuple[JournalLine, JournalEntry]:
    entry = JournalEntry(
        id=uuid.uuid4(),
        tenant_id=account.tenant_id,
        society_id=account.society_id,
        journal_date=journal_date,
        source_type="manual",
        reference_number=f"JV-{line_number}",
        description=f"Entry {line_number}",
        status="posted",
    )
    line = JournalLine(
        id=uuid.uuid4(),
        tenant_id=account.tenant_id,
        society_id=account.society_id,
        journal_entry_id=entry.id,
        account_id=account.id,
        line_number=line_number,
        debit_amount=Decimal(debit),
        credit_amount=Decimal(credit),
    )
    return line, entry


def test_signed_amount_uses_debit_normal_balance() -> None:
    assert signed_amount(
        normal_balance="debit",
        debit_amount=Decimal("100.00"),
        credit_amount=Decimal("25.00"),
    ) == Decimal("75.00")


def test_signed_amount_uses_credit_normal_balance() -> None:
    assert signed_amount(
        normal_balance="credit",
        debit_amount=Decimal("100.00"),
        credit_amount=Decimal("25.00"),
    ) == Decimal("-75.00")


def test_build_account_ledger_returns_opening_running_and_closing_balances() -> None:
    account = build_account("debit")
    opening_rows = [
        build_row(account, journal_date=date(2026, 3, 31), line_number=1, debit="500.00"),
        build_row(account, journal_date=date(2026, 3, 31), line_number=2, credit="100.00"),
    ]
    movement_rows = [
        build_row(account, journal_date=date(2026, 4, 1), line_number=3, debit="300.00"),
        build_row(account, journal_date=date(2026, 4, 2), line_number=4, credit="125.50"),
    ]

    ledger = build_account_ledger(
        account=account,
        date_from=date(2026, 4, 1),
        date_to=date(2026, 4, 30),
        opening_rows=opening_rows,
        movement_rows=movement_rows,
    )

    assert ledger.opening_balance == Decimal("400.00")
    assert ledger.total_debits == Decimal("300.00")
    assert ledger.total_credits == Decimal("125.50")
    assert ledger.closing_balance == Decimal("574.50")
    assert [line.running_balance for line in ledger.lines] == [Decimal("700.00"), Decimal("574.50")]
