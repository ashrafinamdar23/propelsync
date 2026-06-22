import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Building, BuildingFloor, Flat, FlatType, User, Wing
from app.schemas.flat import FlatCreate, FlatUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class FlatAlreadyExistsError(Exception):
    pass


class FlatNotFoundError(Exception):
    pass


class FlatBuildingNotFoundError(Exception):
    pass


class FlatWingNotFoundError(Exception):
    pass


class FlatFloorNotFoundError(Exception):
    pass


class FlatTypeNotFoundError(Exception):
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
        raise FlatBuildingNotFoundError("Building not found.")


def ensure_wing_belongs_to_building(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    wing_id: uuid.UUID | None,
) -> None:
    if wing_id is None:
        return

    wing = session.scalar(
        select(Wing).where(
            Wing.id == wing_id,
            Wing.tenant_id == tenant_context.tenant_id,
            Wing.society_id == society_id,
            Wing.building_id == building_id,
        )
    )
    if wing is None:
        raise FlatWingNotFoundError("Wing not found.")


def ensure_floor_belongs_to_building(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID | None,
) -> None:
    if floor_id is None:
        return

    floor = session.scalar(
        select(BuildingFloor).where(
            BuildingFloor.id == floor_id,
            BuildingFloor.tenant_id == tenant_context.tenant_id,
            BuildingFloor.society_id == society_id,
            BuildingFloor.building_id == building_id,
        )
    )
    if floor is None:
        raise FlatFloorNotFoundError("Building floor not found.")


def get_flat_type(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_type_id: uuid.UUID | None,
) -> FlatType | None:
    if flat_type_id is None:
        return None

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


def list_flats(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
) -> list[Flat]:
    ensure_building_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    return list(
        session.scalars(
            select(Flat)
            .where(
                Flat.tenant_id == tenant_context.tenant_id,
                Flat.society_id == society_id,
                Flat.building_id == building_id,
            )
            .order_by(Flat.flat_number)
        )
    )


def get_flat_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
) -> Flat:
    flat = session.scalar(
        select(Flat).where(
            Flat.id == flat_id,
            Flat.tenant_id == tenant_context.tenant_id,
            Flat.society_id == society_id,
            Flat.building_id == building_id,
        )
    )
    if flat is None:
        raise FlatNotFoundError("Flat not found.")
    return flat


def ensure_flat_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: FlatCreate | FlatUpdate,
    existing_flat_id: uuid.UUID | None = None,
) -> None:
    statement = select(Flat).where(
        Flat.tenant_id == tenant_context.tenant_id,
        Flat.society_id == society_id,
        Flat.building_id == building_id,
        Flat.wing_id == payload.wing_id,
        Flat.flat_number == payload.flat_number,
    )
    if existing_flat_id is not None:
        statement = statement.where(Flat.id != existing_flat_id)

    if session.scalar(statement) is not None:
        raise FlatAlreadyExistsError("Flat number already exists.")


def create_flat(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: FlatCreate,
    actor: User,
) -> Flat:
    ensure_building_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
    )
    ensure_wing_belongs_to_building(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        wing_id=payload.wing_id,
    )
    ensure_floor_belongs_to_building(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        floor_id=payload.floor_id,
    )
    flat_type = get_flat_type(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_type_id=payload.flat_type_id,
    )
    ensure_flat_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
    )

    flat = Flat(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        building_id=building_id,
        wing_id=payload.wing_id,
        floor_id=payload.floor_id,
        flat_type_id=payload.flat_type_id,
        flat_number=payload.flat_number,
        floor_number=payload.floor_number,
        carpet_area_sqft=payload.carpet_area_sqft
        if payload.carpet_area_sqft is not None
        else flat_type.carpet_area_sqft
        if flat_type
        else None,
        built_up_area_sqft=payload.built_up_area_sqft
        if payload.built_up_area_sqft is not None
        else flat_type.built_up_area_sqft
        if flat_type
        else None,
        parking_count=payload.parking_count
        if payload.parking_count is not None
        else flat_type.default_parking_count
        if flat_type
        else 0,
        status="active",
    )
    session.add(flat)
    session.flush()

    record_audit_log(
        session,
        action="flat.created",
        entity_type="Flat",
        entity_id=flat.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat created: {flat.flat_number}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "wing_id": str(flat.wing_id) if flat.wing_id else None,
            "floor_id": str(flat.floor_id) if flat.floor_id else None,
            "flat_type_id": str(flat.flat_type_id) if flat.flat_type_id else None,
        },
    )
    session.commit()
    session.refresh(flat)
    return flat


def update_flat(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: FlatUpdate,
    actor: User,
) -> Flat:
    flat = get_flat_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
    )
    ensure_wing_belongs_to_building(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        wing_id=payload.wing_id,
    )
    ensure_floor_belongs_to_building(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        floor_id=payload.floor_id,
    )
    flat_type = get_flat_type(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_type_id=payload.flat_type_id,
    )
    ensure_flat_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        payload=payload,
        existing_flat_id=flat.id,
    )

    previous_values = {
        "wing_id": str(flat.wing_id) if flat.wing_id else None,
        "floor_id": str(flat.floor_id) if flat.floor_id else None,
        "flat_type_id": str(flat.flat_type_id) if flat.flat_type_id else None,
        "flat_number": flat.flat_number,
        "floor_number": flat.floor_number,
        "carpet_area_sqft": str(flat.carpet_area_sqft) if flat.carpet_area_sqft else None,
        "built_up_area_sqft": str(flat.built_up_area_sqft) if flat.built_up_area_sqft else None,
        "parking_count": flat.parking_count,
    }
    flat.wing_id = payload.wing_id
    flat.floor_id = payload.floor_id
    flat.flat_type_id = payload.flat_type_id
    flat.flat_number = payload.flat_number
    flat.floor_number = payload.floor_number
    flat.carpet_area_sqft = (
        payload.carpet_area_sqft
        if payload.carpet_area_sqft is not None
        else flat_type.carpet_area_sqft
        if flat_type
        else None
    )
    flat.built_up_area_sqft = (
        payload.built_up_area_sqft
        if payload.built_up_area_sqft is not None
        else flat_type.built_up_area_sqft
        if flat_type
        else None
    )
    flat.parking_count = (
        payload.parking_count
        if payload.parking_count is not None
        else flat_type.default_parking_count
        if flat_type
        else 0
    )

    record_audit_log(
        session,
        action="flat.updated",
        entity_type="Flat",
        entity_id=flat.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat updated: {flat.flat_number}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "previous": previous_values,
            "current": {
                "wing_id": str(flat.wing_id) if flat.wing_id else None,
                "floor_id": str(flat.floor_id) if flat.floor_id else None,
                "flat_type_id": str(flat.flat_type_id) if flat.flat_type_id else None,
                "flat_number": flat.flat_number,
                "floor_number": flat.floor_number,
                "carpet_area_sqft": str(flat.carpet_area_sqft) if flat.carpet_area_sqft else None,
                "built_up_area_sqft": (
                    str(flat.built_up_area_sqft) if flat.built_up_area_sqft else None
                ),
                "parking_count": flat.parking_count,
            },
        },
    )
    session.commit()
    session.refresh(flat)
    return flat


def change_flat_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    status: str,
    actor: User,
) -> Flat:
    flat = get_flat_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
    )
    previous_status = flat.status
    flat.status = status

    action = "flat.inactivated" if status == "inactive" else "flat.activated"
    record_audit_log(
        session,
        action=action,
        entity_type="Flat",
        entity_id=flat.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat {status}: {flat.flat_number}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "previous_status": previous_status,
            "current_status": status,
        },
    )
    session.commit()
    session.refresh(flat)
    return flat
