from datetime import date
from decimal import Decimal
import uuid

from app.models import ChartOfAccount, Invoice, JournalEntry, JournalLine, LateFeeApplication, Payment, Society
from app.services.payments import (
    PaymentAllocationInvalidError,
    PaymentJournalPostingError,
    build_oldest_first_allocations,
    create_payment,
    money,
    post_payment_journal,
    update_invoice_after_allocation,
    update_invoice_after_payment_reversal,
)
from app.tenants.context import TenantContext
from app.schemas.payment import PaymentCreate


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
    return TenantContext(tenant_id=tenant_id, tenant=None, user=None)  # type: ignore[arg-type]


def build_invoice(
    *,
    amount_paid: Decimal = Decimal("0.00"),
    amount_due: Decimal = Decimal("500.00"),
    status: str = "issued",
) -> Invoice:
    return Invoice(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        invoice_number="INV-001",
        invoice_date=date(2026, 7, 1),
        due_date=date(2026, 7, 10),
        billing_period_start=date(2026, 7, 1),
        billing_period_end=date(2026, 7, 31),
        total_amount=Decimal("500.00"),
        amount_paid=amount_paid,
        amount_due=amount_due,
        status=status,
    )


def test_money_quantizes_to_two_decimals() -> None:
    assert money(Decimal("10.005")) == Decimal("10.01")


def test_post_payment_journal_debits_deposit_and_credits_receivable() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    deposit_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="1010",
        account_name="Bank",
        account_type="asset",
        normal_balance="debit",
        status="active",
    )
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
    society = Society(
        id=society_id,
        tenant_id=tenant_id,
        name="Dream Savera",
        receivable_account_id=receivable_account.id,
    )
    payment = Payment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=uuid.uuid4(),
        deposit_account_id=deposit_account.id,
        payment_date=date(2026, 7, 5),
        amount=Decimal("500.00"),
        unapplied_amount=Decimal("0.00"),
        payment_mode="bank_transfer",
        status="received",
    )
    session = FakeSession(
        scalar_results=[society],
        scalars_results=[[deposit_account, receivable_account]],
    )

    journal = post_payment_journal(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        payment=payment,
    )

    journal_lines = [item for item in session.added if isinstance(item, JournalLine)]
    assert isinstance(journal, JournalEntry)
    assert journal.source_type == "payment"
    assert journal.source_id == payment.id
    assert payment.journal_entry_id == journal.id
    assert journal_lines[0].account_id == deposit_account.id
    assert journal_lines[0].debit_amount == Decimal("500.00")
    assert journal_lines[1].account_id == receivable_account.id
    assert journal_lines[1].credit_amount == Decimal("500.00")


def test_post_payment_journal_splits_unapplied_amount_to_member_advance() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    deposit_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="1010",
        account_name="Bank",
        account_type="asset",
        normal_balance="debit",
        status="active",
    )
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
    advance_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="2010",
        account_name="Owner Advance Balance",
        account_type="liability",
        normal_balance="credit",
        status="active",
    )
    society = Society(
        id=society_id,
        tenant_id=tenant_id,
        name="Dream Savera",
        receivable_account_id=receivable_account.id,
        member_advance_account_id=advance_account.id,
    )
    payment = Payment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=uuid.uuid4(),
        deposit_account_id=deposit_account.id,
        payment_date=date(2026, 7, 5),
        amount=Decimal("700.00"),
        unapplied_amount=Decimal("200.00"),
        payment_mode="bank_transfer",
        status="received",
    )
    session = FakeSession(
        scalar_results=[society],
        scalars_results=[[deposit_account, receivable_account, advance_account]],
    )

    post_payment_journal(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        payment=payment,
    )

    journal_lines = [item for item in session.added if isinstance(item, JournalLine)]
    assert journal_lines[0].account_id == deposit_account.id
    assert journal_lines[0].debit_amount == Decimal("700.00")
    assert journal_lines[1].account_id == receivable_account.id
    assert journal_lines[1].credit_amount == Decimal("500.00")
    assert journal_lines[2].account_id == advance_account.id
    assert journal_lines[2].credit_amount == Decimal("200.00")


def test_post_payment_journal_requires_deposit_account() -> None:
    tenant_id = uuid.uuid4()
    payment = Payment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        payment_date=date(2026, 7, 5),
        amount=Decimal("500.00"),
        unapplied_amount=Decimal("0.00"),
        payment_mode="bank_transfer",
        status="received",
    )
    session = FakeSession()

    try:
        post_payment_journal(
            session,  # type: ignore[arg-type]
            tenant_context=build_context(tenant_id),
            society_id=payment.society_id,
            payment=payment,
        )
    except PaymentJournalPostingError:
        return

    raise AssertionError("Expected missing deposit account error.")


def test_build_oldest_first_allocations_uses_due_date_order() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    older_invoice = build_invoice()
    older_invoice.tenant_id = tenant_id
    older_invoice.society_id = society_id
    older_invoice.flat_id = uuid.uuid4()
    older_invoice.due_date = date(2026, 4, 10)
    older_invoice.amount_due = Decimal("300.00")
    newer_invoice = build_invoice()
    newer_invoice.tenant_id = tenant_id
    newer_invoice.society_id = society_id
    newer_invoice.flat_id = older_invoice.flat_id
    newer_invoice.due_date = date(2026, 5, 10)
    newer_invoice.amount_due = Decimal("500.00")
    session = FakeSession(scalars_results=[[older_invoice, newer_invoice]])

    allocations = build_oldest_first_allocations(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        flat_id=older_invoice.flat_id,
        amount=Decimal("650.00"),
        payment_date=date(2026, 6, 24),
    )

    assert [allocation.invoice_id for allocation in allocations] == [older_invoice.id, newer_invoice.id]
    assert [allocation.allocated_amount for allocation in allocations] == [
        Decimal("300.00"),
        Decimal("350.00"),
    ]


def test_build_oldest_first_allocations_skips_future_penalty_when_original_paid() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    original_invoice = build_invoice(amount_due=Decimal("3000.00"))
    original_invoice.tenant_id = tenant_id
    original_invoice.society_id = society_id
    original_invoice.flat_id = flat_id
    original_invoice.total_amount = Decimal("3000.00")
    original_invoice.due_date = date(2026, 4, 15)
    penalty_invoice = build_invoice(amount_due=Decimal("100.00"))
    penalty_invoice.tenant_id = tenant_id
    penalty_invoice.society_id = society_id
    penalty_invoice.flat_id = flat_id
    penalty_invoice.total_amount = Decimal("100.00")
    penalty_invoice.due_date = date(2026, 4, 16)
    application = LateFeeApplication(
        tenant_id=tenant_id,
        society_id=society_id,
        late_fee_rule_id=uuid.uuid4(),
        original_invoice_id=original_invoice.id,
        penalty_invoice_id=penalty_invoice.id,
        applied_as_of_date=date(2026, 4, 16),
        penalty_amount=Decimal("100.00"),
        status="active",
    )
    session = FakeSession(scalars_results=[[original_invoice, penalty_invoice], [application]])

    allocations = build_oldest_first_allocations(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        flat_id=flat_id,
        amount=Decimal("3100.00"),
        payment_date=date(2026, 4, 10),
    )

    assert [allocation.invoice_id for allocation in allocations] == [original_invoice.id]
    assert [allocation.allocated_amount for allocation in allocations] == [Decimal("3000.00")]


def test_create_payment_auto_allocates_oldest_invoices_when_none_supplied() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    deposit_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="1010",
        account_name="Bank",
        account_type="asset",
        normal_balance="debit",
        status="active",
    )
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
    society = Society(
        id=society_id,
        tenant_id=tenant_id,
        name="Dream Savera",
        receivable_account_id=receivable_account.id,
    )
    flat = type("FlatRef", (), {"id": flat_id})()
    first_invoice = build_invoice(amount_due=Decimal("300.00"))
    first_invoice.tenant_id = tenant_id
    first_invoice.society_id = society_id
    first_invoice.flat_id = flat_id
    first_invoice.due_date = date(2026, 4, 10)
    first_invoice.total_amount = Decimal("300.00")
    second_invoice = build_invoice(amount_due=Decimal("500.00"))
    second_invoice.tenant_id = tenant_id
    second_invoice.society_id = society_id
    second_invoice.flat_id = flat_id
    second_invoice.due_date = date(2026, 5, 10)
    session = FakeSession(
        scalar_results=[society, flat, deposit_account, society],
        scalars_results=[
            [first_invoice, second_invoice],
            [],
            [first_invoice, second_invoice],
            [],
            [deposit_account, receivable_account],
        ],
    )

    payment = create_payment(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        payload=PaymentCreate(
            flat_id=flat_id,
            deposit_account_id=deposit_account.id,
            payment_date=date(2026, 6, 24),
            amount=Decimal("650.00"),
            payment_mode="bank_transfer",
            allocations=[],
        ),
        actor=FakeActor(),  # type: ignore[arg-type]
    )

    assert payment.unapplied_amount == Decimal("0.00")
    assert first_invoice.status == "paid"
    assert first_invoice.amount_due == Decimal("0.00")
    assert second_invoice.status == "partially_paid"
    assert second_invoice.amount_due == Decimal("150.00")


def test_partial_payment_updates_invoice_balance() -> None:
    invoice = build_invoice()

    update_invoice_after_allocation(invoice, Decimal("200.00"))

    assert invoice.amount_paid == Decimal("200.00")
    assert invoice.amount_due == Decimal("300.00")
    assert invoice.status == "partially_paid"


def test_full_payment_marks_invoice_paid() -> None:
    invoice = build_invoice()

    update_invoice_after_allocation(invoice, Decimal("500.00"))

    assert invoice.amount_paid == Decimal("500.00")
    assert invoice.amount_due == Decimal("0.00")
    assert invoice.status == "paid"


def test_over_allocation_is_rejected() -> None:
    invoice = build_invoice()

    try:
        update_invoice_after_allocation(invoice, Decimal("501.00"))
    except PaymentAllocationInvalidError:
        return

    raise AssertionError("Expected over-allocation to be rejected.")


def test_payment_reversal_restores_partially_paid_invoice_to_issued() -> None:
    invoice = build_invoice(
        amount_paid=Decimal("200.00"),
        amount_due=Decimal("300.00"),
        status="partially_paid",
    )

    update_invoice_after_payment_reversal(invoice, Decimal("200.00"))

    assert invoice.amount_paid == Decimal("0.00")
    assert invoice.amount_due == Decimal("500.00")
    assert invoice.status == "issued"


def test_payment_reversal_restores_paid_invoice_to_partially_paid() -> None:
    invoice = build_invoice(
        amount_paid=Decimal("500.00"),
        amount_due=Decimal("0.00"),
        status="paid",
    )

    update_invoice_after_payment_reversal(invoice, Decimal("100.00"))

    assert invoice.amount_paid == Decimal("400.00")
    assert invoice.amount_due == Decimal("100.00")
    assert invoice.status == "partially_paid"


def test_over_reversal_is_rejected() -> None:
    invoice = build_invoice(
        amount_paid=Decimal("100.00"),
        amount_due=Decimal("400.00"),
        status="partially_paid",
    )

    try:
        update_invoice_after_payment_reversal(invoice, Decimal("101.00"))
    except PaymentAllocationInvalidError:
        return

    raise AssertionError("Expected over-reversal to be rejected.")
