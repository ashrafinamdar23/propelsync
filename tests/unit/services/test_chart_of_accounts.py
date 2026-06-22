import uuid

import pytest

from app.models import ChartOfAccount, Society, User
from app.schemas.chart_of_account import ChartOfAccountCreate, ChartOfAccountUpdate
from app.services.chart_of_accounts import (
    ChartOfAccountAlreadyExistsError,
    ChartOfAccountParentInvalidError,
    change_chart_of_account_status,
    create_chart_of_account,
    preview_chart_of_account_import_rows,
    update_chart_of_account,
)
from app.schemas.chart_of_account_import import ChartOfAccountImportInput
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_account: ChartOfAccount | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_account = existing_account
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_account

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


def test_create_chart_account_adds_account_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    session = FakeSession(scalar_results=[society, None, None])
    payload = ChartOfAccountCreate(
        account_code="4000",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
    )

    account = create_chart_of_account(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert account.tenant_id == tenant_id
    assert account.society_id == society_id
    assert account.account_code == "4000"
    assert account.account_type == "income"
    assert account.normal_balance == "credit"
    assert session.committed is True
    assert len(session.added) == 2


def test_chart_account_payload_accepts_blank_parent_id_as_none() -> None:
    payload = ChartOfAccountCreate(
        parent_account_id="",  # type: ignore[arg-type]
        account_code="4000",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
    )

    assert payload.parent_account_id is None


def test_create_chart_account_rejects_duplicate_code() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    existing = ChartOfAccount(
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4000",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
    )
    session = FakeSession(scalar_results=[society, existing])
    payload = ChartOfAccountCreate(
        account_code="4000",
        account_name="Parking Income",
        account_type="income",
        normal_balance="credit",
    )

    with pytest.raises(ChartOfAccountAlreadyExistsError):
        create_chart_of_account(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_create_chart_account_sets_valid_parent() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    parent = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4000",
        account_name="Income",
        account_type="income",
        normal_balance="credit",
    )
    session = FakeSession(scalar_results=[society, None, None, parent])
    payload = ChartOfAccountCreate(
        parent_account_id=parent.id,
        account_code="4010",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
    )

    account = create_chart_of_account(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert account.parent_account_id == parent.id


def test_create_chart_account_rejects_parent_type_mismatch() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Dream Savera")
    parent = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="1000",
        account_name="Assets",
        account_type="asset",
        normal_balance="debit",
    )
    session = FakeSession(scalar_results=[society, None, None, parent])
    payload = ChartOfAccountCreate(
        parent_account_id=parent.id,
        account_code="4010",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
    )

    with pytest.raises(ChartOfAccountParentInvalidError):
        create_chart_of_account(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_update_chart_account_changes_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4000",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
        status="active",
    )
    session = FakeSession(scalar_results=[account, None, None])
    payload = ChartOfAccountUpdate(
        account_code="4010",
        account_name="Maintenance Charges Income",
        account_type="income",
        normal_balance="credit",
        description="Monthly maintenance income",
    )

    updated = update_chart_of_account(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        account_id=account.id,
        payload=payload,
        actor=actor,
    )

    assert updated.account_code == "4010"
    assert updated.account_name == "Maintenance Charges Income"
    assert updated.description == "Monthly maintenance income"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_chart_account_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    account = ChartOfAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4000",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
        status="active",
    )
    session = FakeSession(existing_account=account)

    updated = change_chart_of_account_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        account_id=account.id,
        status="inactive",
        actor=actor,
    )

    assert updated.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1


def test_preview_chart_account_import_accepts_valid_rows() -> None:
    preview = preview_chart_of_account_import_rows(
        rows=[
            ChartOfAccountImportInput(
                account_code="4000",
                account_name="Maintenance Income",
                account_type="income",
                normal_balance="credit",
            )
        ],
        existing_accounts=[],
    )

    assert preview.total_rows == 1
    assert preview.valid_rows == 1
    assert preview.invalid_rows == 0


def test_preview_chart_account_import_accepts_parent_from_earlier_row() -> None:
    preview = preview_chart_of_account_import_rows(
        rows=[
            ChartOfAccountImportInput(
                account_code="4000",
                account_name="Income",
                account_type="income",
                normal_balance="credit",
            ),
            ChartOfAccountImportInput(
                account_code="4010",
                parent_account_code="4000",
                account_name="Maintenance Income",
                account_type="income",
                normal_balance="credit",
            ),
        ],
        existing_accounts=[],
    )

    assert preview.valid_rows == 2
    assert preview.invalid_rows == 0


def test_preview_chart_account_import_rejects_parent_from_later_row() -> None:
    preview = preview_chart_of_account_import_rows(
        rows=[
            ChartOfAccountImportInput(
                account_code="4010",
                parent_account_code="4000",
                account_name="Maintenance Income",
                account_type="income",
                normal_balance="credit",
            ),
            ChartOfAccountImportInput(
                account_code="4000",
                account_name="Income",
                account_type="income",
                normal_balance="credit",
            ),
        ],
        existing_accounts=[],
    )

    assert preview.invalid_rows == 1
    assert "Parent account code must already exist or appear earlier in this file." in preview.rows[0].errors


def test_preview_chart_account_import_rejects_parent_type_mismatch() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    parent = ChartOfAccount(
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="1000",
        account_name="Assets",
        account_type="asset",
        normal_balance="debit",
    )
    preview = preview_chart_of_account_import_rows(
        rows=[
            ChartOfAccountImportInput(
                account_code="4010",
                parent_account_code="1000",
                account_name="Maintenance Income",
                account_type="income",
                normal_balance="credit",
            )
        ],
        existing_accounts=[parent],
    )

    assert preview.invalid_rows == 1
    assert "Parent account type must match child account type." in preview.rows[0].errors


def test_preview_chart_account_import_rejects_duplicate_existing_code() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    existing = ChartOfAccount(
        tenant_id=tenant_id,
        society_id=society_id,
        account_code="4000",
        account_name="Maintenance Income",
        account_type="income",
        normal_balance="credit",
    )

    preview = preview_chart_of_account_import_rows(
        rows=[
            ChartOfAccountImportInput(
                account_code="4000",
                account_name="Parking Income",
                account_type="income",
                normal_balance="credit",
            )
        ],
        existing_accounts=[existing],
    )

    assert preview.invalid_rows == 1
    assert "Account code already exists." in preview.rows[0].errors


def test_preview_chart_account_import_rejects_duplicate_file_name() -> None:
    preview = preview_chart_of_account_import_rows(
        rows=[
            ChartOfAccountImportInput(
                account_code="4000",
                account_name="Maintenance Income",
                account_type="income",
                normal_balance="credit",
            ),
            ChartOfAccountImportInput(
                account_code="4010",
                account_name="Maintenance Income",
                account_type="income",
                normal_balance="credit",
            ),
        ],
        existing_accounts=[],
    )

    assert preview.invalid_rows == 1
    assert "Account name is duplicated in this import file." in preview.rows[1].errors


def test_preview_chart_account_import_rejects_invalid_type_and_balance() -> None:
    preview = preview_chart_of_account_import_rows(
        rows=[
            ChartOfAccountImportInput(
                account_code="4000",
                account_name="Maintenance Income",
                account_type="revenue",
                normal_balance="plus",
            )
        ],
        existing_accounts=[],
    )

    assert preview.invalid_rows == 1
    assert "Account type must be asset, liability, equity, income, or expense." in preview.rows[0].errors
    assert "Normal balance must be debit or credit." in preview.rows[0].errors
