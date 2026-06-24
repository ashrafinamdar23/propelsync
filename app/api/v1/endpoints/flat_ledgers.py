from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.flat_ledger import FlatLedgerRead
from app.services.flat_ledgers import (
    FlatLedgerFlatNotFoundError,
    get_flat_ledger,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/flats/{flat_id}/ledger")


@router.get("", response_model=FlatLedgerRead)
def read_flat_ledger(
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> FlatLedgerRead:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be after date_to.",
        )
    try:
        return get_flat_ledger(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_id=flat_id,
            date_from=date_from,
            date_to=date_to,
        )
    except FlatLedgerFlatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found.") from exc
