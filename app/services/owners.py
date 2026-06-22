import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Owner, Society, User
from app.schemas.owner import OwnerCreate, OwnerUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class OwnerAlreadyExistsError(Exception):
    pass


class OwnerNotFoundError(Exception):
    pass


class OwnerSocietyNotFoundError(Exception):
    pass


class OwnerUserNotFoundError(Exception):
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
        raise OwnerSocietyNotFoundError("Society not found.")


def ensure_user_exists(
    session: Session,
    *,
    user_id: uuid.UUID | None,
) -> None:
    if user_id is None:
        return

    user = session.scalar(select(User).where(User.id == user_id, User.status == "active"))
    if user is None:
        raise OwnerUserNotFoundError("User not found.")


def ensure_owner_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: OwnerCreate | OwnerUpdate,
    existing_owner_id: uuid.UUID | None = None,
) -> None:
    if payload.user_id is None:
        return

    statement = select(Owner).where(
        Owner.tenant_id == tenant_context.tenant_id,
        Owner.society_id == society_id,
        Owner.user_id == payload.user_id,
    )
    if existing_owner_id is not None:
        statement = statement.where(Owner.id != existing_owner_id)

    if session.scalar(statement) is not None:
        raise OwnerAlreadyExistsError("Owner user already exists in this society.")


def list_owners(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[Owner]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(Owner)
            .where(
                Owner.tenant_id == tenant_context.tenant_id,
                Owner.society_id == society_id,
            )
            .order_by(Owner.full_name)
        )
    )


def get_owner_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> Owner:
    owner = session.scalar(
        select(Owner).where(
            Owner.id == owner_id,
            Owner.tenant_id == tenant_context.tenant_id,
            Owner.society_id == society_id,
        )
    )
    if owner is None:
        raise OwnerNotFoundError("Owner not found.")
    return owner


def create_owner(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: OwnerCreate,
    actor: User,
) -> Owner:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    ensure_user_exists(session, user_id=payload.user_id)
    ensure_owner_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
    )

    owner = Owner(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        user_id=payload.user_id,
        owner_type=payload.owner_type,
        full_name=payload.full_name,
        email=str(payload.email) if payload.email else None,
        mobile_number=payload.mobile_number,
        tax_identifier=payload.tax_identifier,
        billing_address=payload.billing_address,
        status="active",
    )
    session.add(owner)
    session.flush()

    record_audit_log(
        session,
        action="owner.created",
        entity_type="Owner",
        entity_id=owner.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Owner created: {owner.full_name}",
        metadata={
            "society_id": str(society_id),
            "user_id": str(owner.user_id) if owner.user_id else None,
            "owner_type": owner.owner_type,
        },
    )
    session.commit()
    session.refresh(owner)
    return owner


def update_owner(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    owner_id: uuid.UUID,
    payload: OwnerUpdate,
    actor: User,
) -> Owner:
    owner = get_owner_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        owner_id=owner_id,
    )
    ensure_user_exists(session, user_id=payload.user_id)
    ensure_owner_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        payload=payload,
        existing_owner_id=owner.id,
    )

    previous_values = {
        "user_id": str(owner.user_id) if owner.user_id else None,
        "owner_type": owner.owner_type,
        "full_name": owner.full_name,
        "email": owner.email,
        "mobile_number": owner.mobile_number,
        "tax_identifier": owner.tax_identifier,
    }
    owner.user_id = payload.user_id
    owner.owner_type = payload.owner_type
    owner.full_name = payload.full_name
    owner.email = str(payload.email) if payload.email else None
    owner.mobile_number = payload.mobile_number
    owner.tax_identifier = payload.tax_identifier
    owner.billing_address = payload.billing_address

    record_audit_log(
        session,
        action="owner.updated",
        entity_type="Owner",
        entity_id=owner.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Owner updated: {owner.full_name}",
        metadata={
            "society_id": str(society_id),
            "previous": previous_values,
            "current": {
                "user_id": str(owner.user_id) if owner.user_id else None,
                "owner_type": owner.owner_type,
                "full_name": owner.full_name,
                "email": owner.email,
                "mobile_number": owner.mobile_number,
                "tax_identifier": owner.tax_identifier,
            },
        },
    )
    session.commit()
    session.refresh(owner)
    return owner


def change_owner_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    owner_id: uuid.UUID,
    status: str,
    actor: User,
) -> Owner:
    owner = get_owner_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        owner_id=owner_id,
    )
    previous_status = owner.status
    owner.status = status

    action = "owner.inactivated" if status == "inactive" else "owner.activated"
    record_audit_log(
        session,
        action=action,
        entity_type="Owner",
        entity_id=owner.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Owner {status}: {owner.full_name}",
        metadata={
            "society_id": str(society_id),
            "previous_status": previous_status,
            "current_status": status,
        },
    )
    session.commit()
    session.refresh(owner)
    return owner
