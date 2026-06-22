from datetime import date
from decimal import Decimal
import uuid

import pytest

from app.models import ChartOfAccount, JournalEntry, JournalLine, Society, User
from app.schemas.account_transfer import AccountTransferCreate
from app.services.account_transfers import (
    AccountTransferAccountInvalidError,
    AccountTransferSocietyNotFoundError,
    AccountTransferValidationError,
    create_account_transfer,
    money,
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


def build_asset_account(tenant_id: uuid.UUID, society_id: uuid.UUID, name: str) -> ChartOfAccount:
    return ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code=str(uuid.uuid4())[:8],
        account_name=name,
        account_type="asset",
        normal_balance="debit",
        status="active",
    )


def build_payload(from_account_id: uuid.UUID, to_account_id: uuid.UUID) -> AccountTransferCreate:
    return AccountTransferCreate(
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        transfer_date=date(2026, 6, 22),
        amount=Decimal("2500.00"),
        transfer_mode="bank_transfer",
        reference_number="TRF-001",
        description="Cash deposit",
    )


def test_money_quantizes_to_two_decimals() -> None:
    assert money(Decimal("10.005")) == Decimal("10.01")


def test_create_account_transfer_posts_linked_journal() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    from_account = build_asset_account(tenant_id, society_id, "Cash")
    to_account = build_asset_account(tenant_id, society_id, "Bank")
    payload = build_payload(from_account.id, to_account.id)
    session = FakeSession(scalar_results=[society, [from_account, to_account]])

    transfer = create_account_transfer(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    journal_entries = [item for item in session.added if isinstance(item, JournalEntry)]
    journal_lines = [item for item in session.added if isinstance(item, JournalLine)]
    assert transfer.tenant_id == tenant_id
    assert transfer.society_id == society_id
    assert transfer.status == "posted"
    assert transfer.journal_entry_id == journal_entries[0].id
    assert journal_entries[0].source_type == "transfer"
    assert journal_entries[0].source_id == transfer.id
    assert journal_lines[0].account_id == to_account.id
    assert journal_lines[0].debit_amount == Decimal("2500.00")
    assert journal_lines[1].account_id == from_account.id
    assert journal_lines[1].credit_amount == Decimal("2500.00")
    assert session.committed is True


def test_create_account_transfer_rejects_missing_society() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    payload = build_payload(uuid.uuid4(), uuid.uuid4())
    session = FakeSession(scalar_results=[None])

    with pytest.raises(AccountTransferSocietyNotFoundError):
        create_account_transfer(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_account_transfer_rejects_invalid_accounts() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    payload = build_payload(uuid.uuid4(), uuid.uuid4())
    session = FakeSession(scalar_results=[society, []])

    with pytest.raises(AccountTransferAccountInvalidError):
        create_account_transfer(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_create_account_transfer_rejects_same_account() -> None:
    account_id = uuid.uuid4()
    payload = AccountTransferCreate.model_construct(
        from_account_id=account_id,
        to_account_id=account_id,
        transfer_date=date(2026, 6, 22),
        amount=Decimal("100.00"),
        transfer_mode="bank_transfer",
        description="Invalid transfer",
    )
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    society = Society(id=uuid.uuid4(), tenant_id=context.tenant_id, name="Green Heights")
    session = FakeSession(scalar_results=[society])

    with pytest.raises(AccountTransferValidationError):
        create_account_transfer(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society.id,
            payload=payload,
            actor=actor,
        )
