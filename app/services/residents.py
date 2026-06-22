import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Flat, Owner, Resident, User
from app.schemas.resident import ResidentCreate, ResidentUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class ResidentAlreadyExistsError(Exception):
    pass


class ResidentFlatNotFoundError(Exception):
    pass


class ResidentInvalidDateError(Exception):
    pass


class ResidentNotFoundError(Exception):
    pass


class ResidentOwnerNotFoundError(Exception):
    pass


class ResidentUserNotFoundError(Exception):
    pass


def ensure_flat_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
) -> None:
    flat = session.scalar(
        select(Flat).where(
            Flat.id == flat_id,
            Flat.tenant_id == tenant_context.tenant_id,
            Flat.society_id == society_id,
            Flat.building_id == building_id,
        )
    )
    if flat is None:
        raise ResidentFlatNotFoundError("Flat not found.")


def ensure_owner_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    owner_id: uuid.UUID | None,
) -> None:
    if owner_id is None:
        return

    owner = session.scalar(
        select(Owner).where(
            Owner.id == owner_id,
            Owner.tenant_id == tenant_context.tenant_id,
            Owner.society_id == society_id,
        )
    )
    if owner is None:
        raise ResidentOwnerNotFoundError("Owner not found.")


def ensure_user_exists(session: Session, *, user_id: uuid.UUID | None) -> None:
    if user_id is None:
        return

    user = session.scalar(select(User).where(User.id == user_id, User.status == "active"))
    if user is None:
        raise ResidentUserNotFoundError("User not found.")


def ensure_current_user_resident_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: ResidentCreate | ResidentUpdate,
    existing_resident_id: uuid.UUID | None = None,
) -> None:
    if payload.user_id is None or payload.move_out_date is not None:
        return

    statement = select(Resident).where(
        Resident.tenant_id == tenant_context.tenant_id,
        Resident.society_id == society_id,
        Resident.flat_id == flat_id,
        Resident.user_id == payload.user_id,
        Resident.move_out_date.is_(None),
    )
    if existing_resident_id is not None:
        statement = statement.where(Resident.id != existing_resident_id)

    if session.scalar(statement) is not None:
        raise ResidentAlreadyExistsError("Current resident user already exists for this flat.")


def list_residents(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
) -> list[Resident]:
    ensure_flat_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
    )
    return list(
        session.scalars(
            select(Resident)
            .where(
                Resident.tenant_id == tenant_context.tenant_id,
                Resident.society_id == society_id,
                Resident.flat_id == flat_id,
            )
            .order_by(Resident.move_in_date.desc(), Resident.created_at.desc())
        )
    )


def get_resident_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    resident_id: uuid.UUID,
) -> Resident:
    resident = session.scalar(
        select(Resident).where(
            Resident.id == resident_id,
            Resident.tenant_id == tenant_context.tenant_id,
            Resident.society_id == society_id,
            Resident.flat_id == flat_id,
        )
    )
    if resident is None:
        raise ResidentNotFoundError("Resident not found.")
    return resident


def create_resident(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: ResidentCreate,
    actor: User,
) -> Resident:
    ensure_flat_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
    )
    ensure_owner_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        owner_id=payload.owner_id,
    )
    ensure_user_exists(session, user_id=payload.user_id)
    ensure_current_user_resident_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        payload=payload,
    )

    resident = Resident(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        owner_id=payload.owner_id,
        user_id=payload.user_id,
        resident_type=payload.resident_type,
        full_name=payload.full_name,
        email=str(payload.email) if payload.email else None,
        mobile_number=payload.mobile_number,
        move_in_date=payload.move_in_date,
        move_out_date=payload.move_out_date,
        status="inactive" if payload.move_out_date else "active",
    )
    session.add(resident)
    session.flush()

    record_audit_log(
        session,
        action="resident.created",
        entity_type="Resident",
        entity_id=resident.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Resident created: {resident.full_name}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "resident_type": resident.resident_type,
        },
    )
    session.commit()
    session.refresh(resident)
    return resident


def update_resident(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    resident_id: uuid.UUID,
    payload: ResidentUpdate,
    actor: User,
) -> Resident:
    resident = get_resident_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        resident_id=resident_id,
    )
    ensure_owner_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        owner_id=payload.owner_id,
    )
    ensure_user_exists(session, user_id=payload.user_id)
    ensure_current_user_resident_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        payload=payload,
        existing_resident_id=resident.id,
    )

    previous_values = {
        "owner_id": str(resident.owner_id) if resident.owner_id else None,
        "user_id": str(resident.user_id) if resident.user_id else None,
        "resident_type": resident.resident_type,
        "full_name": resident.full_name,
        "email": resident.email,
        "mobile_number": resident.mobile_number,
        "move_in_date": resident.move_in_date.isoformat(),
        "move_out_date": resident.move_out_date.isoformat() if resident.move_out_date else None,
    }
    resident.owner_id = payload.owner_id
    resident.user_id = payload.user_id
    resident.resident_type = payload.resident_type
    resident.full_name = payload.full_name
    resident.email = str(payload.email) if payload.email else None
    resident.mobile_number = payload.mobile_number
    resident.move_in_date = payload.move_in_date
    resident.move_out_date = payload.move_out_date
    resident.status = "inactive" if payload.move_out_date else "active"

    record_audit_log(
        session,
        action="resident.updated",
        entity_type="Resident",
        entity_id=resident.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Resident updated: {resident.full_name}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "previous": previous_values,
            "current": {
                "owner_id": str(resident.owner_id) if resident.owner_id else None,
                "user_id": str(resident.user_id) if resident.user_id else None,
                "resident_type": resident.resident_type,
                "full_name": resident.full_name,
                "email": resident.email,
                "mobile_number": resident.mobile_number,
                "move_in_date": resident.move_in_date.isoformat(),
                "move_out_date": (
                    resident.move_out_date.isoformat() if resident.move_out_date else None
                ),
            },
        },
    )
    session.commit()
    session.refresh(resident)
    return resident


def move_out_resident(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    resident_id: uuid.UUID,
    move_out_date: date,
    actor: User,
) -> Resident:
    resident = get_resident_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        resident_id=resident_id,
    )
    if move_out_date < resident.move_in_date:
        raise ResidentInvalidDateError("move_out_date must be on or after move_in_date.")

    previous_status = resident.status
    previous_move_out_date = resident.move_out_date
    resident.move_out_date = move_out_date
    resident.status = "inactive"

    record_audit_log(
        session,
        action="resident.moved_out",
        entity_type="Resident",
        entity_id=resident.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Resident moved out: {resident.full_name}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "previous_status": previous_status,
            "current_status": resident.status,
            "previous_move_out_date": (
                previous_move_out_date.isoformat() if previous_move_out_date else None
            ),
            "current_move_out_date": resident.move_out_date.isoformat(),
        },
    )
    session.commit()
    session.refresh(resident)
    return resident


def activate_resident(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    resident_id: uuid.UUID,
    actor: User,
) -> Resident:
    resident = get_resident_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        resident_id=resident_id,
    )

    payload = ResidentUpdate(
        owner_id=resident.owner_id,
        user_id=resident.user_id,
        resident_type=resident.resident_type,
        full_name=resident.full_name,
        email=resident.email,
        mobile_number=resident.mobile_number,
        move_in_date=resident.move_in_date,
        move_out_date=None,
    )
    ensure_current_user_resident_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        payload=payload,
        existing_resident_id=resident.id,
    )

    previous_status = resident.status
    previous_move_out_date = resident.move_out_date
    resident.move_out_date = None
    resident.status = "active"

    record_audit_log(
        session,
        action="resident.activated",
        entity_type="Resident",
        entity_id=resident.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Resident activated: {resident.full_name}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "previous_status": previous_status,
            "current_status": resident.status,
            "previous_move_out_date": (
                previous_move_out_date.isoformat() if previous_move_out_date else None
            ),
            "current_move_out_date": None,
        },
    )
    session.commit()
    session.refresh(resident)
    return resident
