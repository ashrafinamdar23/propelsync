import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AccountTransfer, ChartOfAccount, JournalEntry, JournalLine, Society, User
from app.schemas.account_transfer import AccountTransferCreate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class AccountTransferSocietyNotFoundError(Exception):
    pass


class AccountTransferAccountInvalidError(Exception):
    pass


class AccountTransferValidationError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise AccountTransferSocietyNotFoundError("Society not found.")


def list_account_transfers(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[AccountTransfer]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(AccountTransfer)
            .where(
                AccountTransfer.tenant_id == tenant_context.tenant_id,
                AccountTransfer.society_id == society_id,
            )
            .order_by(AccountTransfer.transfer_date.desc(), AccountTransfer.created_at.desc())
        )
    )


def load_transfer_accounts(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: AccountTransferCreate,
) -> dict[uuid.UUID, ChartOfAccount]:
    if payload.from_account_id == payload.to_account_id:
        raise AccountTransferValidationError("Transfer source and destination accounts must be different.")
    account_ids = [payload.from_account_id, payload.to_account_id]
    accounts = {
        account.id: account
        for account in session.scalars(
            select(ChartOfAccount).where(
                ChartOfAccount.id.in_(account_ids),
                ChartOfAccount.tenant_id == tenant_context.tenant_id,
                ChartOfAccount.society_id == society_id,
                ChartOfAccount.account_type == "asset",
                ChartOfAccount.status == "active",
            )
        )
    }
    if set(account_ids) != set(accounts):
        raise AccountTransferAccountInvalidError(
            "Transfer accounts must be active asset accounts and belong to this society."
        )
    return accounts


def create_account_transfer(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: AccountTransferCreate,
    actor: User,
) -> AccountTransfer:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    accounts = load_transfer_accounts(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    transfer_amount = money(payload.amount)
    transfer = AccountTransfer(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        transfer_date=payload.transfer_date,
        amount=transfer_amount,
        transfer_mode=payload.transfer_mode,
        reference_number=payload.reference_number,
        description=payload.description,
        status="posted",
        notes=payload.notes,
    )
    session.add(transfer)
    session.flush()

    from_account = accounts[payload.from_account_id]
    to_account = accounts[payload.to_account_id]
    journal_entry = JournalEntry(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        journal_date=payload.transfer_date,
        source_type="transfer",
        source_id=transfer.id,
        reference_number=payload.reference_number,
        description=payload.description,
        status="posted",
        notes=payload.notes,
    )
    session.add(journal_entry)
    session.flush()

    transfer.journal_entry_id = journal_entry.id
    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=payload.to_account_id,
            line_number=1,
            description=f"Transfer in to {to_account.account_name}",
            debit_amount=transfer_amount,
            credit_amount=Decimal("0.00"),
        )
    )
    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=payload.from_account_id,
            line_number=2,
            description=f"Transfer out from {from_account.account_name}",
            debit_amount=Decimal("0.00"),
            credit_amount=transfer_amount,
        )
    )

    record_audit_log(
        session,
        action="account_transfer.created",
        entity_type="AccountTransfer",
        entity_id=transfer.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Account transfer posted: {transfer.amount}",
        metadata={
            "society_id": str(society_id),
            "from_account_id": str(payload.from_account_id),
            "to_account_id": str(payload.to_account_id),
            "journal_entry_id": str(journal_entry.id),
        },
    )
    session.commit()
    session.refresh(transfer)
    return transfer
