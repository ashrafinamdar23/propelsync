from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import OtherIncomeReceipt
from app.schemas.other_income import (
    OtherIncomeReceiptCreate,
    OtherIncomeReceiptRead,
    OtherIncomeReceiptReverseRequest,
)
from app.services.other_income import (
    OtherIncomeAccountInvalidError,
    OtherIncomeReceiptInvalidError,
    OtherIncomeReceiptNotFoundError,
    OtherIncomeSocietyNotFoundError,
    create_other_income_receipt,
    list_other_income_receipts,
    reverse_other_income_receipt,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/other-income-receipts")


def receipt_to_read(receipt: OtherIncomeReceipt) -> OtherIncomeReceiptRead:
    return OtherIncomeReceiptRead.model_validate(receipt)


@router.get("", response_model=list[OtherIncomeReceiptRead])
def read_other_income_receipts(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[OtherIncomeReceiptRead]:
    try:
        receipts = list_other_income_receipts(db, tenant_context=tenant_context, society_id=society_id)
    except OtherIncomeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [receipt_to_read(receipt) for receipt in receipts]


@router.post("", response_model=OtherIncomeReceiptRead, status_code=status.HTTP_201_CREATED)
def create_society_other_income_receipt(
    society_id: uuid.UUID,
    payload: OtherIncomeReceiptCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> OtherIncomeReceiptRead:
    try:
        receipt = create_other_income_receipt(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except OtherIncomeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except OtherIncomeAccountInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return receipt_to_read(receipt)


@router.post("/{receipt_id}/reverse", response_model=OtherIncomeReceiptRead)
def reverse_society_other_income_receipt(
    society_id: uuid.UUID,
    receipt_id: uuid.UUID,
    payload: OtherIncomeReceiptReverseRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> OtherIncomeReceiptRead:
    try:
        receipt = reverse_other_income_receipt(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            receipt_id=receipt_id,
            reason=payload.reason,
            actor=tenant_context.user,
        )
    except OtherIncomeReceiptNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Other income receipt not found.") from exc
    except OtherIncomeReceiptInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return receipt_to_read(receipt)
