import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentSequence, Society, User
from app.schemas.document_sequence import DocumentSequenceUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class DocumentSequenceSocietyNotFoundError(Exception):
    pass


def ensure_society(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> Society:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise DocumentSequenceSocietyNotFoundError("Society not found.")
    return society


def default_invoice_sequence(*, tenant_context: TenantContext, society_id: uuid.UUID) -> DocumentSequence:
    return DocumentSequence(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        document_type="invoice",
        prefix="INV",
        include_period=True,
        include_financial_year=False,
        separator="-",
        next_sequence=1,
        padding=5,
        reset_policy="never",
        current_reset_key="GLOBAL",
    )


def get_or_create_invoice_sequence(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> DocumentSequence:
    ensure_society(session, tenant_context=tenant_context, society_id=society_id)
    sequence = session.scalar(
        select(DocumentSequence).where(
            DocumentSequence.tenant_id == tenant_context.tenant_id,
            DocumentSequence.society_id == society_id,
            DocumentSequence.document_type == "invoice",
        )
    )
    if sequence is not None:
        return sequence

    sequence = default_invoice_sequence(tenant_context=tenant_context, society_id=society_id)
    session.add(sequence)
    session.commit()
    session.refresh(sequence)
    return sequence


def update_invoice_sequence(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: DocumentSequenceUpdate,
    actor: User,
) -> DocumentSequence:
    sequence = get_or_create_invoice_sequence(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
    )
    sequence.prefix = payload.prefix.upper()
    sequence.include_period = payload.include_period
    sequence.include_financial_year = payload.include_financial_year
    sequence.separator = payload.separator
    sequence.next_sequence = payload.next_sequence
    sequence.padding = payload.padding
    sequence.reset_policy = payload.reset_policy

    record_audit_log(
        session,
        action="document_sequence.updated",
        entity_type="DocumentSequence",
        entity_id=sequence.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary="Invoice numbering settings updated",
        metadata={"society_id": str(society_id), "document_type": "invoice"},
    )
    session.commit()
    session.refresh(sequence)
    return sequence


def financial_year_token(value: date, start_month: int) -> str:
    start_year = value.year if value.month >= start_month else value.year - 1
    end_year = start_year + 1
    return f"FY{start_year % 100:02d}{end_year % 100:02d}"


def reset_key_for(sequence: DocumentSequence, invoice_date: date, financial_year_start_month: int) -> str:
    if sequence.reset_policy == "monthly":
        return invoice_date.strftime("%Y%m")
    if sequence.reset_policy == "financial_year":
        return financial_year_token(invoice_date, financial_year_start_month)
    return "GLOBAL"


def format_document_number(
    sequence: DocumentSequence,
    *,
    invoice_date: date,
    billing_period_start: date,
    financial_year_start_month: int,
) -> str:
    parts = [sequence.prefix]
    if sequence.include_financial_year:
        parts.append(financial_year_token(invoice_date, financial_year_start_month))
    if sequence.include_period:
        parts.append(billing_period_start.strftime("%Y%m"))
    parts.append(str(sequence.next_sequence).zfill(sequence.padding))
    return sequence.separator.join(parts)


def next_invoice_number(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice_date: date,
    billing_period_start: date,
) -> str:
    society = ensure_society(session, tenant_context=tenant_context, society_id=society_id)
    sequence = session.scalar(
        select(DocumentSequence)
        .where(
            DocumentSequence.tenant_id == tenant_context.tenant_id,
            DocumentSequence.society_id == society_id,
            DocumentSequence.document_type == "invoice",
        )
        .with_for_update()
    )
    if sequence is None:
        sequence = default_invoice_sequence(tenant_context=tenant_context, society_id=society_id)
        session.add(sequence)
        session.flush()

    reset_key = reset_key_for(sequence, invoice_date, society.financial_year_start_month)
    if sequence.current_reset_key != reset_key:
        sequence.current_reset_key = reset_key
        sequence.next_sequence = 1

    invoice_number = format_document_number(
        sequence,
        invoice_date=invoice_date,
        billing_period_start=billing_period_start,
        financial_year_start_month=society.financial_year_start_month,
    )
    sequence.next_sequence += 1
    return invoice_number
