from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import ChartOfAccount
from app.schemas.chart_of_account import (
    ChartOfAccountCreate,
    ChartOfAccountRead,
    ChartOfAccountUpdate,
)
from app.schemas.chart_of_account_import import (
    ChartOfAccountImportConfirmRequest,
    ChartOfAccountImportConfirmResponse,
    ChartOfAccountImportPreviewRequest,
    ChartOfAccountImportPreviewResponse,
)
from app.services.chart_of_accounts import (
    ChartOfAccountAlreadyExistsError,
    ChartOfAccountImportValidationError,
    ChartOfAccountNotFoundError,
    ChartOfAccountParentInvalidError,
    ChartOfAccountSocietyNotFoundError,
    change_chart_of_account_status,
    confirm_chart_of_account_import,
    create_chart_of_account,
    list_chart_of_accounts,
    preview_chart_of_account_import,
    update_chart_of_account,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/chart-of-accounts")


def account_to_read(account: ChartOfAccount) -> ChartOfAccountRead:
    return ChartOfAccountRead.model_validate(account)


@router.get("", response_model=list[ChartOfAccountRead])
def read_chart_of_accounts(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ChartOfAccountRead]:
    try:
        accounts = list_chart_of_accounts(db, tenant_context=tenant_context, society_id=society_id)
    except ChartOfAccountSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [account_to_read(account) for account in accounts]


@router.post("/import/preview", response_model=ChartOfAccountImportPreviewResponse)
def preview_society_chart_account_import(
    society_id: uuid.UUID,
    payload: ChartOfAccountImportPreviewRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChartOfAccountImportPreviewResponse:
    try:
        return preview_chart_of_account_import(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            rows=payload.rows,
        )
    except ChartOfAccountSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.post(
    "/import/confirm",
    response_model=ChartOfAccountImportConfirmResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_society_chart_account_import(
    society_id: uuid.UUID,
    payload: ChartOfAccountImportConfirmRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChartOfAccountImportConfirmResponse:
    try:
        return confirm_chart_of_account_import(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            rows=payload.rows,
            actor=tenant_context.user,
        )
    except ChartOfAccountSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except ChartOfAccountImportValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.preview.model_dump()) from exc


@router.post("", response_model=ChartOfAccountRead, status_code=status.HTTP_201_CREATED)
def create_society_chart_account(
    society_id: uuid.UUID,
    payload: ChartOfAccountCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChartOfAccountRead:
    try:
        account = create_chart_of_account(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ChartOfAccountSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except ChartOfAccountAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ChartOfAccountParentInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return account_to_read(account)


@router.patch("/{account_id}", response_model=ChartOfAccountRead)
def update_society_chart_account(
    society_id: uuid.UUID,
    account_id: uuid.UUID,
    payload: ChartOfAccountUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChartOfAccountRead:
    try:
        account = update_chart_of_account(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            account_id=account_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ChartOfAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.") from exc
    except ChartOfAccountAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ChartOfAccountParentInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return account_to_read(account)


@router.post("/{account_id}/inactivate", response_model=ChartOfAccountRead)
def inactivate_society_chart_account(
    society_id: uuid.UUID,
    account_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChartOfAccountRead:
    try:
        account = change_chart_of_account_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            account_id=account_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except ChartOfAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.") from exc
    return account_to_read(account)


@router.post("/{account_id}/activate", response_model=ChartOfAccountRead)
def activate_society_chart_account(
    society_id: uuid.UUID,
    account_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ChartOfAccountRead:
    try:
        account = change_chart_of_account_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            account_id=account_id,
            status="active",
            actor=tenant_context.user,
        )
    except ChartOfAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.") from exc
    return account_to_read(account)
