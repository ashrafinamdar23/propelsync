from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.balance_sheet import BalanceSheetReportRead
from app.services.balance_sheet import (
    BalanceSheetSocietyNotFoundError,
    export_balance_sheet_report,
    get_balance_sheet_report,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/reports/balance-sheet")


@router.get("", response_model=BalanceSheetReportRead)
def read_balance_sheet_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: date = Query(...),
) -> BalanceSheetReportRead:
    try:
        return get_balance_sheet_report(
            db, tenant_context=tenant_context, society_id=society_id, as_of_date=as_of_date
        )
    except BalanceSheetSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.get("/export")
def export_balance_sheet(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: date = Query(...),
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
) -> Response:
    try:
        report = get_balance_sheet_report(
            db, tenant_context=tenant_context, society_id=society_id, as_of_date=as_of_date
        )
    except BalanceSheetSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc

    content = export_balance_sheet_report(report, export_format)
    filename = f"balance-sheet-{as_of_date.isoformat()}.{export_format}"
    media_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if export_format == "xlsx"
        else "application/pdf"
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
