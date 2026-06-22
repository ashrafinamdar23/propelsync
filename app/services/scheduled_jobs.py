import uuid
from calendar import monthrange
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BillingRule, LateFeeRule, ScheduledJobRun, Society, User
from app.schemas.invoice_generation import InvoiceGenerationRequest
from app.schemas.late_fee import LateFeePreviewRequest
from app.schemas.scheduled_job import (
    ScheduledBillingRuleDueRead,
    ScheduledDueWorkRead,
    ScheduledLateFeeRuleDueRead,
    ScheduledRunDueJobsRequest,
    ScheduledRunDueJobsResponse,
    ScheduledJobRunRead,
)
from app.services.invoices import confirm_invoice_generation
from app.services.late_fees import apply_late_fees
from app.services.late_fees import preview_late_fee_application
from app.tenants.context import TenantContext


class ScheduledJobSocietyNotFoundError(Exception):
    pass


class ScheduledJobExecutionError(Exception):
    pass


FREQUENCY_MONTHS = {
    "monthly": 1,
    "quarterly": 3,
    "half_yearly": 6,
    "yearly": 12,
    "one_time": 1,
}


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def clamped_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, monthrange(year, month)[1]))


def due_date_for(invoice_date: date, due_day: int) -> date:
    due_date = clamped_day(invoice_date.year, invoice_date.month, due_day)
    if due_date < invoice_date:
        next_month = add_months(month_start(invoice_date), 1)
        due_date = clamped_day(next_month.year, next_month.month, due_day)
    return due_date


def billing_period_for(rule: BillingRule, generation_date: date) -> tuple[date, date]:
    months = FREQUENCY_MONTHS.get(rule.frequency, 1)
    period_start = month_start(generation_date)
    if rule.billing_period_timing == "next_period":
        period_start = add_months(period_start, months)
    period_end = add_months(period_start, months) - timedelta(days=1)
    return period_start, period_end


def next_generation_date_for(rule: BillingRule) -> date | None:
    if rule.next_generation_date is None or rule.frequency == "one_time":
        return None
    months = FREQUENCY_MONTHS.get(rule.frequency, 1)
    return add_months(rule.next_generation_date, months)


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
        raise ScheduledJobSocietyNotFoundError("Society not found.")


def list_due_billing_rules(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> list[ScheduledBillingRuleDueRead]:
    rules = list(
        session.scalars(
            select(BillingRule)
            .where(
                BillingRule.tenant_id == tenant_context.tenant_id,
                BillingRule.society_id == society_id,
                BillingRule.status == "active",
                BillingRule.calculation_method != "manual",
                BillingRule.next_generation_date.is_not(None),
                BillingRule.next_generation_date <= as_of_date,
                BillingRule.effective_from <= as_of_date,
                (BillingRule.effective_to.is_(None) | (BillingRule.effective_to >= as_of_date)),
            )
            .order_by(BillingRule.next_generation_date, BillingRule.name)
        )
    )
    return [
        ScheduledBillingRuleDueRead(
            billing_rule_id=rule.id,
            billing_rule_name=rule.name,
            charge_type_id=rule.charge_type_id,
            next_generation_date=rule.next_generation_date,
            frequency=rule.frequency,
            generation_day=rule.generation_day,
            due_day=rule.due_day,
            status="due",
            reason="next_generation_date is on or before as_of_date",
        )
        for rule in rules
    ]


def list_due_late_fee_rules(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> list[ScheduledLateFeeRuleDueRead]:
    rules = list(
        session.scalars(
            select(LateFeeRule)
            .where(
                LateFeeRule.tenant_id == tenant_context.tenant_id,
                LateFeeRule.society_id == society_id,
                LateFeeRule.status == "active",
                LateFeeRule.effective_from <= as_of_date,
            )
            .order_by(LateFeeRule.name)
        )
    )
    due_rules: list[ScheduledLateFeeRuleDueRead] = []
    for rule in rules:
        preview = preview_late_fee_application(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=LateFeePreviewRequest(as_of_date=as_of_date, late_fee_rule_ids=[rule.id]),
        )
        if preview.valid_rows == 0:
            continue
        due_rules.append(
            ScheduledLateFeeRuleDueRead(
                late_fee_rule_id=rule.id,
                late_fee_rule_name=rule.name,
                charge_type_id=rule.charge_type_id,
                grace_days=rule.grace_days,
                eligible_invoice_count=preview.valid_rows,
                total_penalty_amount=preview.total_penalty_amount,
                status="due",
                reason="one or more overdue invoices are eligible",
            )
        )
    return due_rules


def get_due_work(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
) -> ScheduledDueWorkRead:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    billing_rules = list_due_billing_rules(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        as_of_date=as_of_date,
    )
    late_fee_rules = list_due_late_fee_rules(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        as_of_date=as_of_date,
    )
    return ScheduledDueWorkRead(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        as_of_date=as_of_date,
        billing_due_count=len(billing_rules),
        late_fee_due_count=len(late_fee_rules),
        billing_rules=billing_rules,
        late_fee_rules=late_fee_rules,
    )


def list_job_runs(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[ScheduledJobRun]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(ScheduledJobRun)
            .where(
                ScheduledJobRun.tenant_id == tenant_context.tenant_id,
                ScheduledJobRun.society_id == society_id,
            )
            .order_by(ScheduledJobRun.created_at.desc())
        )
    )


def create_job_run(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    job_type: str,
    as_of_date: date,
    run_mode: str = "manual",
) -> ScheduledJobRun:
    run = ScheduledJobRun(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        job_type=job_type,
        run_mode=run_mode,
        status="running",
        as_of_date=as_of_date,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def complete_job_run(
    session: Session,
    *,
    run: ScheduledJobRun,
    summary: str,
    metadata: dict,
) -> ScheduledJobRun:
    run.status = "completed"
    run.finished_at = datetime.now(UTC)
    run.summary = summary
    run.metadata_json = metadata
    session.commit()
    session.refresh(run)
    return run


def fail_job_run(
    session: Session,
    *,
    run: ScheduledJobRun,
    error_message: str,
    metadata: dict | None = None,
) -> ScheduledJobRun:
    run.status = "failed"
    run.finished_at = datetime.now(UTC)
    run.error_message = error_message
    run.metadata_json = metadata or {}
    session.commit()
    session.refresh(run)
    return run


def run_due_billing_rules(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
    actor: User,
) -> tuple[int, int, list[uuid.UUID]]:
    due_rules = list_due_billing_rules(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        as_of_date=as_of_date,
    )
    generated_count = 0
    generated_invoice_ids: list[uuid.UUID] = []

    for due_rule in due_rules:
        rule = session.scalar(
            select(BillingRule).where(
                BillingRule.id == due_rule.billing_rule_id,
                BillingRule.tenant_id == tenant_context.tenant_id,
                BillingRule.society_id == society_id,
            )
        )
        if rule is None or rule.next_generation_date is None:
            continue
        period_start, period_end = billing_period_for(rule, rule.next_generation_date)
        response = confirm_invoice_generation(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=InvoiceGenerationRequest(
                billing_period_start=period_start,
                billing_period_end=period_end,
                invoice_date=rule.next_generation_date,
                due_date=due_date_for(rule.next_generation_date, rule.due_day),
                billing_rule_ids=[rule.id],
            ),
            actor=actor,
        )
        generated_count += response.generated_count
        generated_invoice_ids.extend(response.invoice_ids)

        rule = session.scalar(
            select(BillingRule).where(
                BillingRule.id == due_rule.billing_rule_id,
                BillingRule.tenant_id == tenant_context.tenant_id,
                BillingRule.society_id == society_id,
            )
        )
        if rule is not None:
            rule.next_generation_date = next_generation_date_for(rule)
            session.commit()

    return len(due_rules), generated_count, generated_invoice_ids


def run_due_late_fee_rules(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    as_of_date: date,
    actor: User,
) -> tuple[int, int, list[uuid.UUID]]:
    due_rules = list_due_late_fee_rules(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        as_of_date=as_of_date,
    )
    if not due_rules:
        return 0, 0, []

    response = apply_late_fees(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=LateFeePreviewRequest(
            as_of_date=as_of_date,
            late_fee_rule_ids=[rule.late_fee_rule_id for rule in due_rules],
        ),
        actor=actor,
    )
    return len(due_rules), response.generated_count, response.invoice_ids


def run_due_jobs(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ScheduledRunDueJobsRequest,
    actor: User,
    run_mode: str = "manual",
) -> ScheduledRunDueJobsResponse:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)

    billing_run: ScheduledJobRun | None = None
    late_fee_run: ScheduledJobRun | None = None
    billing_rule_count = 0
    late_fee_rule_count = 0
    generated_invoice_count = 0
    generated_penalty_invoice_count = 0

    if payload.include_billing:
        billing_run = create_job_run(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            job_type="billing_generation",
            as_of_date=payload.as_of_date,
            run_mode=run_mode,
        )
        try:
            billing_rule_count, generated_invoice_count, invoice_ids = run_due_billing_rules(
                session,
                tenant_context=tenant_context,
                society_id=society_id,
                as_of_date=payload.as_of_date,
                actor=actor,
            )
            billing_run = complete_job_run(
                session,
                run=billing_run,
                summary=f"Generated {generated_invoice_count} invoices from {billing_rule_count} billing rules.",
                metadata={"invoice_ids": [str(invoice_id) for invoice_id in invoice_ids]},
            )
        except Exception as exc:
            session.rollback()
            fail_job_run(
                session,
                run=billing_run,
                error_message=str(exc),
                metadata={"job_type": "billing_generation"},
            )
            raise ScheduledJobExecutionError(str(exc)) from exc

    if payload.include_late_fees:
        late_fee_run = create_job_run(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            job_type="late_fee_application",
            as_of_date=payload.as_of_date,
            run_mode=run_mode,
        )
        try:
            late_fee_rule_count, generated_penalty_invoice_count, invoice_ids = run_due_late_fee_rules(
                session,
                tenant_context=tenant_context,
                society_id=society_id,
                as_of_date=payload.as_of_date,
                actor=actor,
            )
            late_fee_run = complete_job_run(
                session,
                run=late_fee_run,
                summary=(
                    f"Generated {generated_penalty_invoice_count} penalty invoices "
                    f"from {late_fee_rule_count} penalty rules."
                ),
                metadata={"invoice_ids": [str(invoice_id) for invoice_id in invoice_ids]},
            )
        except Exception as exc:
            session.rollback()
            fail_job_run(
                session,
                run=late_fee_run,
                error_message=str(exc),
                metadata={"job_type": "late_fee_application"},
            )
            raise ScheduledJobExecutionError(str(exc)) from exc

    return ScheduledRunDueJobsResponse(
        billing_job_run=ScheduledJobRunRead.model_validate(billing_run) if billing_run is not None else None,
        late_fee_job_run=ScheduledJobRunRead.model_validate(late_fee_run) if late_fee_run is not None else None,
        generated_invoice_count=generated_invoice_count,
        generated_penalty_invoice_count=generated_penalty_invoice_count,
        billing_rule_count=billing_rule_count,
        late_fee_rule_count=late_fee_rule_count,
    )
