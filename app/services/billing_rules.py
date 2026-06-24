import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BillingRule, BillingRuleLateFeeRule, Building, ChargeType, FlatType, LateFeeRule, Society, User, Wing
from app.schemas.billing_rule import BillingRuleCreate, BillingRuleUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class BillingRuleAlreadyExistsError(Exception):
    pass


class BillingRuleNotFoundError(Exception):
    pass


class BillingRuleSocietyNotFoundError(Exception):
    pass


class BillingRuleReferenceInvalidError(Exception):
    pass


def ensure_society_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> None:
    society = session.scalar(
        select(Society).where(
            Society.id == society_id,
            Society.tenant_id == tenant_context.tenant_id,
        )
    )
    if society is None:
        raise BillingRuleSocietyNotFoundError("Society not found.")


def ensure_billing_rule_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: BillingRuleCreate | BillingRuleUpdate,
    existing_rule_id: uuid.UUID | None = None,
) -> None:
    statement = select(BillingRule).where(
        BillingRule.tenant_id == tenant_context.tenant_id,
        BillingRule.society_id == society_id,
        BillingRule.name == payload.name,
    )
    if existing_rule_id is not None:
        statement = statement.where(BillingRule.id != existing_rule_id)
    if session.scalar(statement) is not None:
        raise BillingRuleAlreadyExistsError("Billing rule name already exists.")


def ensure_references_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: BillingRuleCreate | BillingRuleUpdate,
) -> None:
    charge_type = session.scalar(
        select(ChargeType).where(
            ChargeType.id == payload.charge_type_id,
            ChargeType.tenant_id == tenant_context.tenant_id,
            ChargeType.society_id == society_id,
            ChargeType.status == "active",
        )
    )
    if charge_type is None:
        raise BillingRuleReferenceInvalidError("Charge type must be active and belong to this society.")

    if payload.building_id is not None:
        building = session.scalar(
            select(Building).where(
                Building.id == payload.building_id,
                Building.tenant_id == tenant_context.tenant_id,
                Building.society_id == society_id,
                Building.status == "active",
            )
        )
        if building is None:
            raise BillingRuleReferenceInvalidError("Building must be active and belong to this society.")

    if payload.wing_id is not None:
        wing = session.scalar(
            select(Wing).where(
                Wing.id == payload.wing_id,
                Wing.tenant_id == tenant_context.tenant_id,
                Wing.society_id == society_id,
                Wing.building_id == payload.building_id,
                Wing.status == "active",
            )
        )
        if wing is None:
            raise BillingRuleReferenceInvalidError("Wing must be active and belong to the selected building.")

    if payload.flat_type_id is not None:
        flat_type = session.scalar(
            select(FlatType).where(
                FlatType.id == payload.flat_type_id,
                FlatType.tenant_id == tenant_context.tenant_id,
                FlatType.society_id == society_id,
                FlatType.status == "active",
            )
        )
        if flat_type is None:
            raise BillingRuleReferenceInvalidError("Flat type must be active and belong to this society.")

    ensure_late_fee_rules_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        late_fee_rule_ids=payload.late_fee_rule_ids,
    )


def ensure_late_fee_rules_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    late_fee_rule_ids: list[uuid.UUID],
) -> None:
    if not late_fee_rule_ids:
        return
    if len(set(late_fee_rule_ids)) != len(late_fee_rule_ids):
        raise BillingRuleReferenceInvalidError("Penalty rules cannot contain duplicates.")
    found_rule_ids = set(
        session.scalars(
            select(LateFeeRule.id).where(
                LateFeeRule.id.in_(late_fee_rule_ids),
                LateFeeRule.tenant_id == tenant_context.tenant_id,
                LateFeeRule.society_id == society_id,
                LateFeeRule.status == "active",
            )
        )
    )
    if found_rule_ids != set(late_fee_rule_ids):
        raise BillingRuleReferenceInvalidError("All penalty rules must be active and belong to this society.")


def replace_billing_rule_late_fee_rules(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    rule: BillingRule,
    late_fee_rule_ids: list[uuid.UUID],
) -> None:
    existing = list(
        session.scalars(
            select(BillingRuleLateFeeRule).where(
                BillingRuleLateFeeRule.tenant_id == tenant_context.tenant_id,
                BillingRuleLateFeeRule.society_id == society_id,
                BillingRuleLateFeeRule.billing_rule_id == rule.id,
            )
        )
    )
    for row in existing:
        session.delete(row)
    if existing:
        session.flush()
    for priority, late_fee_rule_id in enumerate(late_fee_rule_ids):
        session.add(
            BillingRuleLateFeeRule(
                tenant_id=tenant_context.tenant_id,
                society_id=society_id,
                billing_rule_id=rule.id,
                late_fee_rule_id=late_fee_rule_id,
                priority=priority,
                effective_from=rule.effective_from,
                effective_to=rule.effective_to,
                status="active",
            )
        )


def list_billing_rule_late_fee_rule_ids(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> dict[uuid.UUID, list[uuid.UUID]]:
    rows = list(
        session.scalars(
            select(BillingRuleLateFeeRule)
            .where(
                BillingRuleLateFeeRule.tenant_id == tenant_context.tenant_id,
                BillingRuleLateFeeRule.society_id == society_id,
                BillingRuleLateFeeRule.status == "active",
            )
            .order_by(BillingRuleLateFeeRule.billing_rule_id, BillingRuleLateFeeRule.priority)
        )
    )
    rule_ids: dict[uuid.UUID, list[uuid.UUID]] = {}
    for row in rows:
        rule_ids.setdefault(row.billing_rule_id, []).append(row.late_fee_rule_id)
    return rule_ids


def list_billing_rules(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[BillingRule]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(BillingRule)
            .where(
                BillingRule.tenant_id == tenant_context.tenant_id,
                BillingRule.society_id == society_id,
            )
            .order_by(BillingRule.name)
        )
    )


def get_billing_rule_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    billing_rule_id: uuid.UUID,
) -> BillingRule:
    rule = session.scalar(
        select(BillingRule).where(
            BillingRule.id == billing_rule_id,
            BillingRule.tenant_id == tenant_context.tenant_id,
            BillingRule.society_id == society_id,
        )
    )
    if rule is None:
        raise BillingRuleNotFoundError("Billing rule not found.")
    return rule


def create_billing_rule(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: BillingRuleCreate,
    actor: User,
) -> BillingRule:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    ensure_billing_rule_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    ensure_references_valid(session, tenant_context=tenant_context, society_id=society_id, payload=payload)
    rule = BillingRule(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        charge_type_id=payload.charge_type_id,
        building_id=payload.building_id,
        wing_id=payload.wing_id,
        flat_type_id=payload.flat_type_id,
        name=payload.name,
        calculation_method=payload.calculation_method,
        amount=payload.amount,
        area_basis=payload.area_basis,
        frequency=payload.frequency,
        generation_day=payload.generation_day,
        due_day=payload.due_day,
        billing_period_timing=payload.billing_period_timing,
        next_generation_date=payload.next_generation_date,
        scope_type=payload.scope_type,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        description=payload.description,
        status="active",
    )
    session.add(rule)
    session.flush()
    replace_billing_rule_late_fee_rules(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        rule=rule,
        late_fee_rule_ids=payload.late_fee_rule_ids,
    )
    record_audit_log(
        session,
        action="billing_rule.created",
        entity_type="BillingRule",
        entity_id=rule.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Billing rule created: {rule.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(rule)
    return rule


def update_billing_rule(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    billing_rule_id: uuid.UUID,
    payload: BillingRuleUpdate,
    actor: User,
) -> BillingRule:
    rule = get_billing_rule_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        billing_rule_id=billing_rule_id,
    )
    ensure_billing_rule_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        existing_rule_id=rule.id,
    )
    ensure_references_valid(session, tenant_context=tenant_context, society_id=society_id, payload=payload)
    rule.charge_type_id = payload.charge_type_id
    rule.building_id = payload.building_id
    rule.wing_id = payload.wing_id
    rule.flat_type_id = payload.flat_type_id
    rule.name = payload.name
    rule.calculation_method = payload.calculation_method
    rule.amount = payload.amount
    rule.area_basis = payload.area_basis
    rule.frequency = payload.frequency
    rule.generation_day = payload.generation_day
    rule.due_day = payload.due_day
    rule.billing_period_timing = payload.billing_period_timing
    rule.next_generation_date = payload.next_generation_date
    rule.scope_type = payload.scope_type
    rule.effective_from = payload.effective_from
    rule.effective_to = payload.effective_to
    rule.description = payload.description
    replace_billing_rule_late_fee_rules(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        rule=rule,
        late_fee_rule_ids=payload.late_fee_rule_ids,
    )
    record_audit_log(
        session,
        action="billing_rule.updated",
        entity_type="BillingRule",
        entity_id=rule.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Billing rule updated: {rule.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(rule)
    return rule


def change_billing_rule_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    billing_rule_id: uuid.UUID,
    status: str,
    actor: User,
) -> BillingRule:
    rule = get_billing_rule_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        billing_rule_id=billing_rule_id,
    )
    rule.status = status
    record_audit_log(
        session,
        action="billing_rule.inactivated" if status == "inactive" else "billing_rule.activated",
        entity_type="BillingRule",
        entity_id=rule.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Billing rule {status}: {rule.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(rule)
    return rule
