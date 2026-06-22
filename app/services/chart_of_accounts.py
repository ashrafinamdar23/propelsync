import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChartOfAccount, Society, User
from app.schemas.chart_of_account import ChartOfAccountCreate, ChartOfAccountUpdate
from app.schemas.chart_of_account_import import (
    ChartOfAccountImportConfirmResponse,
    ChartOfAccountImportInput,
    ChartOfAccountImportPreviewResponse,
    ChartOfAccountImportPreviewRow,
)
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class ChartOfAccountAlreadyExistsError(Exception):
    pass


class ChartOfAccountNotFoundError(Exception):
    pass


class ChartOfAccountSocietyNotFoundError(Exception):
    pass


class ChartOfAccountParentInvalidError(Exception):
    pass


class ChartOfAccountImportValidationError(Exception):
    def __init__(self, preview: ChartOfAccountImportPreviewResponse) -> None:
        self.preview = preview
        super().__init__("Chart of accounts import has validation errors.")


VALID_ACCOUNT_TYPES = {"asset", "liability", "equity", "income", "expense"}
VALID_NORMAL_BALANCES = {"debit", "credit"}


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def normalize_lookup(value: str | None) -> str:
    return clean_text(value).casefold()


def ensure_society_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> None:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise ChartOfAccountSocietyNotFoundError("Society not found.")


def ensure_account_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ChartOfAccountCreate | ChartOfAccountUpdate,
    existing_account_id: uuid.UUID | None = None,
) -> None:
    for field, value, message in (
        ("account_code", payload.account_code, "Account code already exists."),
        ("account_name", payload.account_name, "Account name already exists."),
    ):
        statement = select(ChartOfAccount).where(
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            getattr(ChartOfAccount, field) == value,
        )
        if existing_account_id is not None:
            statement = statement.where(ChartOfAccount.id != existing_account_id)
        if session.scalar(statement) is not None:
            raise ChartOfAccountAlreadyExistsError(message)


def get_parent_account(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    parent_account_id: uuid.UUID | None,
) -> ChartOfAccount | None:
    if parent_account_id is None:
        return None
    parent = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == parent_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
        )
    )
    if parent is None:
        raise ChartOfAccountParentInvalidError("Parent account not found.")
    return parent


def ensure_parent_is_valid(
    *,
    account: ChartOfAccount | None,
    parent: ChartOfAccount | None,
    account_type: str,
    normal_balance: str,
) -> None:
    if parent is None:
        return
    if account is not None and parent.id == account.id:
        raise ChartOfAccountParentInvalidError("Account cannot be its own parent.")
    if parent.account_type != account_type:
        raise ChartOfAccountParentInvalidError("Parent account type must match child account type.")
    if parent.normal_balance != normal_balance:
        raise ChartOfAccountParentInvalidError("Parent normal balance must match child normal balance.")


def ensure_parent_is_not_descendant(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    account: ChartOfAccount,
    parent: ChartOfAccount | None,
) -> None:
    if parent is None:
        return
    accounts = list(
        session.scalars(
            select(ChartOfAccount).where(
                ChartOfAccount.tenant_id == tenant_context.tenant_id,
                ChartOfAccount.society_id == society_id,
            )
        )
    )
    parent_by_id = {item.id: item.parent_account_id for item in accounts}
    cursor = parent.id
    while cursor is not None:
        if cursor == account.id:
            raise ChartOfAccountParentInvalidError("Parent account cannot be a descendant.")
        cursor = parent_by_id.get(cursor)


def list_chart_of_accounts(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[ChartOfAccount]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(ChartOfAccount)
            .where(
                ChartOfAccount.tenant_id == tenant_context.tenant_id,
                ChartOfAccount.society_id == society_id,
            )
            .order_by(ChartOfAccount.account_code)
        )
    )


def preview_chart_of_account_import_rows(
    *,
    rows: list[ChartOfAccountImportInput],
    existing_accounts: list[ChartOfAccount],
) -> ChartOfAccountImportPreviewResponse:
    existing_codes = {normalize_lookup(account.account_code) for account in existing_accounts}
    existing_names = {normalize_lookup(account.account_name) for account in existing_accounts}
    existing_by_code = {normalize_lookup(account.account_code): account for account in existing_accounts}
    pending_codes: set[str] = set()
    pending_names: set[str] = set()
    pending_by_code: dict[str, tuple[str, str]] = {}
    preview_rows: list[ChartOfAccountImportPreviewRow] = []

    for index, row in enumerate(rows, start=1):
        errors: list[str] = []
        account_code = clean_text(row.account_code)
        parent_account_code = clean_text(row.parent_account_code)
        account_name = clean_text(row.account_name)
        account_type = normalize_lookup(row.account_type)
        normal_balance = normalize_lookup(row.normal_balance)
        code_key = normalize_lookup(account_code)
        parent_code_key = normalize_lookup(parent_account_code)
        name_key = normalize_lookup(account_name)

        if not account_code:
            errors.append("Account code is required.")
        elif code_key in existing_codes:
            errors.append("Account code already exists.")
        elif code_key in pending_codes:
            errors.append("Account code is duplicated in this import file.")

        if not account_name:
            errors.append("Account name is required.")
        elif name_key in existing_names:
            errors.append("Account name already exists.")
        elif name_key in pending_names:
            errors.append("Account name is duplicated in this import file.")

        if not account_type:
            errors.append("Account type is required.")
        elif account_type not in VALID_ACCOUNT_TYPES:
            errors.append("Account type must be asset, liability, equity, income, or expense.")

        if not normal_balance:
            errors.append("Normal balance is required.")
        elif normal_balance not in VALID_NORMAL_BALANCES:
            errors.append("Normal balance must be debit or credit.")

        if parent_code_key:
            if parent_code_key == code_key:
                errors.append("Parent account code cannot be the same as account code.")
            else:
                existing_parent = existing_by_code.get(parent_code_key)
                pending_parent = pending_by_code.get(parent_code_key)
                if existing_parent is None and pending_parent is None:
                    errors.append("Parent account code must already exist or appear earlier in this file.")
                elif existing_parent is not None:
                    if existing_parent.account_type != account_type:
                        errors.append("Parent account type must match child account type.")
                    if existing_parent.normal_balance != normal_balance:
                        errors.append("Parent normal balance must match child normal balance.")
                elif pending_parent is not None:
                    parent_type, parent_balance = pending_parent
                    if parent_type != account_type:
                        errors.append("Parent account type must match child account type.")
                    if parent_balance != normal_balance:
                        errors.append("Parent normal balance must match child normal balance.")

        if not errors:
            pending_codes.add(code_key)
            pending_names.add(name_key)
            pending_by_code[code_key] = (account_type, normal_balance)

        preview_rows.append(
            ChartOfAccountImportPreviewRow(
                row_number=index,
                input=row,
                status="invalid" if errors else "valid",
                errors=errors,
            )
        )

    invalid_rows = sum(1 for row in preview_rows if row.status == "invalid")
    return ChartOfAccountImportPreviewResponse(
        total_rows=len(preview_rows),
        valid_rows=len(preview_rows) - invalid_rows,
        invalid_rows=invalid_rows,
        rows=preview_rows,
    )


def preview_chart_of_account_import(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    rows: list[ChartOfAccountImportInput],
) -> ChartOfAccountImportPreviewResponse:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    existing_accounts = list_chart_of_accounts(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
    )
    return preview_chart_of_account_import_rows(rows=rows, existing_accounts=existing_accounts)


def confirm_chart_of_account_import(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    rows: list[ChartOfAccountImportInput],
    actor: User,
) -> ChartOfAccountImportConfirmResponse:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    existing_accounts = list_chart_of_accounts(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
    )
    preview = preview_chart_of_account_import_rows(rows=rows, existing_accounts=existing_accounts)
    if preview.invalid_rows:
        raise ChartOfAccountImportValidationError(preview)

    imported_accounts: list[ChartOfAccount] = []
    account_by_code = {normalize_lookup(account.account_code): account for account in existing_accounts}
    for row in rows:
        parent = account_by_code.get(normalize_lookup(row.parent_account_code))
        account = ChartOfAccount(
            id=uuid.uuid4(),
            tenant_id=tenant_context.tenant_id,
            society_id=society_id,
            parent_account_id=getattr(parent, "id", None),
            account_code=clean_text(row.account_code),
            account_name=clean_text(row.account_name),
            account_type=normalize_lookup(row.account_type),
            normal_balance=normalize_lookup(row.normal_balance),
            description=clean_text(row.description) or None,
            status="active",
        )
        session.add(account)
        imported_accounts.append(account)
        account_by_code[normalize_lookup(account.account_code)] = account

    session.flush()
    account_ids = [account.id for account in imported_accounts]
    record_audit_log(
        session,
        action="chart_of_account.bulk_imported",
        entity_type="ChartOfAccount",
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Bulk chart of accounts import completed: {len(imported_accounts)} accounts",
        metadata={
            "society_id": str(society_id),
            "imported_count": len(imported_accounts),
            "account_ids": [str(account_id) for account_id in account_ids],
        },
    )
    session.commit()
    return ChartOfAccountImportConfirmResponse(imported_count=len(imported_accounts), account_ids=account_ids)


def get_account_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    account_id: uuid.UUID,
) -> ChartOfAccount:
    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
        )
    )
    if account is None:
        raise ChartOfAccountNotFoundError("Account not found.")
    return account


def create_chart_of_account(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ChartOfAccountCreate,
    actor: User,
) -> ChartOfAccount:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    ensure_account_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    parent = get_parent_account(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        parent_account_id=payload.parent_account_id,
    )
    ensure_parent_is_valid(
        account=None,
        parent=parent,
        account_type=payload.account_type,
        normal_balance=payload.normal_balance,
    )
    account = ChartOfAccount(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        parent_account_id=getattr(parent, "id", None),
        account_code=payload.account_code,
        account_name=payload.account_name,
        account_type=payload.account_type,
        normal_balance=payload.normal_balance,
        description=payload.description,
        status="active",
    )
    session.add(account)
    session.flush()
    record_audit_log(
        session,
        action="chart_of_account.created",
        entity_type="ChartOfAccount",
        entity_id=account.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Chart account created: {account.account_code} {account.account_name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(account)
    return account


def update_chart_of_account(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    account_id: uuid.UUID,
    payload: ChartOfAccountUpdate,
    actor: User,
) -> ChartOfAccount:
    account = get_account_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        account_id=account_id,
    )
    ensure_account_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        existing_account_id=account.id,
    )
    parent = get_parent_account(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        parent_account_id=payload.parent_account_id,
    )
    ensure_parent_is_valid(
        account=account,
        parent=parent,
        account_type=payload.account_type,
        normal_balance=payload.normal_balance,
    )
    ensure_parent_is_not_descendant(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        account=account,
        parent=parent,
    )
    account.parent_account_id = getattr(parent, "id", None)
    account.account_code = payload.account_code
    account.account_name = payload.account_name
    account.account_type = payload.account_type
    account.normal_balance = payload.normal_balance
    account.description = payload.description
    record_audit_log(
        session,
        action="chart_of_account.updated",
        entity_type="ChartOfAccount",
        entity_id=account.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Chart account updated: {account.account_code} {account.account_name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(account)
    return account


def change_chart_of_account_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    account_id: uuid.UUID,
    status: str,
    actor: User,
) -> ChartOfAccount:
    account = get_account_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        account_id=account_id,
    )
    account.status = status
    record_audit_log(
        session,
        action="chart_of_account.inactivated" if status == "inactive" else "chart_of_account.activated",
        entity_type="ChartOfAccount",
        entity_id=account.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Chart account {status}: {account.account_code} {account.account_name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(account)
    return account
