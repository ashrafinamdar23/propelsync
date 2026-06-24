import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, JournalEntry, JournalLine, OtherIncomeReceipt, Society, User
from app.schemas.other_income import OtherIncomeReceiptCreate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class OtherIncomeSocietyNotFoundError(Exception):
    pass


class OtherIncomeAccountInvalidError(Exception):
    pass


class OtherIncomeReceiptNotFoundError(Exception):
    pass


class OtherIncomeReceiptInvalidError(Exception):
    pass


MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def ensure_society_exists(session: Session, *, tenant_context: TenantContext, society_id: uuid.UUID) -> None:
    society = session.scalar(
        select(Society).where(Society.id == society_id, Society.tenant_id == tenant_context.tenant_id)
    )
    if society is None:
        raise OtherIncomeSocietyNotFoundError("Society not found.")


def list_other_income_receipts(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[OtherIncomeReceipt]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(OtherIncomeReceipt)
            .where(
                OtherIncomeReceipt.tenant_id == tenant_context.tenant_id,
                OtherIncomeReceipt.society_id == society_id,
            )
            .order_by(OtherIncomeReceipt.receipt_date.desc(), OtherIncomeReceipt.created_at.desc())
        )
    )


def load_receipt_accounts(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    income_account_id: uuid.UUID,
    deposit_account_id: uuid.UUID,
) -> tuple[ChartOfAccount, ChartOfAccount]:
    income_account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == income_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "income",
            ChartOfAccount.status == "active",
        )
    )
    if income_account is None:
        raise OtherIncomeAccountInvalidError("Income account must be an active income account.")

    deposit_account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == deposit_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "asset",
            ChartOfAccount.status == "active",
        )
    )
    if deposit_account is None:
        raise OtherIncomeAccountInvalidError("Deposit account must be an active asset account.")
    return income_account, deposit_account


def create_other_income_receipt(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: OtherIncomeReceiptCreate,
    actor: User,
) -> OtherIncomeReceipt:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    income_account, deposit_account = load_receipt_accounts(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        income_account_id=payload.income_account_id,
        deposit_account_id=payload.deposit_account_id,
    )
    amount = money(payload.amount)
    receipt = OtherIncomeReceipt(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        income_account_id=payload.income_account_id,
        deposit_account_id=payload.deposit_account_id,
        receipt_date=payload.receipt_date,
        payer_name=payload.payer_name,
        payer_type=payload.payer_type,
        amount=amount,
        receipt_mode=payload.receipt_mode,
        reference_number=payload.reference_number,
        description=payload.description,
        status="received",
        notes=payload.notes,
    )
    session.add(receipt)
    session.flush()

    journal_entry = JournalEntry(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        journal_date=payload.receipt_date,
        source_type="other_income",
        source_id=receipt.id,
        reference_number=payload.reference_number,
        description=payload.description,
        status="posted",
        notes=payload.notes,
    )
    session.add(journal_entry)
    session.flush()
    receipt.journal_entry_id = journal_entry.id

    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=deposit_account.id,
            line_number=1,
            description=f"Receipt deposited to {deposit_account.account_name}",
            debit_amount=amount,
            credit_amount=Decimal("0.00"),
        )
    )
    session.add(
        JournalLine(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            journal_entry_id=journal_entry.id,
            account_id=income_account.id,
            line_number=2,
            description=f"Income: {income_account.account_name}",
            debit_amount=Decimal("0.00"),
            credit_amount=amount,
        )
    )

    record_audit_log(
        session,
        action="other_income_receipt.created",
        entity_type="OtherIncomeReceipt",
        entity_id=receipt.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Other income receipt posted: {receipt.amount}",
        metadata={
            "society_id": str(society_id),
            "income_account_id": str(payload.income_account_id),
            "deposit_account_id": str(payload.deposit_account_id),
            "journal_entry_id": str(journal_entry.id),
        },
    )
    session.commit()
    session.refresh(receipt)
    return receipt


def get_other_income_receipt_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    receipt_id: uuid.UUID,
) -> OtherIncomeReceipt:
    receipt = session.scalar(
        select(OtherIncomeReceipt).where(
            OtherIncomeReceipt.id == receipt_id,
            OtherIncomeReceipt.tenant_id == tenant_context.tenant_id,
            OtherIncomeReceipt.society_id == society_id,
        )
    )
    if receipt is None:
        raise OtherIncomeReceiptNotFoundError("Other income receipt not found.")
    return receipt


def reverse_other_income_receipt(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    receipt_id: uuid.UUID,
    reason: str,
    actor: User,
) -> OtherIncomeReceipt:
    receipt = get_other_income_receipt_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        receipt_id=receipt_id,
    )
    if receipt.status == "reversed":
        raise OtherIncomeReceiptInvalidError("Other income receipt is already reversed.")
    receipt.status = "reversed"
    receipt.notes = f"{receipt.notes}\nReversal reason: {reason}" if receipt.notes else f"Reversal reason: {reason}"
    if receipt.journal_entry_id is not None:
        journal_entry = session.scalar(
            select(JournalEntry).where(
                JournalEntry.id == receipt.journal_entry_id,
                JournalEntry.tenant_id == tenant_context.tenant_id,
                JournalEntry.society_id == society_id,
            )
        )
        if journal_entry is not None:
            journal_entry.status = "reversed"

    record_audit_log(
        session,
        action="other_income_receipt.reversed",
        entity_type="OtherIncomeReceipt",
        entity_id=receipt.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Other income receipt reversed: {receipt.amount}",
        metadata={"society_id": str(society_id), "reason": reason},
    )
    session.commit()
    session.refresh(receipt)
    return receipt
