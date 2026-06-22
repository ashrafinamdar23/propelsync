from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import LateFeeRule
from app.schemas.late_fee import (
    LateFeeApplyResponse,
    LateFeePreviewRequest,
    LateFeePreviewResponse,
    LateFeeRuleCreate,
    LateFeeRuleRead,
    LateFeeRuleUpdate,
)
from app.services.late_fees import (
    LateFeeApplicationValidationError,
    LateFeeJournalPostingError,
    LateFeeReferenceInvalidError,
    LateFeeRuleAlreadyExistsError,
    LateFeeRuleNotFoundError,
    LateFeeSocietyNotFoundError,
    apply_late_fees,
    change_late_fee_rule_status,
    create_late_fee_rule,
    list_late_fee_rules,
    preview_late_fee_application,
    update_late_fee_rule,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/late-fees")


def late_fee_rule_to_read(rule: LateFeeRule) -> LateFeeRuleRead:
    return LateFeeRuleRead.model_validate(rule)


@router.get("/rules", response_model=list[LateFeeRuleRead])
def read_late_fee_rules(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LateFeeRuleRead]:
    try:
        rules = list_late_fee_rules(db, tenant_context=tenant_context, society_id=society_id)
    except LateFeeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [late_fee_rule_to_read(rule) for rule in rules]


@router.post("/rules", response_model=LateFeeRuleRead, status_code=status.HTTP_201_CREATED)
def create_society_late_fee_rule(
    society_id: uuid.UUID,
    payload: LateFeeRuleCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LateFeeRuleRead:
    try:
        rule = create_late_fee_rule(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except LateFeeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except LateFeeRuleAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LateFeeReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return late_fee_rule_to_read(rule)


@router.patch("/rules/{late_fee_rule_id}", response_model=LateFeeRuleRead)
def update_society_late_fee_rule(
    society_id: uuid.UUID,
    late_fee_rule_id: uuid.UUID,
    payload: LateFeeRuleUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LateFeeRuleRead:
    try:
        rule = update_late_fee_rule(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            late_fee_rule_id=late_fee_rule_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except LateFeeRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Late fee rule not found.") from exc
    except LateFeeRuleAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LateFeeReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return late_fee_rule_to_read(rule)


@router.post("/rules/{late_fee_rule_id}/inactivate", response_model=LateFeeRuleRead)
def inactivate_society_late_fee_rule(
    society_id: uuid.UUID,
    late_fee_rule_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LateFeeRuleRead:
    try:
        rule = change_late_fee_rule_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            late_fee_rule_id=late_fee_rule_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except LateFeeRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Late fee rule not found.") from exc
    return late_fee_rule_to_read(rule)


@router.post("/rules/{late_fee_rule_id}/activate", response_model=LateFeeRuleRead)
def activate_society_late_fee_rule(
    society_id: uuid.UUID,
    late_fee_rule_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LateFeeRuleRead:
    try:
        rule = change_late_fee_rule_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            late_fee_rule_id=late_fee_rule_id,
            status="active",
            actor=tenant_context.user,
        )
    except LateFeeRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Late fee rule not found.") from exc
    return late_fee_rule_to_read(rule)


@router.post("/preview", response_model=LateFeePreviewResponse)
def preview_society_late_fees(
    society_id: uuid.UUID,
    payload: LateFeePreviewRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LateFeePreviewResponse:
    try:
        return preview_late_fee_application(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
        )
    except LateFeeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except LateFeeReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/apply", response_model=LateFeeApplyResponse, status_code=status.HTTP_201_CREATED)
def apply_society_late_fees(
    society_id: uuid.UUID,
    payload: LateFeePreviewRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> LateFeeApplyResponse:
    try:
        return apply_late_fees(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except LateFeeSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except LateFeeReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except LateFeeApplicationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.preview.model_dump(mode="json"),
        ) from exc
    except LateFeeJournalPostingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
