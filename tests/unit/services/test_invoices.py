import uuid
from datetime import date
from decimal import Decimal

from app.models import (
    BillingRule,
    ChartOfAccount,
    ChargeType,
    Flat,
    Invoice,
    InvoiceLineItem,
    JournalEntry,
    JournalLine,
    Society,
)
from app.schemas.invoice_generation import InvoiceGenerationRequest
from app.services.invoices import (
    InvoiceCancellationInvalidError,
    InvoiceJournalPostingError,
    InvoiceSocietyNotFoundError,
    ManualInvoiceReferenceInvalidError,
    build_invoice_generation_preview,
    cancel_invoice,
    ensure_society_exists,
    ensure_manual_invoice_references,
    list_invoice_line_items,
    list_invoices,
    post_invoice_journal,
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
        self.scalars_calls: list[object] = []

    def scalar(self, *_: object) -> object | None:
        return self.scalar_results.pop(0) if self.scalar_results else None

    def scalars(self, *args: object) -> FakeScalarResult:
        self.scalars_calls.append(args[0])
        return FakeScalarResult(self.scalars_results.pop(0) if self.scalars_results else [])

    def add(self, instance: object) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        for instance in self.added:
            if getattr(instance, "id", None) is None:
                instance.id = uuid.uuid4()

    def commit(self) -> None:
        return None

    def refresh(self, *_: object) -> None:
        return None


class FakeActor:
    def __init__(self) -> None:
        self.id = uuid.uuid4()


def build_context(tenant_id: uuid.UUID) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant=None,  # type: ignore[arg-type]
        user=None,  # type: ignore[arg-type]
    )


def build_generation_payload() -> InvoiceGenerationRequest:
    return InvoiceGenerationRequest(
        billing_period_start=date(2026, 4, 1),
        billing_period_end=date(2026, 4, 30),
        invoice_date=date(2026, 4, 1),
        due_date=date(2026, 4, 10),
        billing_rule_ids=[uuid.uuid4()],
    )


def build_flat(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    carpet_area_sqft: Decimal | None = Decimal("500.00"),
) -> Flat:
    return Flat(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=uuid.uuid4(),
        flat_number="101",
        carpet_area_sqft=carpet_area_sqft,
        built_up_area_sqft=Decimal("600.00") if carpet_area_sqft is not None else None,
        parking_count=1,
        status="active",
    )


def build_billing_rule(
    *,
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    calculation_method: str = "fixed",
    amount: Decimal = Decimal("2500.00"),
) -> BillingRule:
    return BillingRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        charge_type_id=uuid.uuid4(),
        name="Maintenance",
        calculation_method=calculation_method,
        amount=amount,
        area_basis="carpet_area" if calculation_method == "area_based" else None,
        frequency="monthly",
        generation_day=1,
        due_day=10,
        billing_period_timing="current_period",
        scope_type="all_flats",
        effective_from=date(2026, 4, 1),
        status="active",
    )


def test_ensure_society_exists_rejects_missing_society() -> None:
    context = build_context(uuid.uuid4())
    session = FakeSession(scalar_results=[None])

    try:
        ensure_society_exists(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
        )
    except InvoiceSocietyNotFoundError:
        return

    raise AssertionError("Expected missing society error.")


def test_list_invoices_returns_tenant_scoped_rows() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    invoice = Invoice(
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=uuid.uuid4(),
        invoice_number="INV-001",
        invoice_date=date(2026, 7, 1),
        due_date=date(2026, 7, 10),
        billing_period_start=date(2026, 7, 1),
        billing_period_end=date(2026, 7, 31),
        total_amount=Decimal("2500.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("2500.00"),
        status="issued",
    )
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    session = FakeSession(scalar_results=[society], scalars_results=[[invoice]])

    rows = list_invoices(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
    )

    assert rows == [invoice]


def test_list_invoices_applies_optional_filters() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    session = FakeSession(scalar_results=[society], scalars_results=[[]])

    list_invoices(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        flat_id=flat_id,
        status="issued",
        invoice_date_from=date(2026, 4, 1),
        invoice_date_to=date(2026, 4, 30),
    )

    params = session.scalars_calls[0].compile().params
    assert flat_id in params.values()
    assert "issued" in params.values()
    assert date(2026, 4, 1) in params.values()
    assert date(2026, 4, 30) in params.values()


def test_list_invoice_line_items_returns_ordered_rows() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    line = InvoiceLineItem(
        tenant_id=tenant_id,
        society_id=society_id,
        invoice_id=invoice_id,
        charge_type_id=uuid.uuid4(),
        line_number=1,
        description="Maintenance",
        quantity=Decimal("1.00"),
        unit_amount=Decimal("2500.00"),
        line_amount=Decimal("2500.00"),
    )
    session = FakeSession(scalars_results=[[line]])

    rows = list_invoice_line_items(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        invoice_id=invoice_id,
    )

    assert rows == [line]


def test_post_invoice_journal_debits_receivable_and_credits_revenue() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    receivable_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="1100",
        account_name="Maintenance Receivable",
        account_type="asset",
        normal_balance="debit",
        status="active",
    )
    revenue_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4010",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
        status="active",
    )
    charge_type = ChargeType(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        name="Maintenance",
        revenue_account_id=revenue_account.id,
        status="active",
    )
    society = Society(
        id=society_id,
        tenant_id=tenant_id,
        name="Dream Savera",
        receivable_account_id=receivable_account.id,
    )
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=uuid.uuid4(),
        invoice_number="INV-001",
        invoice_date=date(2026, 7, 1),
        due_date=date(2026, 7, 10),
        billing_period_start=date(2026, 7, 1),
        billing_period_end=date(2026, 7, 31),
        total_amount=Decimal("2500.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("2500.00"),
        status="issued",
    )
    line = InvoiceLineItem(
        tenant_id=tenant_id,
        society_id=society_id,
        invoice_id=invoice.id,
        charge_type_id=charge_type.id,
        line_number=1,
        description="Maintenance",
        quantity=Decimal("1.00"),
        unit_amount=Decimal("2500.00"),
        line_amount=Decimal("2500.00"),
    )
    session = FakeSession(
        scalar_results=[society, receivable_account],
        scalars_results=[[charge_type], [revenue_account]],
    )

    journal = post_invoice_journal(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        invoice=invoice,
        line_items=[line],
    )

    journal_lines = [item for item in session.added if isinstance(item, JournalLine)]
    assert isinstance(journal, JournalEntry)
    assert journal.source_type == "invoice"
    assert journal.source_id == invoice.id
    assert invoice.journal_entry_id == journal.id
    assert journal_lines[0].account_id == receivable_account.id
    assert journal_lines[0].debit_amount == Decimal("2500.00")
    assert journal_lines[1].account_id == revenue_account.id
    assert journal_lines[1].credit_amount == Decimal("2500.00")


def test_post_invoice_journal_requires_receivable_account() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=uuid.uuid4(),
        invoice_number="INV-001",
        invoice_date=date(2026, 7, 1),
        due_date=date(2026, 7, 10),
        billing_period_start=date(2026, 7, 1),
        billing_period_end=date(2026, 7, 31),
        total_amount=Decimal("2500.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("2500.00"),
        status="issued",
    )
    session = FakeSession(scalar_results=[society])

    try:
        post_invoice_journal(
            session,  # type: ignore[arg-type]
            tenant_context=build_context(tenant_id),
            society_id=society_id,
            invoice=invoice,
            line_items=[],
        )
    except InvoiceJournalPostingError:
        return

    raise AssertionError("Expected missing receivable account error.")


def test_invoice_generation_preview_creates_fixed_charge_row() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    flat = build_flat(tenant_id=tenant_id, society_id=society_id)
    rule = build_billing_rule(tenant_id=tenant_id, society_id=society_id)

    preview = build_invoice_generation_preview(
        payload=build_generation_payload(),
        flats=[flat],
        rules=[rule],
        existing_rule_lines=[],
        ownerships=[],
    )

    assert preview.valid_rows == 1
    assert preview.invoice_count == 1
    assert preview.invalid_rows == 0
    assert preview.total_amount == Decimal("2500.00")
    assert preview.rows[0].lines[0].line_amount == Decimal("2500.00")


def test_invoice_generation_preview_blocks_existing_period_invoice() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    payload = build_generation_payload()
    flat = build_flat(tenant_id=tenant_id, society_id=society_id)
    rule = build_billing_rule(tenant_id=tenant_id, society_id=society_id)
    invoice = Invoice(
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat.id,
        invoice_number="INV-202604-00001",
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        total_amount=Decimal("2500.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("2500.00"),
        status="issued",
    )

    preview = build_invoice_generation_preview(
        payload=payload,
        flats=[flat],
        rules=[rule],
        existing_rule_lines=[(flat.id, rule.id)],
        ownerships=[],
    )

    assert preview.valid_rows == 0
    assert preview.invalid_rows == 1
    assert "billing rule already invoiced" in preview.rows[0].errors[0]


def test_invoice_generation_preview_marks_missing_area_invalid() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    flat = build_flat(tenant_id=tenant_id, society_id=society_id, carpet_area_sqft=None)
    rule = build_billing_rule(
        tenant_id=tenant_id,
        society_id=society_id,
        calculation_method="area_based",
        amount=Decimal("5.00"),
    )

    preview = build_invoice_generation_preview(
        payload=build_generation_payload(),
        flats=[flat],
        rules=[rule],
        existing_rule_lines=[],
        ownerships=[],
    )

    assert preview.valid_rows == 0
    assert preview.invalid_rows == 1
    assert "Flat area is missing" in preview.rows[0].errors[0]


def test_manual_invoice_reference_validation_rejects_missing_flat() -> None:
    from app.schemas.invoice import ManualInvoiceCreate, ManualInvoiceLineCreate

    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    session = FakeSession(scalar_results=[society, None])
    payload = ManualInvoiceCreate(
        flat_id=uuid.uuid4(),
        invoice_date=date(2026, 7, 1),
        due_date=date(2026, 7, 10),
        billing_period_start=date(2026, 7, 1),
        billing_period_end=date(2026, 7, 31),
        line_items=[
            ManualInvoiceLineCreate(
                charge_type_id=uuid.uuid4(),
                description="Clubhouse booking",
                quantity=Decimal("1.00"),
                unit_amount=Decimal("500.00"),
            )
        ],
    )

    try:
        ensure_manual_invoice_references(
            session,  # type: ignore[arg-type]
            tenant_context=build_context(tenant_id),
            society_id=society_id,
            payload=payload,
        )
    except ManualInvoiceReferenceInvalidError:
        return

    raise AssertionError("Expected missing flat validation error.")


def test_cancel_invoice_marks_invoice_cancelled_and_zeroes_due() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=uuid.uuid4(),
        invoice_number="INV-001",
        invoice_date=date(2026, 7, 1),
        due_date=date(2026, 7, 10),
        billing_period_start=date(2026, 7, 1),
        billing_period_end=date(2026, 7, 31),
        total_amount=Decimal("500.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("500.00"),
        status="issued",
    )
    actor = FakeActor()
    session = FakeSession(scalar_results=[invoice])

    cancelled = cancel_invoice(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        invoice_id=invoice.id,
        reason="Wrong flat",
        actor=actor,  # type: ignore[arg-type]
    )

    assert cancelled.status == "cancelled"
    assert cancelled.amount_due == Decimal("0.00")
    assert "Wrong flat" in (cancelled.notes or "")


def test_cancel_invoice_rejects_paid_invoice() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=uuid.uuid4(),
        invoice_number="INV-001",
        invoice_date=date(2026, 7, 1),
        due_date=date(2026, 7, 10),
        billing_period_start=date(2026, 7, 1),
        billing_period_end=date(2026, 7, 31),
        total_amount=Decimal("500.00"),
        amount_paid=Decimal("100.00"),
        amount_due=Decimal("400.00"),
        status="partially_paid",
    )
    actor = FakeActor()
    session = FakeSession(scalar_results=[invoice])

    try:
        cancel_invoice(
            session,  # type: ignore[arg-type]
            tenant_context=build_context(tenant_id),
            society_id=society_id,
            invoice_id=invoice.id,
            reason="Wrong flat",
            actor=actor,  # type: ignore[arg-type]
        )
    except InvoiceCancellationInvalidError:
        return

    raise AssertionError("Expected paid invoice cancellation error.")
