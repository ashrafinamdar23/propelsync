from datetime import date
from typing import Annotated, Callable
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.operational_report import (
    BillingReportRead,
    CollectionReportRead,
    DefaulterReportRead,
    ExpenseReportRead,
)
from app.schemas.outstanding import OutstandingSummary
from app.services.operational_reports import (
    OperationalReportSocietyNotFoundError,
    billing_export_table,
    collection_export_table,
    defaulter_export_table,
    expense_export_table,
    export_table,
    get_billing_report,
    get_collection_report,
    get_defaulter_report,
    get_expense_report,
    outstanding_export_table,
)
from app.services.outstanding import OutstandingSocietyNotFoundError, calculate_outstanding_summary
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/reports")


def validate_period(period_start: date, period_end: date) -> None:
    if period_start > period_end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="period_start cannot be after period_end.",
        )


def report_response(content: bytes, *, filename: str, export_format: str) -> Response:
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


def export_period_report(
    *,
    society_id: uuid.UUID,
    tenant_context: TenantContext,
    db: Session,
    period_start: date,
    period_end: date,
    export_format: str,
    loader: Callable[..., BaseModel],
    table_builder: Callable[[BaseModel], object],
    filename_prefix: str,
) -> Response:
    validate_period(period_start, period_end)
    try:
        report = loader(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=period_start,
            period_end=period_end,
        )
    except OperationalReportSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    table = table_builder(report)
    content = export_table(table, export_format)  # type: ignore[arg-type]
    filename = f"{filename_prefix}-{period_start.isoformat()}-{period_end.isoformat()}.{export_format}"
    return report_response(content, filename=filename, export_format=export_format)


@router.get("/billing", response_model=BillingReportRead)
def read_billing_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    period_start: date = Query(...),
    period_end: date = Query(...),
) -> BillingReportRead:
    validate_period(period_start, period_end)
    try:
        return get_billing_report(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=period_start,
            period_end=period_end,
        )
    except OperationalReportSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.get("/billing/export")
def export_billing_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    period_start: date = Query(...),
    period_end: date = Query(...),
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
) -> Response:
    return export_period_report(
        society_id=society_id,
        tenant_context=tenant_context,
        db=db,
        period_start=period_start,
        period_end=period_end,
        export_format=export_format,
        loader=get_billing_report,
        table_builder=billing_export_table,
        filename_prefix="billing",
    )


@router.get("/collection", response_model=CollectionReportRead)
def read_collection_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    period_start: date = Query(...),
    period_end: date = Query(...),
) -> CollectionReportRead:
    validate_period(period_start, period_end)
    try:
        return get_collection_report(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=period_start,
            period_end=period_end,
        )
    except OperationalReportSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.get("/collection/export")
def export_collection_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    period_start: date = Query(...),
    period_end: date = Query(...),
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
) -> Response:
    return export_period_report(
        society_id=society_id,
        tenant_context=tenant_context,
        db=db,
        period_start=period_start,
        period_end=period_end,
        export_format=export_format,
        loader=get_collection_report,
        table_builder=collection_export_table,
        filename_prefix="collection",
    )


@router.get("/expenses", response_model=ExpenseReportRead)
def read_expense_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    period_start: date = Query(...),
    period_end: date = Query(...),
) -> ExpenseReportRead:
    validate_period(period_start, period_end)
    try:
        return get_expense_report(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            period_start=period_start,
            period_end=period_end,
        )
    except OperationalReportSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.get("/expenses/export")
def export_expense_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    period_start: date = Query(...),
    period_end: date = Query(...),
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
) -> Response:
    return export_period_report(
        society_id=society_id,
        tenant_context=tenant_context,
        db=db,
        period_start=period_start,
        period_end=period_end,
        export_format=export_format,
        loader=get_expense_report,
        table_builder=expense_export_table,
        filename_prefix="expenses",
    )


@router.get("/defaulters", response_model=DefaulterReportRead)
def read_defaulter_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: date = Query(...),
) -> DefaulterReportRead:
    try:
        return get_defaulter_report(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=as_of_date,
        )
    except OutstandingSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.get("/defaulters/export")
def export_defaulter_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: date = Query(...),
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
) -> Response:
    try:
        report = get_defaulter_report(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=as_of_date,
        )
    except OutstandingSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    content = export_table(defaulter_export_table(report), export_format)
    return report_response(
        content,
        filename=f"defaulters-{as_of_date.isoformat()}.{export_format}",
        export_format=export_format,
    )


@router.get("/outstanding", response_model=OutstandingSummary)
def read_outstanding_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: date = Query(...),
) -> OutstandingSummary:
    try:
        return calculate_outstanding_summary(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=as_of_date,
        )
    except OutstandingSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.get("/outstanding/export")
def export_outstanding_report(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: date = Query(...),
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
) -> Response:
    try:
        report = calculate_outstanding_summary(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=as_of_date,
        )
    except OutstandingSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    content = export_table(outstanding_export_table(report), export_format)
    return report_response(
        content,
        filename=f"outstanding-{as_of_date.isoformat()}.{export_format}",
        export_format=export_format,
    )
