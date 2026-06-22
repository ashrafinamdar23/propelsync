from datetime import date
from decimal import Decimal
import uuid

import pytest

from app.models import ChartOfAccount, Expense, ExpenseCategory, JournalEntry, JournalLine, Society, User, Vendor
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.expenses import (
    ExpenseAlreadyExistsError,
    ExpenseCancellationInvalidError,
    ExpenseJournalPostingError,
    ExpenseReferenceInvalidError,
    ExpenseSocietyNotFoundError,
    approve_expense,
    cancel_expense,
    create_expense,
    money,
    post_expense_journal,
    update_expense,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_expense: Expense | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_expense = existing_expense
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_expense

    def scalars(self, *_: object) -> list[object]:
        return []

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


def build_actor() -> User:
    return User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@example.com",
        full_name="Society Admin",
    )


def build_context(tenant_id: uuid.UUID, actor: User) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant=None,  # type: ignore[arg-type]
        user=actor,
    )


def build_category(
    tenant_id: uuid.UUID,
    society_id: uuid.UUID,
    expense_account_id: uuid.UUID | None = None,
) -> ExpenseCategory:
    return ExpenseCategory(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        name="Housekeeping",
        code="HK",
        expense_account_id=expense_account_id or uuid.uuid4(),
        status="active",
    )


def build_vendor(tenant_id: uuid.UUID, society_id: uuid.UUID) -> Vendor:
    return Vendor(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        vendor_code="VEND-001",
        vendor_name="CleanCo",
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


def build_expense_account(tenant_id: uuid.UUID, society_id: uuid.UUID) -> ChartOfAccount:
    return ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="5010",
        account_name="Housekeeping Expense",
        account_type="expense",
        normal_balance="debit",
        status="active",
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


def build_payload(category_id: uuid.UUID, vendor_id: uuid.UUID | None = None) -> ExpenseCreate:
    return ExpenseCreate(
        vendor_id=vendor_id,
        expense_category_id=category_id,
        expense_type="vendor_bill" if vendor_id else "cash_expense",
        vendor_bill_number="BILL-001" if vendor_id else None,
        reference_number="REF-001",
        expense_date=date(2026, 6, 22),
        due_date=date(2026, 6, 30),
        description="June housekeeping",
        amount=Decimal("1000.00"),
        tax_amount=Decimal("180.00"),
    )


def test_money_quantizes_to_two_decimals() -> None:
    assert money(Decimal("10.005")) == Decimal("10.01")


def test_post_expense_journal_for_vendor_bill_debits_expense_and_credits_payable() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    expense_account = build_expense_account(tenant_id, society_id)
    payable_account = build_payable_account(tenant_id, society_id)
    society = Society(
        id=society_id,
        tenant_id=tenant_id,
        name="Green Heights",
        payable_account_id=payable_account.id,
    )
    expense = Expense(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        expense_category_id=uuid.uuid4(),
        expense_account_id=expense_account.id,
        expense_type="vendor_bill",
        vendor_bill_number="BILL-001",
        expense_date=date(2026, 6, 22),
        due_date=date(2026, 6, 30),
        description="June housekeeping",
        amount=Decimal("1000.00"),
        tax_amount=Decimal("180.00"),
        total_amount=Decimal("1180.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("1180.00"),
    )
    session = FakeSession(scalar_results=[society, expense_account, payable_account])

    journal = post_expense_journal(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        expense=expense,
    )

    journal_lines = [item for item in session.added if isinstance(item, JournalLine)]
    assert isinstance(journal, JournalEntry)
    assert journal.source_type == "expense"
    assert journal.source_id == expense.id
    assert expense.journal_entry_id == journal.id
    assert journal_lines[0].account_id == expense_account.id
    assert journal_lines[0].debit_amount == Decimal("1180.00")
    assert journal_lines[1].account_id == payable_account.id
    assert journal_lines[1].credit_amount == Decimal("1180.00")


def test_post_expense_journal_for_cash_expense_credits_payment_account() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    expense_account = build_expense_account(tenant_id, society_id)
    payment_account = build_asset_account(tenant_id, society_id)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    expense = Expense(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        expense_category_id=uuid.uuid4(),
        expense_account_id=expense_account.id,
        payment_account_id=payment_account.id,
        expense_type="cash_expense",
        expense_date=date(2026, 6, 22),
        due_date=date(2026, 6, 22),
        description="Cash purchase",
        amount=Decimal("500.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("500.00"),
        amount_paid=Decimal("500.00"),
        amount_due=Decimal("0.00"),
    )
    session = FakeSession(scalar_results=[society, expense_account, payment_account])

    post_expense_journal(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        expense=expense,
    )

    journal_lines = [item for item in session.added if isinstance(item, JournalLine)]
    assert journal_lines[1].account_id == payment_account.id
    assert journal_lines[1].credit_amount == Decimal("500.00")


def test_post_expense_journal_requires_payable_account_for_vendor_bill() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    expense_account = build_expense_account(tenant_id, society_id)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    expense = Expense(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        expense_category_id=uuid.uuid4(),
        expense_account_id=expense_account.id,
        expense_type="vendor_bill",
        expense_date=date(2026, 6, 22),
        due_date=date(2026, 6, 30),
        description="June housekeeping",
        amount=Decimal("1000.00"),
        tax_amount=Decimal("180.00"),
        total_amount=Decimal("1180.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("1180.00"),
    )
    session = FakeSession(scalar_results=[society, expense_account])

    with pytest.raises(ExpenseJournalPostingError):
        post_expense_journal(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            expense=expense,
        )


def test_create_expense_records_amounts_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    expense_account = build_expense_account(tenant_id, society_id)
    payable_account = build_payable_account(tenant_id, society_id)
    society = Society(
        id=society_id,
        tenant_id=tenant_id,
        name="Green Heights",
        payable_account_id=payable_account.id,
    )
    category = build_category(tenant_id, society_id, expense_account.id)
    vendor = build_vendor(tenant_id, society_id)
    session = FakeSession(
        scalar_results=[society, category, vendor, None, society, expense_account, payable_account]
    )
    payload = build_payload(category.id, vendor.id)

    expense = create_expense(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert expense.tenant_id == tenant_id
    assert expense.society_id == society_id
    assert expense.expense_account_id == category.expense_account_id
    assert expense.total_amount == Decimal("1180.00")
    assert expense.amount_due == Decimal("1180.00")
    assert expense.payment_status == "unpaid"
    assert expense.status == "recorded"
    assert expense.journal_entry_id is not None
    assert session.committed is True
    assert len(session.added) == 5


def test_create_expense_rejects_missing_society() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(scalar_results=[None])
    payload = build_payload(uuid.uuid4())

    with pytest.raises(ExpenseSocietyNotFoundError):
        create_expense(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_expense_rejects_missing_category() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    session = FakeSession(scalar_results=[society, None])
    payload = build_payload(uuid.uuid4())

    with pytest.raises(ExpenseReferenceInvalidError):
        create_expense(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_create_expense_rejects_duplicate_vendor_bill() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    category = build_category(tenant_id, society_id)
    vendor = build_vendor(tenant_id, society_id)
    existing_expense = Expense(
        tenant_id=tenant_id,
        society_id=society_id,
        vendor_id=vendor.id,
        expense_category_id=category.id,
        expense_account_id=category.expense_account_id,
        expense_type="vendor_bill",
        vendor_bill_number="BILL-001",
        expense_date=date(2026, 6, 22),
        due_date=date(2026, 6, 30),
        description="Existing bill",
        amount=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("100.00"),
    )
    session = FakeSession(scalar_results=[society, category, vendor, existing_expense])
    payload = build_payload(category.id, vendor.id)

    with pytest.raises(ExpenseAlreadyExistsError):
        create_expense(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_update_expense_changes_amounts_and_references() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    expense_account = build_expense_account(tenant_id, society_id)
    payable_account = build_payable_account(tenant_id, society_id)
    category = build_category(tenant_id, society_id, expense_account.id)
    expense = Expense(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        expense_category_id=uuid.uuid4(),
        expense_account_id=uuid.uuid4(),
        expense_type="cash_expense",
        expense_date=date(2026, 6, 1),
        due_date=date(2026, 6, 1),
        description="Old bill",
        amount=Decimal("500.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("500.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("500.00"),
        status="recorded",
    )
    session = FakeSession(scalar_results=[expense, category, Society(
        id=society_id,
        tenant_id=tenant_id,
        name="Green Heights",
        payable_account_id=payable_account.id,
    ), expense_account, payable_account])
    payload = ExpenseUpdate(
        vendor_id=None,
        expense_category_id=category.id,
        expense_type="other",
        expense_date=date(2026, 6, 22),
        due_date=date(2026, 6, 30),
        description="Updated bill",
        amount=Decimal("700.00"),
        tax_amount=Decimal("126.00"),
    )

    updated = update_expense(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        expense_id=expense.id,
        payload=payload,
        actor=actor,
    )

    assert updated.description == "Updated bill"
    assert updated.expense_account_id == category.expense_account_id
    assert updated.total_amount == Decimal("826.00")
    assert updated.amount_due == Decimal("826.00")
    assert updated.journal_entry_id is not None
    assert session.committed is True


def test_approve_expense_sets_status() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    expense = Expense(id=uuid.uuid4(), status="recorded", description="Bill")
    session = FakeSession(existing_expense=expense)

    approved = approve_expense(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=uuid.uuid4(),
        expense_id=expense.id,
        actor=actor,
    )

    assert approved.status == "approved"
    assert session.committed is True


def test_cancel_expense_clears_due_and_marks_cancelled() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    expense = Expense(
        id=uuid.uuid4(),
        status="recorded",
        description="Bill",
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("500.00"),
        payment_status="unpaid",
    )
    session = FakeSession(existing_expense=expense)

    cancelled = cancel_expense(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=uuid.uuid4(),
        expense_id=expense.id,
        reason="Wrong bill",
        actor=actor,
    )

    assert cancelled.status == "cancelled"
    assert cancelled.amount_due == Decimal("0.00")
    assert cancelled.payment_status == "paid"
    assert session.committed is True


def test_cancel_paid_expense_is_rejected() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    expense = Expense(id=uuid.uuid4(), amount_paid=Decimal("1.00"), description="Bill")
    session = FakeSession(existing_expense=expense)

    with pytest.raises(ExpenseCancellationInvalidError):
        cancel_expense(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            expense_id=expense.id,
            reason="Wrong bill",
            actor=actor,
        )
