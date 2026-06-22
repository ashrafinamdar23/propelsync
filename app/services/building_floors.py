import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Building, BuildingFloor, User
from app.schemas.building_floor import BuildingFloorCreate, BuildingFloorUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class BuildingFloorAlreadyExistsError(Exception):
    pass


class BuildingFloorNotFoundError(Exception):
    pass


class BuildingFloorBuildingNotFoundError(Exception):
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
        raise BuildingFloorBuildingNotFoundError("Building not found.")


def ensure_floor_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: BuildingFloorCreate | BuildingFloorUpdate,
    existing_floor_id: uuid.UUID | None = None,
) -> None:
    duplicate_messages = {
        "floor_label": f"Floor label '{payload.floor_label}' already exists for this building.",
        "floor_number": f"Floor sort number {payload.floor_number} already exists for this building.",
    }
    for field, value in (("floor_label", payload.floor_label), ("floor_number", payload.floor_number)):
        statement = select(BuildingFloor).where(
            BuildingFloor.tenant_id == tenant_context.tenant_id,
            BuildingFloor.society_id == society_id,
            BuildingFloor.building_id == building_id,
            getattr(BuildingFloor, field) == value,
        )
        if existing_floor_id is not None:
            statement = statement.where(BuildingFloor.id != existing_floor_id)
        if session.scalar(statement) is not None:
            raise BuildingFloorAlreadyExistsError(duplicate_messages[field])


def list_building_floors(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
) -> list[BuildingFloor]:
    ensure_building_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    return list(
        session.scalars(
            select(BuildingFloor)
            .where(
                BuildingFloor.tenant_id == tenant_context.tenant_id,
                BuildingFloor.society_id == society_id,
                BuildingFloor.building_id == building_id,
            )
            .order_by(BuildingFloor.floor_number)
        )
    )


def get_building_floor_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
) -> BuildingFloor:
    floor = session.scalar(
        select(BuildingFloor).where(
            BuildingFloor.id == floor_id,
            BuildingFloor.tenant_id == tenant_context.tenant_id,
            BuildingFloor.society_id == society_id,
            BuildingFloor.building_id == building_id,
        )
    )
    if floor is None:
        raise BuildingFloorNotFoundError("Building floor not found.")
    return floor


def create_building_floor(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: BuildingFloorCreate,
    actor: User,
) -> BuildingFloor:
    ensure_building_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    ensure_floor_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
    )
    floor = BuildingFloor(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        building_id=building_id,
        floor_label=payload.floor_label,
        floor_number=payload.floor_number,
        status="active",
    )
    session.add(floor)
    session.flush()
    record_audit_log(
        session,
        action="building_floor.created",
        entity_type="BuildingFloor",
        entity_id=floor.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Building floor created: {floor.floor_label}",
        metadata={"society_id": str(society_id), "building_id": str(building_id)},
    )
    session.commit()
    session.refresh(floor)
    return floor


def update_building_floor(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    payload: BuildingFloorUpdate,
    actor: User,
) -> BuildingFloor:
    floor = get_building_floor_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        floor_id=floor_id,
    )
    ensure_floor_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
        existing_floor_id=floor.id,
    )
    floor.floor_label = payload.floor_label
    floor.floor_number = payload.floor_number
    record_audit_log(
        session,
        action="building_floor.updated",
        entity_type="BuildingFloor",
        entity_id=floor.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Building floor updated: {floor.floor_label}",
        metadata={"society_id": str(society_id), "building_id": str(building_id)},
    )
    session.commit()
    session.refresh(floor)
    return floor


def change_building_floor_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    status: str,
    actor: User,
) -> BuildingFloor:
    floor = get_building_floor_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        floor_id=floor_id,
    )
    floor.status = status
    record_audit_log(
        session,
        action="building_floor.inactivated" if status == "inactive" else "building_floor.activated",
        entity_type="BuildingFloor",
        entity_id=floor.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Building floor {status}: {floor.floor_label}",
        metadata={"society_id": str(society_id), "building_id": str(building_id)},
    )
    session.commit()
    session.refresh(floor)
    return floor
