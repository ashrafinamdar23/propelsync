from typing import Annotated
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Invoice, Payment
from app.schemas.pagination import PaginatedResponse
from app.schemas.payment import (
    PaymentAllocationRead,
    PaymentCancelledPenaltyRead,
    PaymentCreate,
    PaymentDetailRead,
    PaymentRegisterRow,
    PaymentRead,
    PaymentReverseRequest,
)
from app.services.payments import (
    PaymentAllocationInvalidError,
    PaymentInvalidStateError,
    PaymentJournalPostingError,
    PaymentReferenceInvalidError,
    PaymentSocietyNotFoundError,
    create_payment,
    list_payment_register_for_export,
    list_payment_register_paginated,
    list_payment_allocations,
    list_payments,
    payment_register_export_table,
    reverse_payment,
)
from app.services.report_exports import build_pdf, build_xlsx
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/payments")


def payment_to_read(payment: Payment) -> PaymentRead:
    return PaymentRead.model_validate(payment)


def export_response(content: bytes, *, filename: str, export_format: str) -> Response:
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


def payment_detail_to_read(
    db: Session,
    *,
    payment: Payment,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    allocations: list,
) -> PaymentDetailRead:
    cancelled_penalty_invoice_ids = getattr(payment, "auto_cancelled_penalty_invoice_ids", [])
    cancelled_penalty_invoices = []
    if cancelled_penalty_invoice_ids:
        cancelled_penalty_invoices = list(
            db.scalars(
                select(Invoice)
                .where(
                    Invoice.id.in_(cancelled_penalty_invoice_ids),
                    Invoice.tenant_id == tenant_context.tenant_id,
                    Invoice.society_id == society_id,
                )
                .order_by(Invoice.invoice_date, Invoice.invoice_number)
            )
        )

    data = PaymentRead.model_validate(payment).model_dump()
    data["allocations"] = [PaymentAllocationRead.model_validate(allocation) for allocation in allocations]
    data["auto_cancelled_penalty_invoices"] = [
        PaymentCancelledPenaltyRead.model_validate(invoice) for invoice in cancelled_penalty_invoices
    ]
    return PaymentDetailRead.model_validate(data)


@router.get("", response_model=list[PaymentRead])
def read_payments(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PaymentRead]:
    try:
        payments = list_payments(db, tenant_context=tenant_context, society_id=society_id)
    except PaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [payment_to_read(payment) for payment in payments]


@router.get("/register", response_model=PaginatedResponse[PaymentRegisterRow])
def read_payment_register(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    flat_id: Annotated[uuid.UUID | None, Query()] = None,
    flat_number: Annotated[str | None, Query(max_length=50)] = None,
    payment_date_from: Annotated[date | None, Query()] = None,
    payment_date_to: Annotated[date | None, Query()] = None,
    payment_status: Annotated[str | None, Query(alias="status")] = None,
    payment_mode: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> PaginatedResponse[PaymentRegisterRow]:
    if payment_date_from and payment_date_to and payment_date_from > payment_date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="payment_date_from cannot be after payment_date_to.",
        )
    try:
        rows, total_items = list_payment_register_paginated(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_id=flat_id,
            flat_number=flat_number,
            status=payment_status,
            payment_mode=payment_mode,
            payment_date_from=payment_date_from,
            payment_date_to=payment_date_to,
            page=page,
            page_size=page_size,
        )
    except PaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return PaginatedResponse[PaymentRegisterRow](
        items=rows,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=(total_items + page_size - 1) // page_size,
    )


@router.get("/register/export")
def export_payment_register(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    flat_id: Annotated[uuid.UUID | None, Query()] = None,
    flat_number: Annotated[str | None, Query(max_length=50)] = None,
    payment_date_from: Annotated[date | None, Query()] = None,
    payment_date_to: Annotated[date | None, Query()] = None,
    payment_status: Annotated[str | None, Query(alias="status")] = None,
    payment_mode: Annotated[str | None, Query()] = None,
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
) -> Response:
    if payment_date_from and payment_date_to and payment_date_from > payment_date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="payment_date_from cannot be after payment_date_to.",
        )
    try:
        rows = list_payment_register_for_export(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_id=flat_id,
            flat_number=flat_number,
            status=payment_status,
            payment_mode=payment_mode,
            payment_date_from=payment_date_from,
            payment_date_to=payment_date_to,
        )
    except PaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    table = payment_register_export_table(
        rows,
        payment_date_from=payment_date_from,
        payment_date_to=payment_date_to,
    )
    content = build_xlsx(table) if export_format == "xlsx" else build_pdf(table)
    filename = f"payment-register.{export_format}"
    return export_response(content, filename=filename, export_format=export_format)


@router.post("", response_model=PaymentDetailRead, status_code=status.HTTP_201_CREATED)
def create_society_payment(
    society_id: uuid.UUID,
    payload: PaymentCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> PaymentDetailRead:
    try:
        payment = create_payment(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except PaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except (PaymentReferenceInvalidError, PaymentAllocationInvalidError, PaymentJournalPostingError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    allocations = list_payment_allocations(
        db,
        tenant_context=tenant_context,
        society_id=society_id,
        payment_id=payment.id,
    )
    return payment_detail_to_read(
        db,
        payment=payment,
        tenant_context=tenant_context,
        society_id=society_id,
        allocations=allocations,
    )


@router.post("/{payment_id}/reverse", response_model=PaymentDetailRead)
def reverse_society_payment(
    society_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: PaymentReverseRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> PaymentDetailRead:
    try:
        payment = reverse_payment(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payment_id=payment_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except PaymentSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except PaymentReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PaymentInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PaymentAllocationInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    allocations = list_payment_allocations(
        db,
        tenant_context=tenant_context,
        society_id=society_id,
        payment_id=payment.id,
    )
    return payment_detail_to_read(
        db,
        payment=payment,
        tenant_context=tenant_context,
        society_id=society_id,
        allocations=allocations,
    )
