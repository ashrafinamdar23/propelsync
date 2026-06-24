import uuid
from datetime import date
from decimal import Decimal

from app.models import ChartOfAccount, JournalEntry, OtherIncomeReceipt, Society
from app.schemas.other_income import OtherIncomeReceiptCreate
from app.services.other_income import create_other_income_receipt, reverse_other_income_receipt
from app.tenants.context import TenantContext


class FakeScalarResult:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class FakeSession:
    def __init__(self, scalar_results: list[object | None] | None = None) -> None:
        self.scalar_results = scalar_results or []
        self.added: list[object] = []

    def scalar(self, *_: object) -> object | None:
        return self.scalar_results.pop(0) if self.scalar_results else None

    def scalars(self, *_: object) -> FakeScalarResult:
        return FakeScalarResult([])

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


def test_create_other_income_receipt_posts_debit_bank_credit_income() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    income_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4060",
        account_name="Bank Interest Income",
        account_type="income",
        normal_balance="credit",
        status="active",
    )
    deposit_account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="1020",
        account_name="Bank Account",
        account_type="asset",
        normal_balance="debit",
        status="active",
    )
    session = FakeSession(
        scalar_results=[
            Society(id=society_id, tenant_id=tenant_id, name="Dream Savera"),
            income_account,
            deposit_account,
        ]
    )

    receipt = create_other_income_receipt(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        payload=OtherIncomeReceiptCreate(
            receipt_date=date(2026, 6, 24),
            payer_name="Bank",
            payer_type="bank",
            income_account_id=income_account.id,
            deposit_account_id=deposit_account.id,
            amount=Decimal("125.50"),
            receipt_mode="bank_transfer",
            reference_number="INT-JUN",
            description="Bank interest",
        ),
        actor=FakeActor(),  # type: ignore[arg-type]
    )

    assert receipt.status == "received"
    assert receipt.amount == Decimal("125.50")
    journal_lines = [row for row in session.added if row.__class__.__name__ == "JournalLine"]
    assert len(journal_lines) == 2
    assert journal_lines[0].account_id == deposit_account.id
    assert journal_lines[0].debit_amount == Decimal("125.50")
    assert journal_lines[1].account_id == income_account.id
    assert journal_lines[1].credit_amount == Decimal("125.50")


def test_reverse_other_income_receipt_reverses_journal() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    journal_entry = JournalEntry(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        journal_date=date(2026, 6, 24),
        source_type="other_income",
        source_id=uuid.uuid4(),
        reference_number="INT-JUN",
        description="Bank interest",
        status="posted",
    )
    receipt = OtherIncomeReceipt(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        income_account_id=uuid.uuid4(),
        deposit_account_id=uuid.uuid4(),
        journal_entry_id=journal_entry.id,
        receipt_date=date(2026, 6, 24),
        payer_name="Bank",
        payer_type="bank",
        amount=Decimal("125.50"),
        receipt_mode="bank_transfer",
        description="Bank interest",
        status="received",
    )
    session = FakeSession(scalar_results=[receipt, journal_entry])

    reversed_receipt = reverse_other_income_receipt(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        receipt_id=receipt.id,
        reason="Wrong amount",
        actor=FakeActor(),  # type: ignore[arg-type]
    )

    assert reversed_receipt.status == "reversed"
    assert journal_entry.status == "reversed"
    assert "Wrong amount" in (reversed_receipt.notes or "")
