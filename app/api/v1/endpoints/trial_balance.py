from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.trial_balance import TrialBalanceRead
from app.services.trial_balance import TrialBalanceSocietyNotFoundError, get_trial_balance
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/trial-balance")


@router.get("", response_model=TrialBalanceRead)
def read_trial_balance(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: date = Query(...),
) -> TrialBalanceRead:
    try:
        return get_trial_balance(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=as_of_date,
        )
    except TrialBalanceSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
