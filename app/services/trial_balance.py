import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, JournalEntry, JournalLine, Society
from app.schemas.trial_balance import TrialBalanceRead, TrialBalanceRowRead
from app.services.account_ledgers import signed_amount
from app.services.journals import money
from app.tenants.context import TenantContext


class TrialBalanceSocietyNotFoundError(Exception):
    pass


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise TrialBalanceSocietyNotFoundError("Society not found.")


def list_society_accounts(
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
            )
            .order_by(ChartOfAccount.account_code)
        )
    )


def account_movement_totals(
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


def closing_debit_credit_balance(
    *,
    normal_balance: str,
    debit_amount: Decimal,
    credit_amount: Decimal,
) -> tuple[Decimal, Decimal]:
    balance = signed_amount(
        normal_balance=normal_balance,
        debit_amount=debit_amount,
        credit_amount=credit_amount,
    )
    if normal_balance == "credit":
        if balance >= Decimal("0.00"):
            return Decimal("0.00"), money(balance)
        return money(abs(balance)), Decimal("0.00")
    if balance >= Decimal("0.00"):
        return money(balance), Decimal("0.00")
    return Decimal("0.00"), money(abs(balance))


def build_trial_balance(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    as_of_date: date,
    accounts: list[ChartOfAccount],
    totals_by_account: dict[uuid.UUID, tuple[Decimal, Decimal]],
) -> TrialBalanceRead:
    rows: list[TrialBalanceRowRead] = []
    total_debits = Decimal("0.00")
    total_credits = Decimal("0.00")

    for account in accounts:
        debit_amount, credit_amount = totals_by_account.get(account.id, (Decimal("0.00"), Decimal("0.00")))
        debit_balance, credit_balance = closing_debit_credit_balance(
            normal_balance=account.normal_balance,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
        )
        total_debits = money(total_debits + debit_balance)
        total_credits = money(total_credits + credit_balance)
        rows.append(
            TrialBalanceRowRead(
                account_id=account.id,
                account_code=account.account_code,
                account_name=account.account_name,
                account_type=account.account_type,
                normal_balance=account.normal_balance,
                status=account.status,
                debit_balance=debit_balance,
                credit_balance=credit_balance,
            )
        )

    return TrialBalanceRead(
        tenant_id=tenant_id,
        society_id=society_id,
        as_of_date=as_of_date,
        total_debits=money(total_debits),
        total_credits=money(total_credits),
        is_balanced=money(total_debits) == money(total_credits),
        rows=rows,
    )


def get_trial_balance(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> TrialBalanceRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    accounts = list_society_accounts(session, tenant_context=tenant_context, society_id=society_id)
    totals_by_account = account_movement_totals(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        as_of_date=as_of_date,
    )
    return build_trial_balance(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        as_of_date=as_of_date,
        accounts=accounts,
        totals_by_account=totals_by_account,
    )
