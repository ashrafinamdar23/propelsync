from datetime import date
from decimal import Decimal
import uuid

import pytest

from app.models import ChartOfAccount, JournalEntry, Society, User
from app.schemas.journal import JournalEntryCreate, JournalLineCreate, OpeningBalanceJournalCreate
from app.services.journals import (
    JournalAccountInvalidError,
    JournalReversalInvalidError,
    JournalSocietyNotFoundError,
    JournalValidationError,
    create_manual_journal_entry,
    create_opening_balance_journal_entry,
    money,
    reverse_journal_entry,
    validate_journal_lines,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(self, scalar_results: list[object | None] | None = None) -> None:
        self.scalar_results = scalar_results or []
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        return self.scalar_results.pop(0)

    def scalars(self, *_: object) -> list[object]:
        return self.scalar_results.pop(0)  # type: ignore[return-value]

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
    return User(id=uuid.uuid4(), keycloak_subject="subject-1", email="admin@example.com")


def build_context(tenant_id: uuid.UUID, actor: User) -> TenantContext:
    return TenantContext(tenant_id=tenant_id, tenant=None, user=actor)  # type: ignore[arg-type]


def build_account(tenant_id: uuid.UUID, society_id: uuid.UUID, account_type: str = "asset") -> ChartOfAccount:
    return ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code=str(uuid.uuid4())[:8],
        account_name=str(uuid.uuid4()),
        account_type=account_type,
        normal_balance="debit" if account_type in {"asset", "expense"} else "credit",
        status="active",
    )


def build_payload(debit_account_id: uuid.UUID, credit_account_id: uuid.UUID) -> JournalEntryCreate:
    return JournalEntryCreate(
        journal_date=date(2026, 6, 22),
        reference_number="JV-001",
        description="Opening adjustment",
        lines=[
            JournalLineCreate(account_id=debit_account_id, debit_amount=Decimal("100.00")),
            JournalLineCreate(account_id=credit_account_id, credit_amount=Decimal("100.00")),
        ],
    )


def test_money_quantizes_to_two_decimals() -> None:
    assert money(Decimal("10.005")) == Decimal("10.01")


def test_validate_journal_lines_rejects_unbalanced_entry() -> None:
    payload = JournalEntryCreate.model_construct(
        journal_date=date(2026, 6, 22),
        description="Bad journal",
        lines=[
            JournalLineCreate(account_id=uuid.uuid4(), debit_amount=Decimal("100.00")),
            JournalLineCreate(account_id=uuid.uuid4(), credit_amount=Decimal("90.00")),
        ],
    )

    with pytest.raises(JournalValidationError):
        validate_journal_lines(payload)


def test_create_manual_journal_entry_adds_entry_lines_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    debit_account = build_account(tenant_id, society_id, "asset")
    credit_account = build_account(tenant_id, society_id, "liability")
    payload = build_payload(debit_account.id, credit_account.id)
    session = FakeSession(scalar_results=[society, [debit_account, credit_account]])

    entry = create_manual_journal_entry(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert entry.tenant_id == tenant_id
    assert entry.society_id == society_id
    assert entry.source_type == "manual"
    assert entry.status == "posted"
    assert session.committed is True
    assert len(session.added) == 4


def test_create_manual_journal_entry_rejects_missing_society() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    payload = build_payload(uuid.uuid4(), uuid.uuid4())
    session = FakeSession(scalar_results=[None])

    with pytest.raises(JournalSocietyNotFoundError):
        create_manual_journal_entry(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_manual_journal_entry_rejects_missing_account() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    debit_account_id = uuid.uuid4()
    credit_account_id = uuid.uuid4()
    payload = build_payload(debit_account_id, credit_account_id)
    session = FakeSession(scalar_results=[society, []])

    with pytest.raises(JournalAccountInvalidError):
        create_manual_journal_entry(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_create_opening_balance_journal_entry_adds_entry_lines_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    debit_account = build_account(tenant_id, society_id, "asset")
    credit_account = build_account(tenant_id, society_id, "equity")
    payload = OpeningBalanceJournalCreate(
        opening_date=date(2026, 4, 1),
        reference_number="OB-001",
        lines=[
            JournalLineCreate(account_id=debit_account.id, debit_amount=Decimal("1000.00")),
            JournalLineCreate(account_id=credit_account.id, credit_amount=Decimal("1000.00")),
        ],
    )
    session = FakeSession(scalar_results=[society, [debit_account, credit_account]])

    entry = create_opening_balance_journal_entry(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert entry.source_type == "opening_balance"
    assert entry.journal_date == date(2026, 4, 1)
    assert entry.description == "Opening balances as of 2026-04-01"
    assert session.committed is True
    assert len(session.added) == 4


def test_reverse_journal_entry_marks_opening_balance_reversed() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    entry = JournalEntry(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        journal_date=date(2026, 4, 1),
        source_type="opening_balance",
        reference_number="OB-001",
        description="Opening balances as of 2026-04-01",
        status="posted",
    )
    session = FakeSession(scalar_results=[society, entry])

    reversed_entry = reverse_journal_entry(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        journal_entry_id=entry.id,
        reason="Wrong opening balances",
        actor=actor,
    )

    assert reversed_entry.status == "reversed"
    assert "Wrong opening balances" in (reversed_entry.notes or "")
    assert session.committed is True
    assert any(getattr(item, "action", "") == "journal_entry.reversed" for item in session.added)


def test_reverse_journal_entry_rejects_business_source_journal() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    entry = JournalEntry(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        journal_date=date(2026, 4, 1),
        source_type="invoice",
        description="Invoice INV-001",
        status="posted",
    )
    session = FakeSession(scalar_results=[society, entry])

    with pytest.raises(JournalReversalInvalidError):
        reverse_journal_entry(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            journal_entry_id=entry.id,
            reason="Wrong entry",
            actor=actor,
        )
