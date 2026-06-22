from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import JournalEntry
from app.schemas.journal import (
    JournalEntryCreate,
    JournalEntryDetailRead,
    JournalEntryRead,
    JournalReverseRequest,
    JournalLineRead,
    OpeningBalanceJournalCreate,
)
from app.services.journals import (
    JournalAccountInvalidError,
    JournalReversalInvalidError,
    JournalSocietyNotFoundError,
    JournalValidationError,
    create_manual_journal_entry,
    create_opening_balance_journal_entry,
    get_journal_entry_or_raise,
    list_journal_entries,
    list_journal_lines,
    reverse_journal_entry,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/journals")


def journal_to_read(entry: JournalEntry) -> JournalEntryRead:
    return JournalEntryRead.model_validate(entry)


@router.get("", response_model=list[JournalEntryRead])
def read_journal_entries(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[JournalEntryRead]:
    try:
        entries = list_journal_entries(db, tenant_context=tenant_context, society_id=society_id)
    except JournalSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [journal_to_read(entry) for entry in entries]


@router.get("/{journal_entry_id}", response_model=JournalEntryDetailRead)
def read_journal_entry_detail(
    society_id: uuid.UUID,
    journal_entry_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> JournalEntryDetailRead:
    try:
        entry = get_journal_entry_or_raise(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            journal_entry_id=journal_entry_id,
        )
    except JournalSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except JournalValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    lines = list_journal_lines(db, tenant_context=tenant_context, society_id=society_id, journal_entry_id=entry.id)
    data = JournalEntryRead.model_validate(entry).model_dump()
    data["lines"] = [JournalLineRead.model_validate(line) for line in lines]
    return JournalEntryDetailRead.model_validate(data)


@router.post("", response_model=JournalEntryDetailRead, status_code=status.HTTP_201_CREATED)
def create_society_manual_journal(
    society_id: uuid.UUID,
    payload: JournalEntryCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> JournalEntryDetailRead:
    try:
        entry = create_manual_journal_entry(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except JournalSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except (JournalAccountInvalidError, JournalValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    lines = list_journal_lines(db, tenant_context=tenant_context, society_id=society_id, journal_entry_id=entry.id)
    data = JournalEntryRead.model_validate(entry).model_dump()
    data["lines"] = [JournalLineRead.model_validate(line) for line in lines]
    return JournalEntryDetailRead.model_validate(data)


@router.post("/opening-balance", response_model=JournalEntryDetailRead, status_code=status.HTTP_201_CREATED)
def create_society_opening_balance_journal(
    society_id: uuid.UUID,
    payload: OpeningBalanceJournalCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> JournalEntryDetailRead:
    try:
        entry = create_opening_balance_journal_entry(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except JournalSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except (JournalAccountInvalidError, JournalValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    lines = list_journal_lines(db, tenant_context=tenant_context, society_id=society_id, journal_entry_id=entry.id)
    data = JournalEntryRead.model_validate(entry).model_dump()
    data["lines"] = [JournalLineRead.model_validate(line) for line in lines]
    return JournalEntryDetailRead.model_validate(data)


@router.post("/{journal_entry_id}/reverse", response_model=JournalEntryRead)
def reverse_society_journal_entry(
    society_id: uuid.UUID,
    journal_entry_id: uuid.UUID,
    payload: JournalReverseRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> JournalEntryRead:
    try:
        entry = reverse_journal_entry(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            journal_entry_id=journal_entry_id,
            reason=payload.reason,
            actor=tenant_context.user,
        )
    except JournalSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except JournalValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except JournalReversalInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return JournalEntryRead.model_validate(entry)
