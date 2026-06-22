from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.outstanding import OutstandingSummary
from app.services.outstanding import OutstandingSocietyNotFoundError, calculate_outstanding_summary
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/outstanding")


@router.get("", response_model=OutstandingSummary)
def read_outstanding_summary(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: Annotated[date | None, Query()] = None,
) -> OutstandingSummary:
    try:
        return calculate_outstanding_summary(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=as_of_date or date.today(),
        )
    except OutstandingSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
