from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import BillingRule
from app.schemas.billing_rule import BillingRuleCreate, BillingRuleRead, BillingRuleUpdate
from app.services.billing_rules import (
    BillingRuleAlreadyExistsError,
    BillingRuleNotFoundError,
    BillingRuleReferenceInvalidError,
    BillingRuleSocietyNotFoundError,
    change_billing_rule_status,
    create_billing_rule,
    list_billing_rules,
    update_billing_rule,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/billing-rules")


def billing_rule_to_read(rule: BillingRule) -> BillingRuleRead:
    return BillingRuleRead.model_validate(rule)


@router.get("", response_model=list[BillingRuleRead])
def read_billing_rules(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[BillingRuleRead]:
    try:
        rules = list_billing_rules(db, tenant_context=tenant_context, society_id=society_id)
    except BillingRuleSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [billing_rule_to_read(rule) for rule in rules]


@router.post("", response_model=BillingRuleRead, status_code=status.HTTP_201_CREATED)
def create_society_billing_rule(
    society_id: uuid.UUID,
    payload: BillingRuleCreate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BillingRuleRead:
    try:
        rule = create_billing_rule(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except BillingRuleSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except BillingRuleAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BillingRuleReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return billing_rule_to_read(rule)


@router.patch("/{billing_rule_id}", response_model=BillingRuleRead)
def update_society_billing_rule(
    society_id: uuid.UUID,
    billing_rule_id: uuid.UUID,
    payload: BillingRuleUpdate,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BillingRuleRead:
    try:
        rule = update_billing_rule(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            billing_rule_id=billing_rule_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except BillingRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing rule not found.") from exc
    except BillingRuleAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BillingRuleReferenceInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return billing_rule_to_read(rule)


@router.post("/{billing_rule_id}/inactivate", response_model=BillingRuleRead)
def inactivate_society_billing_rule(
    society_id: uuid.UUID,
    billing_rule_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BillingRuleRead:
    try:
        rule = change_billing_rule_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            billing_rule_id=billing_rule_id,
            status="inactive",
            actor=tenant_context.user,
        )
    except BillingRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing rule not found.") from exc
    return billing_rule_to_read(rule)


@router.post("/{billing_rule_id}/activate", response_model=BillingRuleRead)
def activate_society_billing_rule(
    society_id: uuid.UUID,
    billing_rule_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> BillingRuleRead:
    try:
        rule = change_billing_rule_status(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            billing_rule_id=billing_rule_id,
            status="active",
            actor=tenant_context.user,
        )
    except BillingRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing rule not found.") from exc
    return billing_rule_to_read(rule)
