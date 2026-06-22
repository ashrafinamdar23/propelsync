import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Building, User, Wing
from app.schemas.wing import WingCreate, WingUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class WingAlreadyExistsError(Exception):
    pass


class WingNotFoundError(Exception):
    pass


class WingBuildingNotFoundError(Exception):
    pass


def ensure_building_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
) -> None:
    building = session.scalar(
        select(Building).where(
            Building.id == building_id,
            Building.tenant_id == tenant_context.tenant_id,
            Building.society_id == society_id,
        )
    )
    if building is None:
        raise WingBuildingNotFoundError("Building not found.")


def list_wings(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
) -> list[Wing]:
    ensure_building_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    return list(
        session.scalars(
            select(Wing)
            .where(
                Wing.tenant_id == tenant_context.tenant_id,
                Wing.society_id == society_id,
                Wing.building_id == building_id,
            )
            .order_by(Wing.name)
        )
    )


def get_wing_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    wing_id: uuid.UUID,
) -> Wing:
    wing = session.scalar(
        select(Wing).where(
            Wing.id == wing_id,
            Wing.tenant_id == tenant_context.tenant_id,
            Wing.society_id == society_id,
            Wing.building_id == building_id,
        )
    )
    if wing is None:
        raise WingNotFoundError("Wing not found.")
    return wing


def ensure_wing_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: WingCreate | WingUpdate,
    existing_wing_id: uuid.UUID | None = None,
) -> None:
    filters = [Wing.name == payload.name]
    if payload.code:
        filters.append(Wing.code == payload.code)

    statement = select(Wing).where(
        Wing.tenant_id == tenant_context.tenant_id,
        Wing.society_id == society_id,
        Wing.building_id == building_id,
        or_(*filters),
    )
    if existing_wing_id is not None:
        statement = statement.where(Wing.id != existing_wing_id)

    if session.scalar(statement) is not None:
        raise WingAlreadyExistsError("Wing name or code already exists.")


def create_wing(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: WingCreate,
    actor: User,
) -> Wing:
    ensure_building_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    ensure_wing_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
    )

    wing = Wing(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        building_id=building_id,
        name=payload.name,
        code=payload.code,
        status="active",
    )
    session.add(wing)
    session.flush()

    record_audit_log(
        session,
        action="wing.created",
        entity_type="Wing",
        entity_id=wing.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Wing created: {wing.name}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "code": wing.code,
        },
    )
    session.commit()
    session.refresh(wing)
    return wing


def update_wing(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    wing_id: uuid.UUID,
    payload: WingUpdate,
    actor: User,
) -> Wing:
    wing = get_wing_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        wing_id=wing_id,
    )
    ensure_wing_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
        existing_wing_id=wing.id,
    )

    previous_values = {
        "name": wing.name,
        "code": wing.code,
    }
    wing.name = payload.name
    wing.code = payload.code

    record_audit_log(
        session,
        action="wing.updated",
        entity_type="Wing",
        entity_id=wing.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Wing updated: {wing.name}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "previous": previous_values,
            "current": {
                "name": wing.name,
                "code": wing.code,
            },
        },
    )
    session.commit()
    session.refresh(wing)
    return wing


def change_wing_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    wing_id: uuid.UUID,
    status: str,
    actor: User,
) -> Wing:
    wing = get_wing_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        wing_id=wing_id,
    )
    previous_status = wing.status
    wing.status = status

    action = "wing.suspended" if status == "suspended" else "wing.activated"
    record_audit_log(
        session,
        action=action,
        entity_type="Wing",
        entity_id=wing.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Wing {status}: {wing.name}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "previous_status": previous_status,
            "current_status": status,
        },
    )
    session.commit()
    session.refresh(wing)
    return wing
