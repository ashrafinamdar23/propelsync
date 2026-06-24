import uuid
from datetime import date
from decimal import Decimal

from app.models import Flat, Invoice, JournalEntry, LateFeeApplication, LateFeeRule
from app.schemas.late_fee import LateFeePreviewRequest
from app.services.late_fees import (
    auto_cancel_invalid_unpaid_penalties,
    build_late_fee_preview,
    calculate_penalty_amount,
    due_late_fee_application_dates,
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


class FakeActor:
    def __init__(self) -> None:
        self.id = uuid.uuid4()


def build_context(tenant_id: uuid.UUID) -> TenantContext:
    return TenantContext(tenant_id=tenant_id, tenant=None, user=None)  # type: ignore[arg-type]


def build_rule(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    calculation_method: str = "fixed",
    amount: Decimal = Decimal("100.00"),
    grace_days: int = 5,
    repeat_interval_days: int | None = None,
    max_applications_per_invoice: int | None = None,
) -> LateFeeRule:
    return LateFeeRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        charge_type_id=uuid.uuid4(),
        name="Late Fee",
        calculation_method=calculation_method,
        amount=amount,
        grace_days=grace_days,
        repeat_interval_days=repeat_interval_days,
        max_applications_per_invoice=max_applications_per_invoice,
        effective_from=date(2026, 1, 1),
        status="active",
    )


def build_invoice(*, tenant_id: uuid.UUID, society_id: uuid.UUID, due_date: date) -> Invoice:
    return Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=uuid.uuid4(),
        invoice_number="INV-001",
        invoice_date=date(2026, 4, 1),
        due_date=due_date,
        billing_period_start=date(2026, 4, 1),
        billing_period_end=date(2026, 4, 30),
        total_amount=Decimal("1000.00"),
        amount_paid=Decimal("200.00"),
        amount_due=Decimal("800.00"),
        status="partially_paid",
    )


def build_flat(*, tenant_id: uuid.UUID, society_id: uuid.UUID, flat_id: uuid.UUID) -> Flat:
    return Flat(
        id=flat_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=uuid.uuid4(),
        flat_number="101",
        status="active",
    )


def test_calculate_fixed_penalty_amount() -> None:
    rule = build_rule(tenant_id=uuid.uuid4(), society_id=uuid.uuid4())

    assert calculate_penalty_amount(rule, Decimal("800.00")) == Decimal("100.00")


def test_calculate_percent_penalty_amount() -> None:
    rule = build_rule(
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        calculation_method="percent_of_due",
        amount=Decimal("2.50"),
    )

    assert calculate_penalty_amount(rule, Decimal("800.00")) == Decimal("20.00")


def test_late_fee_preview_marks_overdue_invoice_valid() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(tenant_id=tenant_id, society_id=society_id)
    invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 10))
    flat = build_flat(tenant_id=tenant_id, society_id=society_id, flat_id=invoice.flat_id)

    preview = build_late_fee_preview(
        payload=LateFeePreviewRequest(as_of_date=date(2026, 4, 20), late_fee_rule_ids=[rule.id]),
        rules=[rule],
        invoices=[invoice],
        flats_by_id={flat.id: flat},
        applications_by_invoice_rule={},
        penalty_invoice_ids=set(),
    )

    assert preview.valid_rows == 1
    assert preview.total_penalty_amount == Decimal("100.00")
    assert preview.rows[0].status == "valid"
    assert preview.rows[0].days_overdue == 6
    assert preview.rows[0].applied_as_of_date == date(2026, 4, 16)


def test_late_fee_preview_skips_invoice_inside_grace_period() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(tenant_id=tenant_id, society_id=society_id, grace_days=10)
    invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 10))
    flat = build_flat(tenant_id=tenant_id, society_id=society_id, flat_id=invoice.flat_id)

    preview = build_late_fee_preview(
        payload=LateFeePreviewRequest(as_of_date=date(2026, 4, 20), late_fee_rule_ids=[rule.id]),
        rules=[rule],
        invoices=[invoice],
        flats_by_id={flat.id: flat},
        applications_by_invoice_rule={},
        penalty_invoice_ids=set(),
    )

    assert preview.valid_rows == 0
    assert preview.skipped_rows == 1
    assert "grace period" in preview.rows[0].errors[0]


def test_late_fee_preview_skips_when_repeat_interval_has_not_elapsed() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(tenant_id=tenant_id, society_id=society_id, repeat_interval_days=30)
    invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 10))
    flat = build_flat(tenant_id=tenant_id, society_id=society_id, flat_id=invoice.flat_id)
    application = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=rule.id,
        original_invoice_id=invoice.id,
        penalty_invoice_id=uuid.uuid4(),
        applied_as_of_date=date(2026, 4, 20),
        penalty_amount=Decimal("100.00"),
    )

    preview = build_late_fee_preview(
        payload=LateFeePreviewRequest(as_of_date=date(2026, 5, 1), late_fee_rule_ids=[rule.id]),
        rules=[rule],
        invoices=[invoice],
        flats_by_id={flat.id: flat},
        applications_by_invoice_rule={(invoice.id, rule.id): [application]},
        penalty_invoice_ids=set(),
    )

    assert preview.valid_rows == 0
    assert preview.skipped_rows == 1
    assert "No late fee application is due" in preview.rows[0].errors[-1]


def test_late_fee_preview_catches_up_missed_daily_penalties() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(
        tenant_id=tenant_id,
        society_id=society_id,
        amount=Decimal("50.00"),
        grace_days=5,
        repeat_interval_days=1,
        max_applications_per_invoice=12,
    )
    invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 15))
    flat = build_flat(tenant_id=tenant_id, society_id=society_id, flat_id=invoice.flat_id)

    preview = build_late_fee_preview(
        payload=LateFeePreviewRequest(as_of_date=date(2026, 4, 25), late_fee_rule_ids=[rule.id]),
        rules=[rule],
        invoices=[invoice],
        flats_by_id={flat.id: flat},
        applications_by_invoice_rule={},
        penalty_invoice_ids=set(),
    )

    assert preview.valid_rows == 5
    assert preview.total_penalty_amount == Decimal("250.00")
    assert [row.applied_as_of_date for row in preview.rows] == [
        date(2026, 4, 21),
        date(2026, 4, 22),
        date(2026, 4, 23),
        date(2026, 4, 24),
        date(2026, 4, 25),
    ]


def test_late_fee_preview_catches_up_only_missing_daily_penalties() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(
        tenant_id=tenant_id,
        society_id=society_id,
        amount=Decimal("50.00"),
        grace_days=5,
        repeat_interval_days=1,
        max_applications_per_invoice=12,
    )
    invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 15))
    flat = build_flat(tenant_id=tenant_id, society_id=society_id, flat_id=invoice.flat_id)
    application = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=rule.id,
        original_invoice_id=invoice.id,
        penalty_invoice_id=uuid.uuid4(),
        applied_as_of_date=date(2026, 4, 21),
        penalty_amount=Decimal("50.00"),
    )

    preview = build_late_fee_preview(
        payload=LateFeePreviewRequest(as_of_date=date(2026, 4, 25), late_fee_rule_ids=[rule.id]),
        rules=[rule],
        invoices=[invoice],
        flats_by_id={flat.id: flat},
        applications_by_invoice_rule={(invoice.id, rule.id): [application]},
        penalty_invoice_ids=set(),
    )

    assert preview.valid_rows == 4
    assert [row.applied_as_of_date for row in preview.rows] == [
        date(2026, 4, 22),
        date(2026, 4, 23),
        date(2026, 4, 24),
        date(2026, 4, 25),
    ]


def test_due_late_fee_application_dates_treats_no_repeat_as_one_time() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(tenant_id=tenant_id, society_id=society_id, grace_days=0, repeat_interval_days=None)
    invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 15))

    assert due_late_fee_application_dates(
        rule=rule,
        invoice=invoice,
        as_of_date=date(2026, 4, 25),
        existing_applications=[],
    ) == [date(2026, 4, 16)]


def test_late_fee_preview_does_not_penalize_penalty_invoices() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(tenant_id=tenant_id, society_id=society_id)
    invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 10))
    flat = build_flat(tenant_id=tenant_id, society_id=society_id, flat_id=invoice.flat_id)

    preview = build_late_fee_preview(
        payload=LateFeePreviewRequest(as_of_date=date(2026, 4, 20), late_fee_rule_ids=[rule.id]),
        rules=[rule],
        invoices=[invoice],
        flats_by_id={flat.id: flat},
        applications_by_invoice_rule={},
        penalty_invoice_ids={invoice.id},
    )

    assert preview.rows == []


def test_auto_cancel_invalid_unpaid_penalty_when_original_paid_within_grace() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(tenant_id=tenant_id, society_id=society_id, grace_days=15)
    original_invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 10))
    original_invoice.total_amount = Decimal("1000.00")
    original_invoice.amount_due = Decimal("0.00")
    original_invoice.status = "paid"
    penalty_invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 26))
    penalty_invoice.id = uuid.uuid4()
    penalty_invoice.invoice_number = "INV-PEN-001"
    penalty_invoice.total_amount = Decimal("100.00")
    penalty_invoice.amount_paid = Decimal("0.00")
    penalty_invoice.amount_due = Decimal("100.00")
    penalty_invoice.journal_entry_id = uuid.uuid4()
    journal = JournalEntry(
        id=penalty_invoice.journal_entry_id,
        tenant_id=tenant_id,
        society_id=society_id,
        journal_date=date(2026, 4, 26),
        source_type="invoice",
        reference_number=penalty_invoice.invoice_number,
        description="Penalty invoice",
        status="posted",
    )
    application = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=rule.id,
        original_invoice_id=original_invoice.id,
        penalty_invoice_id=penalty_invoice.id,
        applied_as_of_date=date(2026, 4, 26),
        penalty_amount=Decimal("100.00"),
        status="active",
    )
    session = FakeSession(
        scalar_results=[Decimal("1000.00"), journal],
        scalars_results=[[application], [original_invoice], [rule], [penalty_invoice]],
    )

    cancelled_ids = auto_cancel_invalid_unpaid_penalties(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        original_invoice_ids=[original_invoice.id],
        actor=FakeActor(),  # type: ignore[arg-type]
    )

    assert cancelled_ids == [penalty_invoice.id]
    assert penalty_invoice.status == "cancelled"
    assert penalty_invoice.amount_due == Decimal("0.00")
    assert application.status == "cancelled"
    assert journal.status == "reversed"


def test_auto_cancel_invalid_penalty_keeps_paid_penalty_invoice() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(tenant_id=tenant_id, society_id=society_id, grace_days=15)
    original_invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 10))
    penalty_invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 26))
    penalty_invoice.total_amount = Decimal("100.00")
    penalty_invoice.amount_paid = Decimal("100.00")
    penalty_invoice.amount_due = Decimal("0.00")
    penalty_invoice.status = "paid"
    application = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=rule.id,
        original_invoice_id=original_invoice.id,
        penalty_invoice_id=penalty_invoice.id,
        applied_as_of_date=date(2026, 4, 26),
        penalty_amount=Decimal("100.00"),
        status="active",
    )
    session = FakeSession(
        scalars_results=[[application], [original_invoice], [rule], [penalty_invoice]],
    )

    cancelled_ids = auto_cancel_invalid_unpaid_penalties(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        original_invoice_ids=[original_invoice.id],
        actor=FakeActor(),  # type: ignore[arg-type]
    )

    assert cancelled_ids == []
    assert penalty_invoice.status == "paid"
    assert application.status == "active"


def test_auto_cancel_invalid_penalty_after_backdated_full_payment_date() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(
        tenant_id=tenant_id,
        society_id=society_id,
        grace_days=5,
        repeat_interval_days=1,
        max_applications_per_invoice=12,
    )
    original_invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 15))
    original_invoice.total_amount = Decimal("1000.00")
    original_invoice.amount_due = Decimal("0.00")
    original_invoice.status = "paid"
    penalty_24 = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 24))
    penalty_24.id = uuid.uuid4()
    penalty_24.invoice_number = "INV-PEN-024"
    penalty_24.total_amount = Decimal("50.00")
    penalty_24.amount_paid = Decimal("0.00")
    penalty_24.amount_due = Decimal("50.00")
    penalty_25 = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 25))
    penalty_25.id = uuid.uuid4()
    penalty_25.invoice_number = "INV-PEN-025"
    penalty_25.total_amount = Decimal("50.00")
    penalty_25.amount_paid = Decimal("0.00")
    penalty_25.amount_due = Decimal("50.00")
    application_24 = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=rule.id,
        original_invoice_id=original_invoice.id,
        penalty_invoice_id=penalty_24.id,
        applied_as_of_date=date(2026, 4, 24),
        penalty_amount=Decimal("50.00"),
        status="active",
    )
    application_25 = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=rule.id,
        original_invoice_id=original_invoice.id,
        penalty_invoice_id=penalty_25.id,
        applied_as_of_date=date(2026, 4, 25),
        penalty_amount=Decimal("50.00"),
        status="active",
    )
    session = FakeSession(
        scalar_results=[
            Decimal("0.00"),  # Paid by 2026-04-23, so 24th penalty remains.
            Decimal("1000.00"),  # Paid by 2026-04-24, so 25th penalty is cancelled.
        ],
        scalars_results=[
            [application_24, application_25],
            [original_invoice],
            [rule],
            [penalty_24, penalty_25],
        ],
    )

    cancelled_ids = auto_cancel_invalid_unpaid_penalties(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        original_invoice_ids=[original_invoice.id],
        actor=FakeActor(),  # type: ignore[arg-type]
    )

    assert cancelled_ids == [penalty_25.id]
    assert penalty_24.status != "cancelled"
    assert application_24.status == "active"
    assert penalty_25.status == "cancelled"
    assert penalty_25.amount_due == Decimal("0.00")
    assert application_25.status == "cancelled"


def test_auto_cancel_invalid_penalty_after_advance_payment_before_due_date() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    rule = build_rule(
        tenant_id=tenant_id,
        society_id=society_id,
        grace_days=0,
        repeat_interval_days=1,
        max_applications_per_invoice=12,
    )
    original_invoice = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 15))
    original_invoice.total_amount = Decimal("3000.00")
    original_invoice.amount_due = Decimal("0.00")
    original_invoice.status = "paid"
    penalty_16 = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 16))
    penalty_16.id = uuid.uuid4()
    penalty_16.invoice_number = "INV-PEN-016"
    penalty_16.total_amount = Decimal("100.00")
    penalty_16.amount_paid = Decimal("0.00")
    penalty_16.amount_due = Decimal("100.00")
    penalty_24 = build_invoice(tenant_id=tenant_id, society_id=society_id, due_date=date(2026, 4, 24))
    penalty_24.id = uuid.uuid4()
    penalty_24.invoice_number = "INV-PEN-024"
    penalty_24.total_amount = Decimal("50.00")
    penalty_24.amount_paid = Decimal("0.00")
    penalty_24.amount_due = Decimal("50.00")
    application_16 = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=rule.id,
        original_invoice_id=original_invoice.id,
        penalty_invoice_id=penalty_16.id,
        applied_as_of_date=date(2026, 4, 16),
        penalty_amount=Decimal("100.00"),
        status="active",
    )
    application_24 = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=rule.id,
        original_invoice_id=original_invoice.id,
        penalty_invoice_id=penalty_24.id,
        applied_as_of_date=date(2026, 4, 24),
        penalty_amount=Decimal("50.00"),
        status="active",
    )
    session = FakeSession(
        scalar_results=[
            Decimal("3000.00"),
            Decimal("3000.00"),
        ],
        scalars_results=[
            [application_16, application_24],
            [original_invoice],
            [rule],
            [penalty_16, penalty_24],
        ],
    )

    cancelled_ids = auto_cancel_invalid_unpaid_penalties(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        original_invoice_ids=[original_invoice.id],
        actor=FakeActor(),  # type: ignore[arg-type]
    )

    assert cancelled_ids == [penalty_16.id, penalty_24.id]
    assert penalty_16.status == "cancelled"
    assert penalty_16.amount_due == Decimal("0.00")
    assert application_16.status == "cancelled"
    assert penalty_24.status == "cancelled"
    assert penalty_24.amount_due == Decimal("0.00")
    assert application_24.status == "cancelled"
