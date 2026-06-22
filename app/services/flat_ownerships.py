import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Flat, FlatOwnership, Owner, User
from app.schemas.flat_ownership import FlatOwnershipCreate, FlatOwnershipUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class FlatOwnershipAlreadyExistsError(Exception):
    pass


class FlatOwnershipCurrentPrimaryExistsError(Exception):
    pass


class FlatOwnershipFlatNotFoundError(Exception):
    pass


class FlatOwnershipNotFoundError(Exception):
    pass


class FlatOwnershipOwnerNotFoundError(Exception):
    pass


class FlatOwnershipInvalidDateError(Exception):
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
        raise FlatOwnershipFlatNotFoundError("Flat not found.")


def ensure_owner_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> None:
    owner = session.scalar(
        select(Owner).where(
            Owner.id == owner_id,
            Owner.tenant_id == tenant_context.tenant_id,
            Owner.society_id == society_id,
        )
    )
    if owner is None:
        raise FlatOwnershipOwnerNotFoundError("Owner not found.")


def ensure_ownership_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: FlatOwnershipCreate | FlatOwnershipUpdate,
    existing_ownership_id: uuid.UUID | None = None,
) -> None:
    statement = select(FlatOwnership).where(
        FlatOwnership.tenant_id == tenant_context.tenant_id,
        FlatOwnership.society_id == society_id,
        FlatOwnership.flat_id == flat_id,
        FlatOwnership.owner_id == payload.owner_id,
        FlatOwnership.effective_from == payload.effective_from,
    )
    if existing_ownership_id is not None:
        statement = statement.where(FlatOwnership.id != existing_ownership_id)

    if session.scalar(statement) is not None:
        raise FlatOwnershipAlreadyExistsError("Flat ownership already exists.")


def ensure_current_primary_available(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: FlatOwnershipCreate | FlatOwnershipUpdate,
    existing_ownership_id: uuid.UUID | None = None,
) -> None:
    if payload.ownership_type != "primary_owner" or payload.effective_to is not None:
        return

    statement = select(FlatOwnership).where(
        FlatOwnership.tenant_id == tenant_context.tenant_id,
        FlatOwnership.society_id == society_id,
        FlatOwnership.flat_id == flat_id,
        FlatOwnership.ownership_type == "primary_owner",
        FlatOwnership.effective_to.is_(None),
        FlatOwnership.status == "active",
    )
    if existing_ownership_id is not None:
        statement = statement.where(FlatOwnership.id != existing_ownership_id)

    if session.scalar(statement) is not None:
        raise FlatOwnershipCurrentPrimaryExistsError("Current primary owner already exists.")


def list_flat_ownerships(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
) -> list[FlatOwnership]:
    ensure_flat_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
    )
    return list(
        session.scalars(
            select(FlatOwnership)
            .where(
                FlatOwnership.tenant_id == tenant_context.tenant_id,
                FlatOwnership.society_id == society_id,
                FlatOwnership.flat_id == flat_id,
            )
            .order_by(FlatOwnership.effective_from.desc(), FlatOwnership.created_at.desc())
        )
    )


def get_flat_ownership_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    ownership_id: uuid.UUID,
) -> FlatOwnership:
    ownership = session.scalar(
        select(FlatOwnership).where(
            FlatOwnership.id == ownership_id,
            FlatOwnership.tenant_id == tenant_context.tenant_id,
            FlatOwnership.society_id == society_id,
            FlatOwnership.flat_id == flat_id,
        )
    )
    if ownership is None:
        raise FlatOwnershipNotFoundError("Flat ownership not found.")
    return ownership


def create_flat_ownership(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: FlatOwnershipCreate,
    actor: User,
) -> FlatOwnership:
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
    ensure_ownership_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        payload=payload,
    )
    ensure_current_primary_available(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        payload=payload,
    )

    ownership = FlatOwnership(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        owner_id=payload.owner_id,
        ownership_type=payload.ownership_type,
        ownership_percentage=payload.ownership_percentage,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        status="active",
    )
    session.add(ownership)
    session.flush()

    record_audit_log(
        session,
        action="flat_ownership.created",
        entity_type="FlatOwnership",
        entity_id=ownership.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat ownership created: {ownership.ownership_type}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "owner_id": str(ownership.owner_id),
        },
    )
    session.commit()
    session.refresh(ownership)
    return ownership


def update_flat_ownership(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    ownership_id: uuid.UUID,
    payload: FlatOwnershipUpdate,
    actor: User,
) -> FlatOwnership:
    ownership = get_flat_ownership_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        ownership_id=ownership_id,
    )
    ensure_owner_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        owner_id=payload.owner_id,
    )
    ensure_ownership_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        payload=payload,
        existing_ownership_id=ownership.id,
    )
    ensure_current_primary_available(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        payload=payload,
        existing_ownership_id=ownership.id,
    )

    previous_values = {
        "owner_id": str(ownership.owner_id),
        "ownership_type": ownership.ownership_type,
        "ownership_percentage": (
            str(ownership.ownership_percentage) if ownership.ownership_percentage else None
        ),
        "effective_from": ownership.effective_from.isoformat(),
        "effective_to": ownership.effective_to.isoformat() if ownership.effective_to else None,
    }
    ownership.owner_id = payload.owner_id
    ownership.ownership_type = payload.ownership_type
    ownership.ownership_percentage = payload.ownership_percentage
    ownership.effective_from = payload.effective_from
    ownership.effective_to = payload.effective_to

    record_audit_log(
        session,
        action="flat_ownership.updated",
        entity_type="FlatOwnership",
        entity_id=ownership.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat ownership updated: {ownership.ownership_type}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "previous": previous_values,
            "current": {
                "owner_id": str(ownership.owner_id),
                "ownership_type": ownership.ownership_type,
                "ownership_percentage": (
                    str(ownership.ownership_percentage) if ownership.ownership_percentage else None
                ),
                "effective_from": ownership.effective_from.isoformat(),
                "effective_to": ownership.effective_to.isoformat() if ownership.effective_to else None,
            },
        },
    )
    session.commit()
    session.refresh(ownership)
    return ownership


def close_flat_ownership(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    ownership_id: uuid.UUID,
    effective_to: date,
    actor: User,
) -> FlatOwnership:
    ownership = get_flat_ownership_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        ownership_id=ownership_id,
    )
    if effective_to < ownership.effective_from:
        raise FlatOwnershipInvalidDateError("effective_to must be on or after effective_from.")

    previous_status = ownership.status
    previous_effective_to = ownership.effective_to
    ownership.effective_to = effective_to
    ownership.status = "inactive"

    record_audit_log(
        session,
        action="flat_ownership.closed",
        entity_type="FlatOwnership",
        entity_id=ownership.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat ownership closed: {ownership.ownership_type}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "previous_status": previous_status,
            "current_status": ownership.status,
            "previous_effective_to": (
                previous_effective_to.isoformat() if previous_effective_to else None
            ),
            "current_effective_to": ownership.effective_to.isoformat(),
        },
    )
    session.commit()
    session.refresh(ownership)
    return ownership


def activate_flat_ownership(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    ownership_id: uuid.UUID,
    actor: User,
) -> FlatOwnership:
    ownership = get_flat_ownership_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        ownership_id=ownership_id,
    )

    payload = FlatOwnershipUpdate(
        owner_id=ownership.owner_id,
        ownership_type=ownership.ownership_type,
        ownership_percentage=ownership.ownership_percentage,
        effective_from=ownership.effective_from,
        effective_to=None,
    )
    ensure_current_primary_available(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        payload=payload,
        existing_ownership_id=ownership.id,
    )

    previous_status = ownership.status
    previous_effective_to = ownership.effective_to
    ownership.effective_to = None
    ownership.status = "active"

    record_audit_log(
        session,
        action="flat_ownership.activated",
        entity_type="FlatOwnership",
        entity_id=ownership.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Flat ownership activated: {ownership.ownership_type}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "previous_status": previous_status,
            "current_status": ownership.status,
            "previous_effective_to": (
                previous_effective_to.isoformat() if previous_effective_to else None
            ),
            "current_effective_to": None,
        },
    )
    session.commit()
    session.refresh(ownership)
    return ownership
