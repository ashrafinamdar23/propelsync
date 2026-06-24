from typing import Annotated
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Invoice
from app.schemas.invoice import (
    InvoiceBulkCancelRequest,
    InvoiceBulkCancelResponse,
    InvoiceCancelRequest,
    InvoiceDetailRead,
    InvoiceLineItemRead,
    InvoiceRead,
    ManualInvoiceCreate,
)
from app.schemas.invoice_generation import (
    InvoiceGenerationConfirmResponse,
    InvoiceGenerationPreviewResponse,
    InvoiceGenerationRequest,
)
from app.schemas.pagination import PaginatedResponse
from app.services.invoices import (
    InvoiceGenerationValidationError,
    InvoiceGenerationRuleSelectionError,
    InvoiceCancellationInvalidError,
    InvoiceJournalPostingError,
    InvoiceNotFoundError,
    InvoiceSocietyNotFoundError,
    ManualInvoiceReferenceInvalidError,
    bulk_cancel_invoices,
    cancel_invoice,
    confirm_invoice_generation,
    create_manual_invoice,
    get_invoice_or_raise,
    list_invoice_line_items,
    list_invoices,
    list_invoices_paginated,
    preview_invoice_generation,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/invoices")


def invoice_to_read(invoice: Invoice) -> InvoiceRead:
    return InvoiceRead.model_validate(invoice)


@router.get("", response_model=PaginatedResponse[InvoiceRead])
def read_invoices(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    flat_id: Annotated[uuid.UUID | None, Query()] = None,
    invoice_date_from: Annotated[date | None, Query()] = None,
    invoice_date_to: Annotated[date | None, Query()] = None,
    due_date_from: Annotated[date | None, Query()] = None,
    due_date_to: Annotated[date | None, Query()] = None,
    invoice_status: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> PaginatedResponse[InvoiceRead]:
    try:
        invoices, total_items = list_invoices_paginated(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_id=flat_id,
            status=invoice_status,
            invoice_date_from=invoice_date_from,
            invoice_date_to=invoice_date_to,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            page=page,
            page_size=page_size,
        )
    except InvoiceSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except InvoiceGenerationRuleSelectionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return PaginatedResponse[InvoiceRead](
        items=[invoice_to_read(invoice) for invoice in invoices],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=(total_items + page_size - 1) // page_size,
    )


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_manual_society_invoice(
    society_id: uuid.UUID,
    payload: ManualInvoiceCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> InvoiceRead:
    try:
        invoice = create_manual_invoice(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except InvoiceSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except (ManualInvoiceReferenceInvalidError, InvoiceJournalPostingError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return invoice_to_read(invoice)


@router.post("/bulk-cancel", response_model=InvoiceBulkCancelResponse)
def bulk_cancel_society_invoices(
    society_id: uuid.UUID,
    payload: InvoiceBulkCancelRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> InvoiceBulkCancelResponse:
    return bulk_cancel_invoices(
        db,
        tenant_context=tenant_context,
        society_id=society_id,
        invoice_ids=payload.invoice_ids,
        reason=payload.reason,
        actor=tenant_context.user,
    )


@router.post("/{invoice_id}/cancel", response_model=InvoiceRead)
def cancel_society_invoice(
    society_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payload: InvoiceCancelRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> InvoiceRead:
    try:
        invoice = cancel_invoice(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            invoice_id=invoice_id,
            reason=payload.reason,
            actor=tenant_context.user,
        )
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.") from exc
    except InvoiceCancellationInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return invoice_to_read(invoice)


@router.post("/generation/preview", response_model=InvoiceGenerationPreviewResponse)
def preview_generation(
    society_id: uuid.UUID,
    payload: InvoiceGenerationRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> InvoiceGenerationPreviewResponse:
    try:
        return preview_invoice_generation(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
        )
    except InvoiceSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.post("/generation/confirm", response_model=InvoiceGenerationConfirmResponse, status_code=status.HTTP_201_CREATED)
def confirm_generation(
    society_id: uuid.UUID,
    payload: InvoiceGenerationRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> InvoiceGenerationConfirmResponse:
    try:
        return confirm_invoice_generation(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except InvoiceSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except InvoiceGenerationRuleSelectionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except InvoiceGenerationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.preview.model_dump()) from exc
    except InvoiceJournalPostingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/{invoice_id}", response_model=InvoiceDetailRead)
def read_invoice(
    society_id: uuid.UUID,
    invoice_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> InvoiceDetailRead:
    try:
        invoice = get_invoice_or_raise(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            invoice_id=invoice_id,
        )
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.") from exc
    line_items = list_invoice_line_items(
        db,
        tenant_context=tenant_context,
        society_id=society_id,
        invoice_id=invoice.id,
    )
    data = InvoiceRead.model_validate(invoice).model_dump()
    data["line_items"] = [InvoiceLineItemRead.model_validate(item) for item in line_items]
    return InvoiceDetailRead.model_validate(data)
