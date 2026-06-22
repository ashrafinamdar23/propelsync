from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import Invoice
from app.schemas.invoice import InvoiceCancelRequest, InvoiceDetailRead, InvoiceLineItemRead, InvoiceRead, ManualInvoiceCreate
from app.schemas.invoice_generation import (
    InvoiceGenerationConfirmResponse,
    InvoiceGenerationPreviewResponse,
    InvoiceGenerationRequest,
)
from app.services.invoices import (
    InvoiceGenerationValidationError,
    InvoiceGenerationRuleSelectionError,
    InvoiceCancellationInvalidError,
    InvoiceJournalPostingError,
    InvoiceNotFoundError,
    InvoiceSocietyNotFoundError,
    ManualInvoiceReferenceInvalidError,
    cancel_invoice,
    confirm_invoice_generation,
    create_manual_invoice,
    get_invoice_or_raise,
    list_invoice_line_items,
    list_invoices,
    preview_invoice_generation,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/invoices")


def invoice_to_read(invoice: Invoice) -> InvoiceRead:
    return InvoiceRead.model_validate(invoice)


@router.get("", response_model=list[InvoiceRead])
def read_invoices(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InvoiceRead]:
    try:
        invoices = list_invoices(db, tenant_context=tenant_context, society_id=society_id)
    except InvoiceSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except InvoiceGenerationRuleSelectionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [invoice_to_read(invoice) for invoice in invoices]


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
