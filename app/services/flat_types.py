import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FlatType, Society, User
from app.schemas.flat_type import FlatTypeCreate, FlatTypeUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class FlatTypeAlreadyExistsError(Exception):
    pass


class FlatTypeNotFoundError(Exception):
    pass


class FlatTypeSocietyNotFoundError(Exception):
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
        raise FlatTypeSocietyNotFoundError("Society not found.")


def ensure_flat_type_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: FlatTypeCreate | FlatTypeUpdate,
    existing_flat_type_id: uuid.UUID | None = None,
) -> None:
    statement = select(FlatType).where(
        FlatType.tenant_id == tenant_context.tenant_id,
        FlatType.society_id == society_id,
        FlatType.name == payload.name,
    )
    if existing_flat_type_id is not None:
        statement = statement.where(FlatType.id != existing_flat_type_id)
    if session.scalar(statement) is not None:
        raise FlatTypeAlreadyExistsError("Flat type name already exists.")

    if payload.code is None:
        return

    statement = select(FlatType).where(
        FlatType.tenant_id == tenant_context.tenant_id,
        FlatType.society_id == society_id,
        FlatType.code == payload.code,
    )
    if existing_flat_type_id is not None:
        statement = statement.where(FlatType.id != existing_flat_type_id)
    if session.scalar(statement) is not None:
        raise FlatTypeAlreadyExistsError("Flat type code already exists.")


def list_flat_types(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[FlatType]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(FlatType)
            .where(
                FlatType.tenant_id == tenant_context.tenant_id,
                FlatType.society_id == society_id,
            )
            .order_by(FlatType.name)
        )
    )


def get_flat_type_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_type_id: uuid.UUID,
) -> FlatType:
    flat_type = session.scalar(
        select(FlatType).where(
            FlatType.id == flat_type_id,
            FlatType.tenant_id == tenant_context.tenant_id,
            FlatType.society_id == society_id,
        )
    )
    if flat_type is None:
        raise FlatTypeNotFoundError("Flat type not found.")
    return flat_type


def create_flat_type(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: FlatTypeCreate,
    actor: User,
) -> FlatType:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    ensure_flat_type_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )
    flat_type = FlatType(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        name=payload.name,
        code=payload.code,
        unit_category=payload.unit_category,
        bedroom_count=payload.bedroom_count,
        bathroom_count=payload.bathroom_count,
        carpet_area_sqft=payload.carpet_area_sqft,
        built_up_area_sqft=payload.built_up_area_sqft,
        default_parking_count=payload.default_parking_count,
        status="active",
    )
    session.add(flat_type)
    session.flush()
    record_audit_log(
        session,
        action="flat_type.created",
        entity_type="FlatType",
        entity_id=flat_type.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat type created: {flat_type.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(flat_type)
    return flat_type


def update_flat_type(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_type_id: uuid.UUID,
    payload: FlatTypeUpdate,
    actor: User,
) -> FlatType:
    flat_type = get_flat_type_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_type_id=flat_type_id,
    )
    ensure_flat_type_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        existing_flat_type_id=flat_type.id,
    )
    flat_type.name = payload.name
    flat_type.code = payload.code
    flat_type.unit_category = payload.unit_category
    flat_type.bedroom_count = payload.bedroom_count
    flat_type.bathroom_count = payload.bathroom_count
    flat_type.carpet_area_sqft = payload.carpet_area_sqft
    flat_type.built_up_area_sqft = payload.built_up_area_sqft
    flat_type.default_parking_count = payload.default_parking_count
    record_audit_log(
        session,
        action="flat_type.updated",
        entity_type="FlatType",
        entity_id=flat_type.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat type updated: {flat_type.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(flat_type)
    return flat_type


def change_flat_type_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_type_id: uuid.UUID,
    status: str,
    actor: User,
) -> FlatType:
    flat_type = get_flat_type_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_type_id=flat_type_id,
    )
    flat_type.status = status
    record_audit_log(
        session,
        action="flat_type.inactivated" if status == "inactive" else "flat_type.activated",
        entity_type="FlatType",
        entity_id=flat_type.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat type {status}: {flat_type.name}",
        metadata={"society_id": str(society_id)},
    )
    session.commit()
    session.refresh(flat_type)
    return flat_type
