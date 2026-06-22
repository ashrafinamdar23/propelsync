import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChargeType, ChartOfAccount, Society, User
from app.schemas.charge_type import ChargeTypeCreate, ChargeTypeUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class ChargeTypeAlreadyExistsError(Exception):
    pass


class ChargeTypeNotFoundError(Exception):
    pass


class ChargeTypeSocietyNotFoundError(Exception):
    pass


class ChargeTypeRevenueAccountInvalidError(Exception):
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
        raise ChargeTypeSocietyNotFoundError("Society not found.")


def ensure_charge_type_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ChargeTypeCreate | ChargeTypeUpdate,
    existing_charge_type_id: uuid.UUID | None = None,
) -> None:
    statement = select(ChargeType).where(
        ChargeType.tenant_id == tenant_context.tenant_id,
        ChargeType.society_id == society_id,
        ChargeType.name == payload.name,
    )
    if existing_charge_type_id is not None:
        statement = statement.where(ChargeType.id != existing_charge_type_id)
    if session.scalar(statement) is not None:
        raise ChargeTypeAlreadyExistsError("Charge type name already exists.")

    if payload.code is None:
        return

    statement = select(ChargeType).where(
        ChargeType.tenant_id == tenant_context.tenant_id,
        ChargeType.society_id == society_id,
        ChargeType.code == payload.code,
    )
    if existing_charge_type_id is not None:
        statement = statement.where(ChargeType.id != existing_charge_type_id)
    if session.scalar(statement) is not None:
        raise ChargeTypeAlreadyExistsError("Charge type code already exists.")


def ensure_revenue_account_valid(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    revenue_account_id: uuid.UUID,
) -> None:
    account = session.scalar(
        select(ChartOfAccount).where(
            ChartOfAccount.id == revenue_account_id,
            ChartOfAccount.tenant_id == tenant_context.tenant_id,
            ChartOfAccount.society_id == society_id,
            ChartOfAccount.account_type == "income",
            ChartOfAccount.status == "active",
        )
    )
    if account is None:
        raise ChargeTypeRevenueAccountInvalidError("Revenue account must be an active income account.")


def list_charge_types(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[ChargeType]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(ChargeType)
            .where(
                ChargeType.tenant_id == tenant_context.tenant_id,
                ChargeType.society_id == society_id,
            )
            .order_by(ChargeType.name)
        )
    )


def get_charge_type_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    charge_type_id: uuid.UUID,
) -> ChargeType:
    charge_type = session.scalar(
        select(ChargeType).where(
            ChargeType.id == charge_type_id,
            ChargeType.tenant_id == tenant_context.tenant_id,
            ChargeType.society_id == society_id,
        )
    )
    if charge_type is None:
        raise ChargeTypeNotFoundError("Charge type not found.")
    return charge_type


def create_charge_type(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: ChargeTypeCreate,
    actor: User,
) -> ChargeType:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    ensure_charge_type_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    ensure_revenue_account_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        revenue_account_id=payload.revenue_account_id,
    )
    charge_type = ChargeType(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        revenue_account_id=payload.revenue_account_id,
        status="active",
    )
    session.add(charge_type)
    session.flush()
    record_audit_log(
        session,
        action="charge_type.created",
        entity_type="ChargeType",
        entity_id=charge_type.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Charge type created: {charge_type.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(charge_type)
    return charge_type


def update_charge_type(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    charge_type_id: uuid.UUID,
    payload: ChargeTypeUpdate,
    actor: User,
) -> ChargeType:
    charge_type = get_charge_type_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        charge_type_id=charge_type_id,
    )
    ensure_charge_type_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        existing_charge_type_id=charge_type.id,
    )
    ensure_revenue_account_valid(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        revenue_account_id=payload.revenue_account_id,
    )
    charge_type.name = payload.name
    charge_type.code = payload.code
    charge_type.description = payload.description
    charge_type.revenue_account_id = payload.revenue_account_id
    record_audit_log(
        session,
        action="charge_type.updated",
        entity_type="ChargeType",
        entity_id=charge_type.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Charge type updated: {charge_type.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(charge_type)
    return charge_type


def change_charge_type_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    charge_type_id: uuid.UUID,
    status: str,
    actor: User,
) -> ChargeType:
    charge_type = get_charge_type_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        charge_type_id=charge_type_id,
    )
    charge_type.status = status
    record_audit_log(
        session,
        action="charge_type.inactivated" if status == "inactive" else "charge_type.activated",
        entity_type="ChargeType",
        entity_id=charge_type.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Charge type {status}: {charge_type.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(charge_type)
    return charge_type
