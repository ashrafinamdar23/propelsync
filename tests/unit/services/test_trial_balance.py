from datetime import date
from decimal import Decimal
import uuid

from app.models import ChartOfAccount
from app.services.trial_balance import build_trial_balance, closing_debit_credit_balance


def build_account(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    code: str,
    account_type: str,
    normal_balance: str,
) -> ChartOfAccount:
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


def test_closing_debit_credit_balance_for_debit_normal_account() -> None:
    assert closing_debit_credit_balance(
        normal_balance="debit",
        debit_amount=Decimal("500.00"),
        credit_amount=Decimal("125.00"),
    ) == (Decimal("375.00"), Decimal("0.00"))


def test_closing_debit_credit_balance_for_credit_normal_account() -> None:
    assert closing_debit_credit_balance(
        normal_balance="credit",
        debit_amount=Decimal("125.00"),
        credit_amount=Decimal("500.00"),
    ) == (Decimal("0.00"), Decimal("375.00"))


def test_closing_debit_credit_balance_handles_abnormal_credit_account_debit_balance() -> None:
    assert closing_debit_credit_balance(
        normal_balance="credit",
        debit_amount=Decimal("700.00"),
        credit_amount=Decimal("500.00"),
    ) == (Decimal("200.00"), Decimal("0.00"))


def test_build_trial_balance_summarizes_accounts_and_balances_totals() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    bank = build_account(
        tenant_id=tenant_id,
        society_id=society_id,
        code="1010",
        account_type="asset",
        normal_balance="debit",
    )
    income = build_account(
        tenant_id=tenant_id,
        society_id=society_id,
        code="4010",
        account_type="income",
        normal_balance="credit",
    )

    trial_balance = build_trial_balance(
        tenant_id=tenant_id,
        society_id=society_id,
        as_of_date=date(2026, 6, 22),
        accounts=[bank, income],
        totals_by_account={
            bank.id: (Decimal("1000.00"), Decimal("0.00")),
            income.id: (Decimal("0.00"), Decimal("1000.00")),
        },
    )

    assert trial_balance.total_debits == Decimal("1000.00")
    assert trial_balance.total_credits == Decimal("1000.00")
    assert trial_balance.is_balanced is True
    assert trial_balance.rows[0].debit_balance == Decimal("1000.00")
    assert trial_balance.rows[1].credit_balance == Decimal("1000.00")
