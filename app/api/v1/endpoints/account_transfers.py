from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import AccountTransfer
from app.schemas.account_transfer import AccountTransferCreate, AccountTransferRead
from app.services.account_transfers import (
    AccountTransferAccountInvalidError,
    AccountTransferSocietyNotFoundError,
    AccountTransferValidationError,
    create_account_transfer,
    list_account_transfers,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/account-transfers")


def transfer_to_read(transfer: AccountTransfer) -> AccountTransferRead:
    return AccountTransferRead.model_validate(transfer)


@router.get("", response_model=list[AccountTransferRead])
def read_account_transfers(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AccountTransferRead]:
    try:
        transfers = list_account_transfers(db, tenant_context=tenant_context, society_id=society_id)
    except AccountTransferSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [transfer_to_read(transfer) for transfer in transfers]


@router.post("", response_model=AccountTransferRead, status_code=status.HTTP_201_CREATED)
def create_society_account_transfer(
    society_id: uuid.UUID,
    payload: AccountTransferCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> AccountTransferRead:
    try:
        transfer = create_account_transfer(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except AccountTransferSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except (AccountTransferAccountInvalidError, AccountTransferValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return transfer_to_read(transfer)
