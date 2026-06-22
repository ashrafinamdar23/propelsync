import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Building, User
from app.schemas.building import BuildingCreate, BuildingUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class BuildingAlreadyExistsError(Exception):
    pass


class BuildingNotFoundError(Exception):
    pass


def list_buildings(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[Building]:
    return list(
        session.scalars(
            select(Building)
            .where(
                Building.tenant_id == tenant_context.tenant_id,
                Building.society_id == society_id,
            )
            .order_by(Building.name)
        )
    )


def get_building_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
) -> Building:
    building = session.scalar(
        select(Building).where(
            Building.id == building_id,
            Building.tenant_id == tenant_context.tenant_id,
            Building.society_id == society_id,
        )
    )
    if building is None:
        raise BuildingNotFoundError("Building not found.")
    return building


def ensure_building_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: BuildingCreate | BuildingUpdate,
    existing_building_id: uuid.UUID | None = None,
) -> None:
    filters = [Building.name == payload.name]
    if payload.code:
        filters.append(Building.code == payload.code)

    statement = select(Building).where(
        Building.tenant_id == tenant_context.tenant_id,
        Building.society_id == society_id,
        or_(*filters),
    )
    if existing_building_id is not None:
        statement = statement.where(Building.id != existing_building_id)

    if session.scalar(statement) is not None:
        raise BuildingAlreadyExistsError("Building name or code already exists.")


def create_building(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: BuildingCreate,
    actor: User,
) -> Building:
    ensure_building_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )

    building = Building(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        name=payload.name,
        code=payload.code,
        status="active",
    )
    session.add(building)
    session.flush()

    record_audit_log(
        session,
        action="building.created",
        entity_type="Building",
        entity_id=building.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Building created: {building.name}",
        metadata={
            "society_id": str(society_id),
            "code": building.code,
        },
    )
    session.commit()
    session.refresh(building)
    return building


def update_building(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: BuildingUpdate,
    actor: User,
) -> Building:
    building = get_building_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    ensure_building_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        existing_building_id=building.id,
    )

    previous_values = {
        "name": building.name,
        "code": building.code,
    }
    building.name = payload.name
    building.code = payload.code

    record_audit_log(
        session,
        action="building.updated",
        entity_type="Building",
        entity_id=building.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Building updated: {building.name}",
        metadata={
            "society_id": str(society_id),
            "previous": previous_values,
            "current": {
                "name": building.name,
                "code": building.code,
            },
        },
    )
    session.commit()
    session.refresh(building)
    return building


def change_building_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    status: str,
    actor: User,
) -> Building:
    building = get_building_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    previous_status = building.status
    building.status = status

    action = "building.suspended" if status == "suspended" else "building.activated"
    record_audit_log(
        session,
        action=action,
        entity_type="Building",
        entity_id=building.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Building {status}: {building.name}",
        metadata={
            "society_id": str(society_id),
            "previous_status": previous_status,
            "current_status": status,
        },
    )
    session.commit()
    session.refresh(building)
    return building
