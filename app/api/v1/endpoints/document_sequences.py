from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import DocumentSequence
from app.schemas.document_sequence import DocumentSequenceRead, DocumentSequenceUpdate
from app.services.document_sequences import (
    DocumentSequenceSocietyNotFoundError,
    get_or_create_invoice_sequence,
    update_invoice_sequence,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/document-sequences")


def document_sequence_to_read(sequence: DocumentSequence) -> DocumentSequenceRead:
    return DocumentSequenceRead.model_validate(sequence)


@router.get("/invoice", response_model=DocumentSequenceRead)
def read_invoice_sequence(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentSequenceRead:
    try:
        sequence = get_or_create_invoice_sequence(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
        )
    except DocumentSequenceSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return document_sequence_to_read(sequence)


@router.patch("/invoice", response_model=DocumentSequenceRead)
def update_society_invoice_sequence(
    society_id: uuid.UUID,
    payload: DocumentSequenceUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentSequenceRead:
    try:
        sequence = update_invoice_sequence(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except DocumentSequenceSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return document_sequence_to_read(sequence)
