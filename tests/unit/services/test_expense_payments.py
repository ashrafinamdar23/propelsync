from datetime import date
from decimal import Decimal
import uuid

import pytest

from app.models import ChartOfAccount, Expense, ExpensePayment, ExpensePaymentAllocation, JournalEntry, JournalLine, Society, User
from app.services.expense_payments import (
    ExpensePaymentAllocationInvalidError,
    ExpensePaymentJournalPostingError,
    allocate_existing_expense_payment,
    money,
    post_expense_payment_journal,
    update_expense_after_payment,
)
from app.schemas.expense_payment import ExpensePaymentAllocateRequest, ExpensePaymentAllocationCreate
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        scalar_results: list[object | None] | None = None,
        scalars_results: list[list[object]] | None = None,
    ) -> None:
        self.scalar_results = scalar_results or []
        self.scalars_results = scalars_results or []
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        return self.scalar_results.pop(0) if self.scalar_results else None

    def scalars(self, *_: object) -> list[object]:
        return self.scalars_results.pop(0) if self.scalars_results else []

    def add(self, instance: object) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        for instance in self.added:
            if getattr(instance, "id", None) is None:
                instance.id = uuid.uuid4()

    def commit(self) -> None:
        self.committed = True

    def refresh(self, _: object) -> None:
        return None


def build_context(tenant_id: uuid.UUID) -> TenantContext:
    return TenantContext(tenant_id=tenant_id, tenant=None, user=None)  # type: ignore[arg-type]


def build_actor() -> User:
    return User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@example.com",
        full_name="Society Admin",
    )


def build_payable_account(tenant_id: uuid.UUID, society_id: uuid.UUID) -> ChartOfAccount:
    return ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="2010",
        account_name="Accounts Payable",
        account_type="liability",
        normal_balance="credit",
        status="active",
    )


def build_asset_account(tenant_id: uuid.UUID, society_id: uuid.UUID) -> ChartOfAccount:
    return ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="1010",
        account_name="Bank Account",
        account_type="asset",
        normal_balance="debit",
        status="active",
    )


def build_expense(*, amount_paid: Decimal = Decimal("0.00"), amount_due: Decimal = Decimal("500.00")) -> Expense:
    return Expense(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        expense_category_id=uuid.uuid4(),
        expense_account_id=uuid.uuid4(),
        expense_date=date(2026, 6, 22),
        due_date=date(2026, 6, 30),
        description="Housekeeping bill",
        amount=Decimal("500.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("500.00"),
        amount_paid=amount_paid,
        amount_due=amount_due,
        payment_status="unpaid" if amount_paid == Decimal("0.00") else "partially_paid",
    )


def test_money_quantizes_to_two_decimals() -> None:
    assert money(Decimal("10.005")) == Decimal("10.01")


def test_post_expense_payment_journal_debits_payable_and_credits_bank() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    payable_account = build_payable_account(tenant_id, society_id)
    payment_account = build_asset_account(tenant_id, society_id)
    society = Society(
        id=society_id,
        tenant_id=tenant_id,
        name="Green Heights",
        payable_account_id=payable_account.id,
    )
    payment = ExpensePayment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        payment_account_id=payment_account.id,
        payment_date=date(2026, 6, 25),
        amount=Decimal("500.00"),
        unapplied_amount=Decimal("0.00"),
        payment_mode="bank_transfer",
        status="paid",
    )
    session = FakeSession(
        scalar_results=[society],
        scalars_results=[[payable_account, payment_account]],
    )

    journal = post_expense_payment_journal(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        payment=payment,
    )

    journal_lines = [item for item in session.added if isinstance(item, JournalLine)]
    assert isinstance(journal, JournalEntry)
    assert journal.source_type == "expense_payment"
    assert journal.source_id == payment.id
    assert payment.journal_entry_id == journal.id
    assert journal_lines[0].account_id == payable_account.id
    assert journal_lines[0].debit_amount == Decimal("500.00")
    assert journal_lines[1].account_id == payment_account.id
    assert journal_lines[1].credit_amount == Decimal("500.00")


def test_post_expense_payment_journal_requires_payable_account() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    payment_account = build_asset_account(tenant_id, society_id)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    payment = ExpensePayment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        payment_account_id=payment_account.id,
        payment_date=date(2026, 6, 25),
        amount=Decimal("500.00"),
        unapplied_amount=Decimal("0.00"),
        payment_mode="bank_transfer",
        status="paid",
    )
    session = FakeSession(scalar_results=[society])

    with pytest.raises(ExpensePaymentJournalPostingError):
        post_expense_payment_journal(
            session,  # type: ignore[arg-type]
            tenant_context=build_context(tenant_id),
            society_id=society_id,
            payment=payment,
        )


def test_partial_expense_payment_updates_balance() -> None:
    expense = build_expense()

    update_expense_after_payment(expense, Decimal("200.00"))

    assert expense.amount_paid == Decimal("200.00")
    assert expense.amount_due == Decimal("300.00")
    assert expense.payment_status == "partially_paid"


def test_full_expense_payment_marks_paid() -> None:
    expense = build_expense()

    update_expense_after_payment(expense, Decimal("500.00"))

    assert expense.amount_paid == Decimal("500.00")
    assert expense.amount_due == Decimal("0.00")
    assert expense.payment_status == "paid"


def test_over_allocation_is_rejected() -> None:
    expense = build_expense()

    with pytest.raises(ExpensePaymentAllocationInvalidError):
        update_expense_after_payment(expense, Decimal("501.00"))


def test_allocate_existing_expense_payment_consumes_unapplied_amount() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    vendor_id = uuid.uuid4()
    payment = ExpensePayment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        vendor_id=vendor_id,
        payment_account_id=uuid.uuid4(),
        payment_date=date(2026, 3, 31),
        amount=Decimal("14.16"),
        unapplied_amount=Decimal("14.16"),
        payment_mode="bank_transfer",
        status="paid",
    )
    expense = build_expense(amount_due=Decimal("14.16"))
    expense.tenant_id = tenant_id
    expense.society_id = society_id
    expense.vendor_id = vendor_id
    expense.total_amount = Decimal("14.16")
    expense.amount = Decimal("14.16")
    payload = ExpensePaymentAllocateRequest(
        allocations=[
            ExpensePaymentAllocationCreate(expense_id=expense.id, allocated_amount=Decimal("14.16"))
        ]
    )
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    session = FakeSession(scalar_results=[society, payment], scalars_results=[[expense]])

    updated = allocate_existing_expense_payment(
        session,  # type: ignore[arg-type]
        tenant_context=build_context(tenant_id),
        society_id=society_id,
        expense_payment_id=payment.id,
        payload=payload,
        actor=build_actor(),
    )

    allocations = [item for item in session.added if isinstance(item, ExpensePaymentAllocation)]
    assert updated.unapplied_amount == Decimal("0.00")
    assert expense.payment_status == "paid"
    assert expense.amount_due == Decimal("0.00")
    assert len(allocations) == 1
    assert allocations[0].expense_id == expense.id
    assert allocations[0].allocated_amount == Decimal("14.16")
    assert session.committed is True
