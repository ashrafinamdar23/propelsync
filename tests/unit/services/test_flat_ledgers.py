import uuid
from datetime import date
from decimal import Decimal

from app.models import Flat, Invoice, Payment
from app.services.flat_ledgers import build_flat_ledger


def test_build_flat_ledger_summarizes_charges_payments_and_opening_balance() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    flat = Flat(
        id=flat_id,
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=uuid.uuid4(),
        flat_number="201",
        parking_count=0,
        status="active",
    )
    old_invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        invoice_number="INV-OLD",
        invoice_date=date(2026, 3, 1),
        due_date=date(2026, 3, 15),
        billing_period_start=date(2026, 3, 1),
        billing_period_end=date(2026, 3, 31),
        total_amount=Decimal("1000.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("1000.00"),
        status="issued",
    )
    old_payment = Payment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        payment_date=date(2026, 3, 20),
        amount=Decimal("250.00"),
        unapplied_amount=Decimal("0.00"),
        payment_mode="upi",
        reference_number="PAY-OLD",
        status="received",
    )
    current_invoice = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        invoice_number="INV-APR",
        invoice_date=date(2026, 4, 1),
        due_date=date(2026, 4, 15),
        billing_period_start=date(2026, 4, 1),
        billing_period_end=date(2026, 4, 30),
        total_amount=Decimal("3000.00"),
        amount_paid=Decimal("500.00"),
        amount_due=Decimal("2500.00"),
        status="partially_paid",
    )
    current_payment = Payment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        payment_date=date(2026, 4, 10),
        amount=Decimal("500.00"),
        unapplied_amount=Decimal("0.00"),
        payment_mode="bank_transfer",
        reference_number="PAY-APR",
        status="received",
    )

    ledger = build_flat_ledger(
        tenant_id=tenant_id,
        society_id=society_id,
        flat=flat,
        date_from=date(2026, 4, 1),
        date_to=date(2026, 4, 30),
        opening_events=[
            (old_invoice.invoice_date, 0, old_invoice.invoice_number, old_invoice),
            (old_payment.payment_date, 1, old_payment.reference_number or "", old_payment),
        ],
        movement_events=[
            (current_invoice.invoice_date, 0, current_invoice.invoice_number, current_invoice),
            (current_payment.payment_date, 1, current_payment.reference_number or "", current_payment),
        ],
    )

    assert ledger.opening_balance == Decimal("750.00")
    assert ledger.total_debits == Decimal("3000.00")
    assert ledger.total_credits == Decimal("500.00")
    assert ledger.closing_balance == Decimal("3250.00")
    assert [line.source_type for line in ledger.lines] == ["invoice", "payment"]
    assert [line.running_balance for line in ledger.lines] == [Decimal("3750.00"), Decimal("3250.00")]
