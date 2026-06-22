import uuid

import pytest

from app.models import ChartOfAccount, ExpenseCategory, Society, User
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryUpdate
from app.services.expense_categories import (
    ExpenseCategoryAccountInvalidError,
    ExpenseCategoryAlreadyExistsError,
    ExpenseCategorySocietyNotFoundError,
    change_expense_category_status,
    create_expense_category,
    update_expense_category,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_category: ExpenseCategory | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_category = existing_category
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_category

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


def test_create_expense_category_adds_category_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    expense_account = build_expense_account(tenant_id, society_id)
    session = FakeSession(scalar_results=[society, None, None, expense_account])
    payload = ExpenseCategoryCreate(
        name="Housekeeping",
        code="HK",
        description="Housekeeping vendor bills",
        expense_account_id=expense_account.id,
    )

    category = create_expense_category(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert category.tenant_id == tenant_id
    assert category.society_id == society_id
    assert category.name == "Housekeeping"
    assert category.expense_account_id == expense_account.id
    assert category.status == "active"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_expense_category_rejects_missing_society() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(scalar_results=[None])
    payload = ExpenseCategoryCreate(name="Housekeeping", code="HK", expense_account_id=uuid.uuid4())

    with pytest.raises(ExpenseCategorySocietyNotFoundError):
        create_expense_category(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_expense_category_rejects_duplicate_name() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    existing_category = ExpenseCategory(
        tenant_id=tenant_id,
        society_id=society_id,
        name="Housekeeping",
        expense_account_id=uuid.uuid4(),
    )
    session = FakeSession(scalar_results=[society, existing_category])
    payload = ExpenseCategoryCreate(name="Housekeeping", code="HK", expense_account_id=uuid.uuid4())

    with pytest.raises(ExpenseCategoryAlreadyExistsError):
        create_expense_category(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_create_expense_category_rejects_non_expense_account() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    session = FakeSession(scalar_results=[society, None, None, None])
    payload = ExpenseCategoryCreate(name="Housekeeping", code="HK", expense_account_id=uuid.uuid4())

    with pytest.raises(ExpenseCategoryAccountInvalidError):
        create_expense_category(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_update_expense_category_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    expense_account = build_expense_account(tenant_id, society_id)
    category = ExpenseCategory(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        name="Housekeeping",
        code="HK",
        expense_account_id=expense_account.id,
        status="active",
    )
    session = FakeSession(scalar_results=[category, None, None, expense_account])
    payload = ExpenseCategoryUpdate(
        name="Facility Housekeeping",
        code="FHK",
        description="Recurring housekeeping bills",
        expense_account_id=expense_account.id,
    )

    updated = update_expense_category(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        category_id=category.id,
        payload=payload,
        actor=actor,
    )

    assert updated.name == "Facility Housekeeping"
    assert updated.code == "FHK"
    assert updated.description == "Recurring housekeeping bills"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_expense_category_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    category = ExpenseCategory(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        name="Housekeeping",
        expense_account_id=uuid.uuid4(),
        status="active",
    )
    session = FakeSession(existing_category=category)

    updated = change_expense_category_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        category_id=category.id,
        status="inactive",
        actor=actor,
    )

    assert updated.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1
