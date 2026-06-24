import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ChargeType,
    Flat,
    Invoice,
    InvoiceLateFeeRule,
    InvoiceLineItem,
    JournalEntry,
    LateFeeApplication,
    LateFeeRule,
    Payment,
    PaymentAllocation,
    Society,
    User,
)
from app.schemas.late_fee import (
    LateFeeApplyResponse,
    LateFeePreviewRequest,
    LateFeePreviewResponse,
    LateFeePreviewRow,
    LateFeeRuleCreate,
    LateFeeRuleUpdate,
)
from app.services.audit import record_audit_log
from app.services.document_sequences import next_invoice_number
from app.services.invoices import InvoiceJournalPostingError, money, post_invoice_journal
from app.tenants.context import TenantContext


class LateFeeRuleAlreadyExistsError(Exception):
    pass


class LateFeeRuleNotFoundError(Exception):
    pass


class LateFeeSocietyNotFoundError(Exception):
    pass


class LateFeeReferenceInvalidError(Exception):
    pass


class LateFeeApplicationValidationError(Exception):
    def __init__(self, preview: LateFeePreviewResponse) -> None:
        self.preview = preview
        super().__init__("Late fee application has validation errors.")


class LateFeeJournalPostingError(Exception):
    pass


def ensure_society_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> None:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise LateFeeSocietyNotFoundError("Society not found.")


def ensure_late_fee_rule_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: LateFeeRuleCreate | LateFeeRuleUpdate,
    existing_rule_id: uuid.UUID | None = None,
) -> None:
    statement = select(LateFeeRule).where(
        LateFeeRule.tenant_id == tenant_context.tenant_id,
        LateFeeRule.society_id == society_id,
        LateFeeRule.name == payload.name,
    )
    if existing_rule_id is not None:
        statement = statement.where(LateFeeRule.id != existing_rule_id)
    if session.scalar(statement) is not None:
        raise LateFeeRuleAlreadyExistsError("Late fee rule name already exists.")


def ensure_charge_type_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    charge_type_id: uuid.UUID,
) -> None:
    charge_type = session.scalar(
        select(ChargeType).where(
            ChargeType.id == charge_type_id,
            ChargeType.tenant_id == tenant_context.tenant_id,
            ChargeType.society_id == society_id,
            ChargeType.status == "active",
        )
    )
    if charge_type is None:
        raise LateFeeReferenceInvalidError("Charge type must be active and belong to this society.")
    if charge_type.revenue_account_id is None:
        raise LateFeeReferenceInvalidError("Late fee charge type must have a revenue account.")


def list_late_fee_rules(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[LateFeeRule]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(LateFeeRule)
            .where(
                LateFeeRule.tenant_id == tenant_context.tenant_id,
                LateFeeRule.society_id == society_id,
            )
            .order_by(LateFeeRule.name)
        )
    )


def get_late_fee_rule_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    late_fee_rule_id: uuid.UUID,
) -> LateFeeRule:
    rule = session.scalar(
        select(LateFeeRule).where(
            LateFeeRule.id == late_fee_rule_id,
            LateFeeRule.tenant_id == tenant_context.tenant_id,
            LateFeeRule.society_id == society_id,
        )
    )
    if rule is None:
        raise LateFeeRuleNotFoundError("Late fee rule not found.")
    return rule


def create_late_fee_rule(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: LateFeeRuleCreate,
    actor: User,
) -> LateFeeRule:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    ensure_late_fee_rule_unique(session, tenant_context=tenant_context, society_id=society_id, payload=payload)
    ensure_charge_type_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        charge_type_id=payload.charge_type_id,
    )
    rule = LateFeeRule(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        charge_type_id=payload.charge_type_id,
        name=payload.name,
        calculation_method=payload.calculation_method,
        amount=payload.amount,
        grace_days=payload.grace_days,
        repeat_interval_days=payload.repeat_interval_days,
        max_applications_per_invoice=payload.max_applications_per_invoice,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        description=payload.description,
        status="active",
    )
    session.add(rule)
    session.flush()
    record_audit_log(
        session,
        action="late_fee_rule.created",
        entity_type="LateFeeRule",
        entity_id=rule.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Late fee rule created: {rule.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(rule)
    return rule


def update_late_fee_rule(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    late_fee_rule_id: uuid.UUID,
    payload: LateFeeRuleUpdate,
    actor: User,
) -> LateFeeRule:
    rule = get_late_fee_rule_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        late_fee_rule_id=late_fee_rule_id,
    )
    ensure_late_fee_rule_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        existing_rule_id=rule.id,
    )
    ensure_charge_type_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        charge_type_id=payload.charge_type_id,
    )
    rule.charge_type_id = payload.charge_type_id
    rule.name = payload.name
    rule.calculation_method = payload.calculation_method
    rule.amount = payload.amount
    rule.grace_days = payload.grace_days
    rule.repeat_interval_days = payload.repeat_interval_days
    rule.max_applications_per_invoice = payload.max_applications_per_invoice
    rule.effective_from = payload.effective_from
    rule.effective_to = payload.effective_to
    rule.description = payload.description
    record_audit_log(
        session,
        action="late_fee_rule.updated",
        entity_type="LateFeeRule",
        entity_id=rule.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Late fee rule updated: {rule.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(rule)
    return rule


def change_late_fee_rule_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    late_fee_rule_id: uuid.UUID,
    status: str,
    actor: User,
) -> LateFeeRule:
    rule = get_late_fee_rule_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        late_fee_rule_id=late_fee_rule_id,
    )
    rule.status = status
    record_audit_log(
        session,
        action="late_fee_rule.inactivated" if status == "inactive" else "late_fee_rule.activated",
        entity_type="LateFeeRule",
        entity_id=rule.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Late fee rule {status}: {rule.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(rule)
    return rule


def late_fee_rule_is_effective(rule: LateFeeRule, as_of_date: date) -> bool:
    return rule.effective_from <= as_of_date and (rule.effective_to is None or rule.effective_to >= as_of_date)


def calculate_penalty_amount(rule: LateFeeRule, amount_due: Decimal) -> Decimal:
    if rule.calculation_method == "fixed":
        return money(rule.amount)
    return money(amount_due * rule.amount / Decimal("100.00"))


def due_late_fee_application_dates(
    *,
    rule: LateFeeRule,
    invoice: Invoice,
    as_of_date: date,
    existing_applications: list[LateFeeApplication],
) -> list[date]:
    first_eligible_date = invoice.due_date + timedelta(days=rule.grace_days + 1)
    start_date = max(first_eligible_date, rule.effective_from)
    end_date = min(as_of_date, rule.effective_to) if rule.effective_to is not None else as_of_date
    if end_date < start_date:
        return []

    existing_dates = {application.applied_as_of_date for application in existing_applications}
    max_applications = rule.max_applications_per_invoice
    if rule.repeat_interval_days is None:
        candidate_dates = [start_date]
        max_applications = 1 if max_applications is None else min(max_applications, 1)
    else:
        if existing_dates:
            start_date = max(start_date, max(existing_dates) + timedelta(days=rule.repeat_interval_days))
        candidate_dates = []
        candidate_date = start_date
        while candidate_date <= end_date:
            candidate_dates.append(candidate_date)
            candidate_date += timedelta(days=rule.repeat_interval_days)

    remaining_applications = None
    if max_applications is not None:
        remaining_applications = max(max_applications - len(existing_applications), 0)
        if remaining_applications == 0:
            return []

    due_dates: list[date] = []
    for candidate_date in candidate_dates:
        if candidate_date in existing_dates:
            continue
        due_dates.append(candidate_date)
        if remaining_applications is not None and len(due_dates) >= remaining_applications:
            break
    return due_dates


def build_late_fee_preview(
    *,
    payload: LateFeePreviewRequest,
    rules: list[LateFeeRule],
    invoices: list[Invoice],
    flats_by_id: dict[uuid.UUID, Flat],
    applications_by_invoice_rule: dict[tuple[uuid.UUID, uuid.UUID], list[LateFeeApplication]],
    penalty_invoice_ids: set[uuid.UUID],
    invoice_late_fee_rule_ids: dict[uuid.UUID, set[uuid.UUID]] | None = None,
) -> LateFeePreviewResponse:
    rows: list[LateFeePreviewRow] = []
    enforce_invoice_assignments = invoice_late_fee_rule_ids is not None
    invoice_late_fee_rule_ids = invoice_late_fee_rule_ids or {}
    for invoice in invoices:
        flat = flats_by_id.get(invoice.flat_id)
        if flat is None or invoice.id in penalty_invoice_ids:
            continue
        for rule in rules:
            if enforce_invoice_assignments and rule.id not in invoice_late_fee_rule_ids.get(invoice.id, set()):
                continue
            errors: list[str] = []
            days_overdue = max((payload.as_of_date - invoice.due_date).days, 0)
            existing_applications = applications_by_invoice_rule.get((invoice.id, rule.id), [])
            due_application_dates = due_late_fee_application_dates(
                rule=rule,
                invoice=invoice,
                as_of_date=payload.as_of_date,
                existing_applications=existing_applications,
            )

            if payload.as_of_date <= invoice.due_date + timedelta(days=rule.grace_days):
                errors.append("Invoice is still within its grace period.")
            if rule.max_applications_per_invoice is not None and len(existing_applications) >= rule.max_applications_per_invoice:
                errors.append("Maximum applications reached for this invoice.")
            if not due_application_dates and not errors:
                errors.append("No late fee application is due for this invoice and rule as of this date.")

            penalty_amount = calculate_penalty_amount(rule, invoice.amount_due)
            if penalty_amount <= 0:
                errors.append("Penalty amount is zero.")

            if errors or not due_application_dates:
                rows.append(
                    LateFeePreviewRow(
                        original_invoice_id=invoice.id,
                        original_invoice_number=invoice.invoice_number,
                        flat_id=invoice.flat_id,
                        flat_number=flat.flat_number,
                        due_date=invoice.due_date,
                        applied_as_of_date=payload.as_of_date,
                        days_overdue=days_overdue,
                        amount_due=money(invoice.amount_due),
                        late_fee_rule_id=rule.id,
                        late_fee_rule_name=rule.name,
                        status="skipped",
                        errors=errors,
                        penalty_amount=Decimal("0.00"),
                    )
                )
                continue

            for application_date in due_application_dates:
                rows.append(
                    LateFeePreviewRow(
                        original_invoice_id=invoice.id,
                        original_invoice_number=invoice.invoice_number,
                        flat_id=invoice.flat_id,
                        flat_number=flat.flat_number,
                        due_date=invoice.due_date,
                        applied_as_of_date=application_date,
                        days_overdue=max((application_date - invoice.due_date).days, 0),
                        amount_due=money(invoice.amount_due),
                        late_fee_rule_id=rule.id,
                        late_fee_rule_name=rule.name,
                        status="valid",
                        errors=[],
                        penalty_amount=penalty_amount,
                    )
                )

    valid_rows = sum(1 for row in rows if row.status == "valid")
    invalid_rows = sum(1 for row in rows if row.status == "invalid")
    skipped_rows = sum(1 for row in rows if row.status == "skipped")
    return LateFeePreviewResponse(
        as_of_date=payload.as_of_date,
        invoice_count=valid_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        skipped_rows=skipped_rows,
        total_penalty_amount=money(sum((row.penalty_amount for row in rows if row.status == "valid"), Decimal("0.00"))),
        rows=rows,
    )


def load_late_fee_preview_context(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: LateFeePreviewRequest,
) -> tuple[
    list[LateFeeRule],
    list[Invoice],
    dict[uuid.UUID, Flat],
    dict[tuple[uuid.UUID, uuid.UUID], list[LateFeeApplication]],
    set[uuid.UUID],
    dict[uuid.UUID, set[uuid.UUID]],
]:
    rules = list(
        session.scalars(
            select(LateFeeRule).where(
                LateFeeRule.tenant_id == tenant_context.tenant_id,
                LateFeeRule.society_id == society_id,
                LateFeeRule.status == "active",
                LateFeeRule.id.in_(payload.late_fee_rule_ids),
            )
        )
    )
    if set(payload.late_fee_rule_ids) != {rule.id for rule in rules}:
        raise LateFeeReferenceInvalidError("One or more selected late fee rules are not active.")

    invoices = list(
        session.scalars(
            select(Invoice).where(
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
                Invoice.status.in_(["issued", "partially_paid", "overdue"]),
                Invoice.amount_due > 0,
                Invoice.due_date < payload.as_of_date,
            )
        )
    )
    flat_ids = {invoice.flat_id for invoice in invoices}
    invoice_late_fee_rows = list(
        session.scalars(
            select(InvoiceLateFeeRule).where(
                InvoiceLateFeeRule.tenant_id == tenant_context.tenant_id,
                InvoiceLateFeeRule.society_id == society_id,
                InvoiceLateFeeRule.invoice_id.in_({invoice.id for invoice in invoices}),
                InvoiceLateFeeRule.late_fee_rule_id.in_(payload.late_fee_rule_ids),
                InvoiceLateFeeRule.status == "active",
            )
        )
    )
    invoice_late_fee_rule_ids: dict[uuid.UUID, set[uuid.UUID]] = {}
    for row in invoice_late_fee_rows:
        invoice_late_fee_rule_ids.setdefault(row.invoice_id, set()).add(row.late_fee_rule_id)
    flats_by_id = {
        flat.id: flat
        for flat in session.scalars(
            select(Flat).where(
                Flat.id.in_(flat_ids),
                Flat.tenant_id == tenant_context.tenant_id,
                Flat.society_id == society_id,
            )
        )
    }
    applications = list(
        session.scalars(
            select(LateFeeApplication).where(
                LateFeeApplication.tenant_id == tenant_context.tenant_id,
                LateFeeApplication.society_id == society_id,
                LateFeeApplication.late_fee_rule_id.in_(payload.late_fee_rule_ids),
                LateFeeApplication.status == "active",
            )
        )
    )
    applications_by_invoice_rule: dict[tuple[uuid.UUID, uuid.UUID], list[LateFeeApplication]] = {}
    for application in applications:
        applications_by_invoice_rule.setdefault(
            (application.original_invoice_id, application.late_fee_rule_id),
            [],
        ).append(application)
    penalty_invoice_ids = {application.penalty_invoice_id for application in applications}
    return rules, invoices, flats_by_id, applications_by_invoice_rule, penalty_invoice_ids, invoice_late_fee_rule_ids


def preview_late_fee_application(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: LateFeePreviewRequest,
) -> LateFeePreviewResponse:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    rules, invoices, flats_by_id, applications_by_invoice_rule, penalty_invoice_ids, invoice_late_fee_rule_ids = load_late_fee_preview_context(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    return build_late_fee_preview(
        payload=payload,
        rules=rules,
        invoices=invoices,
        flats_by_id=flats_by_id,
        applications_by_invoice_rule=applications_by_invoice_rule,
        penalty_invoice_ids=penalty_invoice_ids,
        invoice_late_fee_rule_ids=invoice_late_fee_rule_ids,
    )


def apply_late_fees(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: LateFeePreviewRequest,
    actor: User,
) -> LateFeeApplyResponse:
    preview = preview_late_fee_application(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    if preview.invalid_rows:
        raise LateFeeApplicationValidationError(preview)

    if not preview.valid_rows:
        return LateFeeApplyResponse(generated_count=0, invoice_ids=[])

    original_invoice_ids = [row.original_invoice_id for row in preview.rows if row.status == "valid"]
    original_invoices = {
        invoice.id: invoice
        for invoice in session.scalars(
            select(Invoice).where(
                Invoice.id.in_(original_invoice_ids),
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
            )
        )
    }
    rule_ids = [row.late_fee_rule_id for row in preview.rows if row.status == "valid"]
    rules = {
        rule.id: rule
        for rule in session.scalars(
            select(LateFeeRule).where(
                LateFeeRule.id.in_(rule_ids),
                LateFeeRule.tenant_id == tenant_context.tenant_id,
                LateFeeRule.society_id == society_id,
            )
        )
    }

    generated_invoice_ids: list[uuid.UUID] = []
    for row in preview.rows:
        if row.status != "valid":
            continue
        original_invoice = original_invoices[row.original_invoice_id]
        rule = rules[row.late_fee_rule_id]
        invoice = Invoice(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            flat_id=row.flat_id,
            owner_id=original_invoice.owner_id,
            invoice_number=next_invoice_number(
                session,
                tenant_context=tenant_context,
                society_id=society_id,
                invoice_date=row.applied_as_of_date,
                billing_period_start=row.applied_as_of_date,
            ),
            invoice_date=row.applied_as_of_date,
            due_date=row.applied_as_of_date,
            billing_period_start=row.applied_as_of_date,
            billing_period_end=row.applied_as_of_date,
            total_amount=row.penalty_amount,
            amount_paid=Decimal("0.00"),
            amount_due=row.penalty_amount,
            status="issued",
            notes=f"Late fee for invoice {row.original_invoice_number}",
        )
        session.add(invoice)
        session.flush()
        invoice_line = InvoiceLineItem(
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            invoice_id=invoice.id,
            charge_type_id=rule.charge_type_id,
            billing_rule_id=None,
            line_number=1,
            description=f"{rule.name} for {row.original_invoice_number}",
            quantity=Decimal("1.00"),
            unit_amount=row.penalty_amount,
            line_amount=row.penalty_amount,
        )
        session.add(invoice_line)
        try:
            post_invoice_journal(
                session,
                tenant_context=tenant_context,
                society_id=society_id,
                invoice=invoice,
                line_items=[invoice_line],
            )
        except InvoiceJournalPostingError as exc:
            raise LateFeeJournalPostingError(str(exc)) from exc
        session.add(
            LateFeeApplication(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                late_fee_rule_id=rule.id,
                original_invoice_id=row.original_invoice_id,
                penalty_invoice_id=invoice.id,
                applied_as_of_date=row.applied_as_of_date,
                penalty_amount=row.penalty_amount,
                status="active",
            )
        )
        generated_invoice_ids.append(invoice.id)

    record_audit_log(
        session,
        action="late_fee_application.completed",
        entity_type="Invoice",
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Late fee application completed: {len(generated_invoice_ids)} invoices",
        metadata={
            "society_id": str(society_id),
            "as_of_date": payload.as_of_date.isoformat(),
            "invoice_ids": [str(invoice_id) for invoice_id in generated_invoice_ids],
            "late_fee_rule_ids": [str(rule_id) for rule_id in payload.late_fee_rule_ids],
        },
    )
    session.commit()
    return LateFeeApplyResponse(generated_count=len(generated_invoice_ids), invoice_ids=generated_invoice_ids)


def amount_paid_by_cutoff(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    invoice_id: uuid.UUID,
    cutoff_date: date,
) -> Decimal:
    amount = session.scalar(
        select(func.coalesce(func.sum(PaymentAllocation.allocated_amount), 0))
        .join(Payment, Payment.id == PaymentAllocation.payment_id)
        .where(
            PaymentAllocation.tenant_id == tenant_context.tenant_id,
            PaymentAllocation.society_id == society_id,
            PaymentAllocation.invoice_id == invoice_id,
            PaymentAllocation.status == "active",
            Payment.tenant_id == tenant_context.tenant_id,
            Payment.society_id == society_id,
            Payment.status == "received",
            Payment.payment_date <= cutoff_date,
        )
    )
    return money(Decimal(amount or 0))


def auto_cancel_invalid_unpaid_penalties(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    original_invoice_ids: list[uuid.UUID],
    actor: User,
) -> list[uuid.UUID]:
    if not original_invoice_ids:
        return []

    applications = list(
        session.scalars(
            select(LateFeeApplication)
            .where(
                LateFeeApplication.tenant_id == tenant_context.tenant_id,
                LateFeeApplication.society_id == society_id,
                LateFeeApplication.original_invoice_id.in_(original_invoice_ids),
                LateFeeApplication.status == "active",
            )
            .with_for_update()
        )
    )
    if not applications:
        return []

    original_invoices = {
        invoice.id: invoice
        for invoice in session.scalars(
            select(Invoice).where(
                Invoice.id.in_({application.original_invoice_id for application in applications}),
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
            )
        )
    }
    rules = {
        rule.id: rule
        for rule in session.scalars(
            select(LateFeeRule).where(
                LateFeeRule.id.in_({application.late_fee_rule_id for application in applications}),
                LateFeeRule.tenant_id == tenant_context.tenant_id,
                LateFeeRule.society_id == society_id,
            )
        )
    }
    penalty_invoices = {
        invoice.id: invoice
        for invoice in session.scalars(
            select(Invoice)
            .where(
                Invoice.id.in_({application.penalty_invoice_id for application in applications}),
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.society_id == society_id,
            )
            .with_for_update()
        )
    }

    cancelled_invoice_ids: list[uuid.UUID] = []
    for application in applications:
        original_invoice = original_invoices.get(application.original_invoice_id)
        rule = rules.get(application.late_fee_rule_id)
        penalty_invoice = penalty_invoices.get(application.penalty_invoice_id)
        if original_invoice is None or rule is None or penalty_invoice is None:
            continue
        if penalty_invoice.status == "cancelled" or penalty_invoice.amount_paid > 0:
            continue

        cutoff_date = application.applied_as_of_date - timedelta(days=1)
        paid_by_cutoff = amount_paid_by_cutoff(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            invoice_id=original_invoice.id,
            cutoff_date=cutoff_date,
        )
        if paid_by_cutoff < original_invoice.total_amount:
            continue

        penalty_invoice.status = "cancelled"
        penalty_invoice.amount_due = Decimal("0.00")
        penalty_invoice.notes = (
            f"{penalty_invoice.notes}\nAuto-cancelled: original invoice paid within grace period."
            if penalty_invoice.notes
            else "Auto-cancelled: original invoice paid within grace period."
        )
        application.status = "cancelled"
        if penalty_invoice.journal_entry_id is not None:
            journal_entry = session.scalar(
                select(JournalEntry).where(
                    JournalEntry.id == penalty_invoice.journal_entry_id,
                    JournalEntry.tenant_id == tenant_context.tenant_id,
                    JournalEntry.society_id == society_id,
                )
            )
            if journal_entry is not None:
                journal_entry.status = "reversed"
        record_audit_log(
            session,
            action="late_fee_application.auto_cancelled",
            entity_type="Invoice",
            entity_id=penalty_invoice.id,
            actor_user_id=actor.id,
            tenant_id=tenant_context.tenant_id,
            summary=f"Penalty invoice auto-cancelled: {penalty_invoice.invoice_number}",
            metadata={
                "society_id": str(society_id),
                "original_invoice_id": str(original_invoice.id),
                "late_fee_rule_id": str(rule.id),
                "paid_by_cutoff": str(paid_by_cutoff),
                "cutoff_date": cutoff_date.isoformat(),
                "applied_as_of_date": application.applied_as_of_date.isoformat(),
            },
        )
        cancelled_invoice_ids.append(penalty_invoice.id)

    return cancelled_invoice_ids
