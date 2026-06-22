import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, JournalEntry, JournalLine, Society
from app.schemas.account_ledger import AccountLedgerLineRead, AccountLedgerRead
from app.services.journals import money
from app.tenants.context import TenantContext


class AccountLedgerSocietyNotFoundError(Exception):
    pass


class AccountLedgerAccountNotFoundError(Exception):
    pass


def signed_amount(*, normal_balance: str, debit_amount: Decimal, credit_amount: Decimal) -> Decimal:
    if normal_balance == "credit":
        return money(credit_amount - debit_amount)
    return money(debit_amount - credit_amount)


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise AccountLedgerSocietyNotFoundError("Society not found.")


def load_account(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    account_id: uuid.UUID,
) -> ChartOfAccount:
    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
        )
    )
    if account is None:
        raise AccountLedgerAccountNotFoundError("Account not found.")
    return account


def list_posted_account_lines(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    account_id: uuid.UUID,
    before_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[tuple[JournalLine, JournalEntry]]:
    query = (
        select(JournalLine, JournalEntry)
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        .where(
            JournalLine.tenant_id == tenant_context.tenant_id,
            JournalLine.society_id == society_id,
            JournalLine.account_id == account_id,
            JournalEntry.tenant_id == tenant_context.tenant_id,
            JournalEntry.society_id == society_id,
            JournalEntry.status == "posted",
        )
    )
    if before_date is not None:
        query = query.where(JournalEntry.journal_date < before_date)
    if date_from is not None:
        query = query.where(JournalEntry.journal_date >= date_from)
    if date_to is not None:
        query = query.where(JournalEntry.journal_date <= date_to)
    query = query.order_by(JournalEntry.journal_date, JournalEntry.created_at, JournalLine.line_number)
    return list(session.execute(query).all())


def build_account_ledger(
    *,
    account: ChartOfAccount,
    date_from: date | None,
    date_to: date | None,
    opening_rows: list[tuple[JournalLine, JournalEntry]],
    movement_rows: list[tuple[JournalLine, JournalEntry]],
) -> AccountLedgerRead:
    opening_balance = money(
        sum(
            (
                signed_amount(
                    normal_balance=account.normal_balance,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                )
                for line, _entry in opening_rows
            ),
            Decimal("0.00"),
        )
    )
    running_balance = opening_balance
    total_debits = Decimal("0.00")
    total_credits = Decimal("0.00")
    lines: list[AccountLedgerLineRead] = []

    for line, entry in movement_rows:
        total_debits = money(total_debits + line.debit_amount)
        total_credits = money(total_credits + line.credit_amount)
        running_balance = money(
            running_balance
            + signed_amount(
                normal_balance=account.normal_balance,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
            )
        )
        lines.append(
            AccountLedgerLineRead(
                journal_entry_id=entry.id,
                journal_line_id=line.id,
                journal_date=entry.journal_date,
                source_type=entry.source_type,
                source_id=entry.source_id,
                reference_number=entry.reference_number,
                description=entry.description,
                line_description=line.description,
                debit_amount=money(line.debit_amount),
                credit_amount=money(line.credit_amount),
                running_balance=running_balance,
            )
        )

    return AccountLedgerRead(
        tenant_id=account.tenant_id,
        society_id=account.society_id,
        account_id=account.id,
        account_code=account.account_code,
        account_name=account.account_name,
        account_type=account.account_type,
        normal_balance=account.normal_balance,
        date_from=date_from,
        date_to=date_to,
        opening_balance=opening_balance,
        total_debits=money(total_debits),
        total_credits=money(total_credits),
        closing_balance=running_balance,
        lines=lines,
    )


def get_account_ledger(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    account_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> AccountLedgerRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    account = load_account(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        account_id=account_id,
    )
    opening_rows = (
        list_posted_account_lines(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            account_id=account_id,
            before_date=date_from,
        )
        if date_from is not None
        else []
    )
    movement_rows = list_posted_account_lines(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
    )
    return build_account_ledger(
        account=account,
        date_from=date_from,
        date_to=date_to,
        opening_rows=opening_rows,
        movement_rows=movement_rows,
    )
