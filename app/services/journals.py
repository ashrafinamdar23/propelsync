import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, JournalEntry, JournalLine, Society, User
from app.schemas.journal import JournalEntryCreate, OpeningBalanceJournalCreate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class JournalSocietyNotFoundError(Exception):
    pass


class JournalAccountInvalidError(Exception):
    pass


class JournalValidationError(Exception):
    pass


class JournalReversalInvalidError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise JournalSocietyNotFoundError("Society not found.")


def validate_journal_lines(payload: JournalEntryCreate) -> None:
    total_debit = money(sum((line.debit_amount for line in payload.lines), Decimal("0.00")))
    total_credit = money(sum((line.credit_amount for line in payload.lines), Decimal("0.00")))
    if total_debit <= Decimal("0.00") or total_credit <= Decimal("0.00"):
        raise JournalValidationError("Journal entry must have debit and credit lines.")
    if total_debit != total_credit:
        raise JournalValidationError("Journal entry debits and credits must balance.")


def validate_opening_balance_lines(payload: OpeningBalanceJournalCreate) -> None:
    total_debit = money(sum((line.debit_amount for line in payload.lines), Decimal("0.00")))
    total_credit = money(sum((line.credit_amount for line in payload.lines), Decimal("0.00")))
    if total_debit <= Decimal("0.00") or total_credit <= Decimal("0.00"):
        raise JournalValidationError("Opening balance must have debit and credit lines.")
    if total_debit != total_credit:
        raise JournalValidationError("Opening balance debits and credits must balance.")


def load_active_accounts(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    account_ids: list[uuid.UUID],
) -> dict[uuid.UUID, ChartOfAccount]:
    accounts = {
        account.id: account
        for account in session.scalars(
            select(ChartOfAccount).where(
                ChartOfAccount.id.in_(account_ids),
                ChartOfAccount.tenant_id == tenant_context.tenant_id,
                ChartOfAccount.society_id == society_id,
                ChartOfAccount.status == "active",
            )
        )
    }
    if set(account_ids) != set(accounts):
        raise JournalAccountInvalidError("All journal accounts must be active and belong to this society.")
    return accounts


def list_journal_entries(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[JournalEntry]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(JournalEntry)
            .where(
                JournalEntry.tenant_id == tenant_context.tenant_id,
                JournalEntry.society_id == society_id,
            )
            .order_by(JournalEntry.journal_date.desc(), JournalEntry.created_at.desc())
        )
    )


def list_journal_lines(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    journal_entry_id: uuid.UUID,
) -> list[JournalLine]:
    return list(
        session.scalars(
            select(JournalLine)
            .where(
                JournalLine.tenant_id == tenant_context.tenant_id,
                JournalLine.society_id == society_id,
                JournalLine.journal_entry_id == journal_entry_id,
            )
            .order_by(JournalLine.line_number)
        )
    )


def get_journal_entry_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    journal_entry_id: uuid.UUID,
) -> JournalEntry:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    entry = session.scalar(
        select(JournalEntry).where(
            JournalEntry.id == journal_entry_id,
            JournalEntry.tenant_id == tenant_context.tenant_id,
            JournalEntry.society_id == society_id,
        )
    )
    if entry is None:
        raise JournalValidationError("Journal entry not found.")
    return entry


def create_manual_journal_entry(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: JournalEntryCreate,
    actor: User,
) -> JournalEntry:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    validate_journal_lines(payload)
    load_active_accounts(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        account_ids=[line.account_id for line in payload.lines],
    )
    entry = JournalEntry(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        journal_date=payload.journal_date,
        source_type="manual",
        reference_number=payload.reference_number,
        description=payload.description,
        status="posted",
        notes=payload.notes,
    )
    session.add(entry)
    session.flush()

    for line_number, line in enumerate(payload.lines, start=1):
        session.add(
            JournalLine(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                journal_entry_id=entry.id,
                account_id=line.account_id,
                line_number=line_number,
                description=line.description,
                debit_amount=money(line.debit_amount),
                credit_amount=money(line.credit_amount),
            )
        )

    record_audit_log(
        session,
        action="journal_entry.created",
        entity_type="JournalEntry",
        entity_id=entry.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Manual journal posted: {entry.description}",
        metadata={"society_id": str(society_id), "line_count": len(payload.lines)},
    )
    session.commit()
    session.refresh(entry)
    return entry


def create_opening_balance_journal_entry(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: OpeningBalanceJournalCreate,
    actor: User,
) -> JournalEntry:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    validate_opening_balance_lines(payload)
    load_active_accounts(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        account_ids=[line.account_id for line in payload.lines],
    )
    entry = JournalEntry(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        journal_date=payload.opening_date,
        source_type="opening_balance",
        reference_number=payload.reference_number,
        description=f"Opening balances as of {payload.opening_date.isoformat()}",
        status="posted",
        notes=payload.notes,
    )
    session.add(entry)
    session.flush()

    for line_number, line in enumerate(payload.lines, start=1):
        session.add(
            JournalLine(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                journal_entry_id=entry.id,
                account_id=line.account_id,
                line_number=line_number,
                description=line.description,
                debit_amount=money(line.debit_amount),
                credit_amount=money(line.credit_amount),
            )
        )

    record_audit_log(
        session,
        action="journal_entry.opening_balance_created",
        entity_type="JournalEntry",
        entity_id=entry.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Opening balance journal posted for {payload.opening_date.isoformat()}",
        metadata={"society_id": str(society_id), "line_count": len(payload.lines)},
    )
    session.commit()
    session.refresh(entry)
    return entry


def reverse_journal_entry(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    journal_entry_id: uuid.UUID,
    reason: str,
    actor: User,
) -> JournalEntry:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    entry = session.scalar(
        select(JournalEntry).where(
            JournalEntry.id == journal_entry_id,
            JournalEntry.tenant_id == tenant_context.tenant_id,
            JournalEntry.society_id == society_id,
        )
    )
    if entry is None:
        raise JournalValidationError("Journal entry not found.")
    if entry.status == "reversed":
        raise JournalReversalInvalidError("Journal entry is already reversed.")
    if entry.source_type not in {"manual", "opening_balance"}:
        raise JournalReversalInvalidError(
            "Only manual and opening balance journals can be reversed directly."
        )

    entry.status = "reversed"
    entry.notes = f"{entry.notes}\nReversal reason: {reason}" if entry.notes else f"Reversal reason: {reason}"
    record_audit_log(
        session,
        action="journal_entry.reversed",
        entity_type="JournalEntry",
        entity_id=entry.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Journal reversed: {entry.description}",
        metadata={
            "society_id": str(society_id),
            "source_type": entry.source_type,
            "reason": reason,
        },
    )
    session.commit()
    session.refresh(entry)
    return entry
