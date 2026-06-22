from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.income_expense import IncomeExpenseReportRead
from app.services.income_expense import (
    IncomeExpenseSocietyNotFoundError,
    export_income_expense_report,
    get_income_expense_report,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/reports/income-expense")


def validate_period(period_start: date, period_end: date) -> None:
    if period_start > period_end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="period_start cannot be after period_end.",
        )


@router.get("", response_model=IncomeExpenseReportRead)
def read_income_expense_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    period_start: date = Query(...),
    period_end: date = Query(...),
) -> IncomeExpenseReportRead:
    validate_period(period_start, period_end)
    try:
        return get_income_expense_report(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=period_start,
            period_end=period_end,
        )
    except IncomeExpenseSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.get("/export")
def export_income_expense(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    period_start: date = Query(...),
    period_end: date = Query(...),
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
) -> Response:
    validate_period(period_start, period_end)
    try:
        report = get_income_expense_report(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=period_start,
            period_end=period_end,
        )
    except IncomeExpenseSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc

    content = export_income_expense_report(report, export_format)
    filename = f"income-expense-{period_start.isoformat()}-{period_end.isoformat()}.{export_format}"
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
