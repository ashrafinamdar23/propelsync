import uuid
from datetime import date
from decimal import Decimal

from app.models import BillingRule, Flat, Invoice, LateFeeRule, ScheduledJobRun, Society
from app.services.scheduled_jobs import (
    billing_period_for,
    complete_job_run,
    due_date_for,
    get_due_work,
    list_due_billing_rules,
    next_generation_date_for,
)
from app.tenants.context import TenantContext


class FakeScalarResult:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class FakeSession:
    def __init__(
        self,
        scalar_results: list[object | None] | None = None,
        scalars_results: list[list[object]] | None = None,
    ) -> None:
        self.scalar_results = scalar_results or []
        self.scalars_results = scalars_results or []
        self.added: list[object] = []

    def scalar(self, *_: object) -> object | None:
        return self.scalar_results.pop(0) if self.scalar_results else None

    def scalars(self, *_: object) -> FakeScalarResult:
        return FakeScalarResult(self.scalars_results.pop(0) if self.scalars_results else [])

    def add(self, instance: object) -> None:
        self.added.append(instance)

    def commit(self) -> None:
        return None

    def refresh(self, *_: object) -> None:
        return None


def build_context(tenant_id: uuid.UUID) -> TenantContext:
    return TenantContext(tenant_id=tenant_id, tenant=None, user=None)  # type: ignore[arg-type]


def build_billing_rule(*, tenant_id: uuid.UUID, society_id: uuid.UUID) -> BillingRule:
    return BillingRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        charge_type_id=uuid.uuid4(),
        name="Monthly Maintenance",
        calculation_method="fixed",
        amount=Decimal("3000.00"),
        frequency="monthly",
        generation_day=1,
        due_day=10,
        billing_period_timing="current_period",
        next_generation_date=date(2026, 6, 1),
        scope_type="all_flats",
        effective_from=date(2026, 1, 1),
        status="active",
    )


def build_late_fee_rule(*, tenant_id: uuid.UUID, society_id: uuid.UUID) -> LateFeeRule:
    return LateFeeRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        charge_type_id=uuid.uuid4(),
        name="Late Fee",
        calculation_method="fixed",
        amount=Decimal("100.00"),
        grace_days=5,
        effective_from=date(2026, 1, 1),
        status="active",
    )


def test_list_due_billing_rules_uses_next_generation_date() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_billing_rule(tenant_id=tenant_id, society_id=society_id)
    session = FakeSession(scalars_results=[[rule]])

    due_rules = list_due_billing_rules(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        as_of_date=date(2026, 6, 22),
    )

    assert len(due_rules) == 1
    assert due_rules[0].billing_rule_id == rule.id
    assert due_rules[0].status == "due"


def test_get_due_work_includes_late_fee_eligible_count() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    billing_rule = build_billing_rule(tenant_id=tenant_id, society_id=society_id)
    late_fee_rule = build_late_fee_rule(tenant_id=tenant_id, society_id=society_id)
    flat = Flat(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=uuid.uuid4(),
        flat_number="101",
        status="active",
    )
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat.id,
        invoice_number="INV-001",
        invoice_date=date(2026, 6, 1),
        due_date=date(2026, 6, 10),
        billing_period_start=date(2026, 6, 1),
        billing_period_end=date(2026, 6, 30),
        total_amount=Decimal("3000.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("3000.00"),
        status="issued",
    )
    session = FakeSession(
        scalar_results=[society, society],
        scalars_results=[
            [billing_rule],
            [late_fee_rule],
            [late_fee_rule],
            [invoice],
            [flat],
            [],
        ],
    )

    due_work = get_due_work(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        as_of_date=date(2026, 6, 22),
    )

    assert due_work.billing_due_count == 1
    assert due_work.late_fee_due_count == 1
    assert due_work.late_fee_rules[0].eligible_invoice_count == 1
    assert due_work.late_fee_rules[0].total_penalty_amount == Decimal("100.00")


def test_billing_period_for_current_monthly_rule() -> None:
    rule = build_billing_rule(tenant_id=uuid.uuid4(), society_id=uuid.uuid4())

    assert billing_period_for(rule, date(2026, 6, 1)) == (
        date(2026, 6, 1),
        date(2026, 6, 30),
    )


def test_billing_period_for_next_quarter_rule() -> None:
    rule = build_billing_rule(tenant_id=uuid.uuid4(), society_id=uuid.uuid4())
    rule.frequency = "quarterly"
    rule.billing_period_timing = "next_period"

    assert billing_period_for(rule, date(2026, 6, 1)) == (
        date(2026, 9, 1),
        date(2026, 11, 30),
    )


def test_due_date_moves_to_next_month_when_due_day_before_invoice_date() -> None:
    assert due_date_for(date(2026, 6, 25), 10) == date(2026, 7, 10)


def test_next_generation_date_for_monthly_rule_advances_one_month() -> None:
    rule = build_billing_rule(tenant_id=uuid.uuid4(), society_id=uuid.uuid4())
    rule.next_generation_date = date(2026, 1, 31)

    assert next_generation_date_for(rule) == date(2026, 2, 28)


def test_complete_job_run_marks_run_completed() -> None:
    run = ScheduledJobRun(
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        job_type="billing_generation",
        run_mode="manual",
        status="running",
        as_of_date=date(2026, 6, 22),
    )
    session = FakeSession()

    completed = complete_job_run(
        session,  # type: ignore[arg-type]
        run=run,
        summary="Done",
        metadata={"invoice_ids": []},
    )

    assert completed.status == "completed"
    assert completed.summary == "Done"
    assert completed.metadata_json == {"invoice_ids": []}
    assert completed.finished_at is not None


def test_create_job_run_can_mark_scheduled_mode() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    session = FakeSession()

    from app.services.scheduled_jobs import create_job_run

    run = create_job_run(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        job_type="billing_generation",
        as_of_date=date(2026, 6, 22),
        run_mode="scheduled",
    )

    assert run.run_mode == "scheduled"
    assert run.status == "running"
    assert run in session.added
