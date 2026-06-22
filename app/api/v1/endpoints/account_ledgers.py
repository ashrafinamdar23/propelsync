from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.account_ledger import AccountLedgerRead
from app.services.account_ledgers import (
    AccountLedgerAccountNotFoundError,
    AccountLedgerSocietyNotFoundError,
    get_account_ledger,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/accounts/{account_id}/ledger")


@router.get("", response_model=AccountLedgerRead)
def read_account_ledger(
    society_id: uuid.UUID,
    account_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> AccountLedgerRead:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be after date_to.",
        )
    try:
        return get_account_ledger(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
        )
    except AccountLedgerSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except AccountLedgerAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.") from exc
