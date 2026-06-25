from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.monthly_report import MonthlySocietyReportRead
from app.services.monthly_reports import (
    MonthlyReportInvalidMonthError,
    MonthlyReportSocietyNotFoundError,
    export_monthly_society_report_xlsx,
    get_monthly_society_report,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/reports/monthly")


def load_monthly_report(
    *,
    society_id: uuid.UUID,
    tenant_context: TenantContext,
    db: Session,
    report_month: str,
) -> MonthlySocietyReportRead:
    try:
        return get_monthly_society_report(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            report_month=report_month,
        )
    except MonthlyReportSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except MonthlyReportInvalidMonthError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("", response_model=MonthlySocietyReportRead)
def read_monthly_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    report_month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
) -> MonthlySocietyReportRead:
    return load_monthly_report(
        society_id=society_id,
        tenant_context=tenant_context,
        db=db,
        report_month=report_month,
    )


@router.get("/export")
def export_monthly_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    report_month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    export_format: Annotated[str, Query(pattern="^xlsx$")] = "xlsx",
) -> Response:
    report = load_monthly_report(
        society_id=society_id,
        tenant_context=tenant_context,
        db=db,
        report_month=report_month,
    )
    content = export_monthly_society_report_xlsx(report)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="monthly-report-{report_month}.{export_format}"'},
    )
