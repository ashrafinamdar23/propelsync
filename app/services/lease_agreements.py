import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Flat, LeaseAgreement, Owner, Resident, User
from app.schemas.lease_agreement import LeaseAgreementCreate, LeaseAgreementUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class LeaseAgreementAlreadyExistsError(Exception):
    pass


class LeaseAgreementFlatNotFoundError(Exception):
    pass


class LeaseAgreementInvalidDateError(Exception):
    pass


class LeaseAgreementNotFoundError(Exception):
    pass


class LeaseAgreementOwnerNotFoundError(Exception):
    pass


class LeaseAgreementResidentNotFoundError(Exception):
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
        raise LeaseAgreementFlatNotFoundError("Flat not found.")


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
        raise LeaseAgreementOwnerNotFoundError("Owner not found.")


def ensure_resident_exists(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    resident_id: uuid.UUID | None,
) -> None:
    if resident_id is None:
        return

    resident = session.scalar(
        select(Resident).where(
            Resident.id == resident_id,
            Resident.tenant_id == tenant_context.tenant_id,
            Resident.society_id == society_id,
            Resident.flat_id == flat_id,
        )
    )
    if resident is None:
        raise LeaseAgreementResidentNotFoundError("Resident not found.")


def ensure_active_lease_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    flat_id: uuid.UUID,
    existing_lease_id: uuid.UUID | None = None,
) -> None:
    statement = select(LeaseAgreement).where(
        LeaseAgreement.tenant_id == tenant_context.tenant_id,
        LeaseAgreement.society_id == society_id,
        LeaseAgreement.flat_id == flat_id,
        LeaseAgreement.status == "active",
    )
    if existing_lease_id is not None:
        statement = statement.where(LeaseAgreement.id != existing_lease_id)
    if session.scalar(statement) is not None:
        raise LeaseAgreementAlreadyExistsError("Active lease already exists for this flat.")


def list_lease_agreements(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
) -> list[LeaseAgreement]:
    ensure_flat_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
    )
    return list(
        session.scalars(
            select(LeaseAgreement)
            .where(
                LeaseAgreement.tenant_id == tenant_context.tenant_id,
                LeaseAgreement.society_id == society_id,
                LeaseAgreement.building_id == building_id,
                LeaseAgreement.flat_id == flat_id,
            )
            .order_by(LeaseAgreement.agreement_end_date.desc(), LeaseAgreement.created_at.desc())
        )
    )


def get_lease_agreement_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    lease_agreement_id: uuid.UUID,
) -> LeaseAgreement:
    lease = session.scalar(
        select(LeaseAgreement).where(
            LeaseAgreement.id == lease_agreement_id,
            LeaseAgreement.tenant_id == tenant_context.tenant_id,
            LeaseAgreement.society_id == society_id,
            LeaseAgreement.building_id == building_id,
            LeaseAgreement.flat_id == flat_id,
        )
    )
    if lease is None:
        raise LeaseAgreementNotFoundError("Lease agreement not found.")
    return lease


def create_lease_agreement(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    payload: LeaseAgreementCreate,
    actor: User,
) -> LeaseAgreement:
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
    ensure_resident_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        resident_id=payload.resident_id,
    )
    ensure_active_lease_unique(session, tenant_context=tenant_context, society_id=society_id, flat_id=flat_id)

    lease = LeaseAgreement(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        owner_id=payload.owner_id,
        resident_id=payload.resident_id,
        tenant_name=payload.tenant_name,
        tenant_email=str(payload.tenant_email) if payload.tenant_email else None,
        tenant_mobile_number=payload.tenant_mobile_number,
        agreement_start_date=payload.agreement_start_date,
        agreement_end_date=payload.agreement_end_date,
        move_in_date=payload.move_in_date,
        move_out_date=payload.move_out_date,
        monthly_rent=payload.monthly_rent,
        security_deposit=payload.security_deposit,
        police_verification_status=payload.police_verification_status,
        document_reference=payload.document_reference,
        notes=payload.notes,
        status="terminated" if payload.move_out_date else "active",
    )
    session.add(lease)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise LeaseAgreementAlreadyExistsError("Active lease already exists for this flat.") from exc

    record_audit_log(
        session,
        action="lease_agreement.created",
        entity_type="LeaseAgreement",
        entity_id=lease.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Lease agreement created: {lease.tenant_name}",
        metadata={
            "society_id": str(society_id),
            "building_id": str(building_id),
            "flat_id": str(flat_id),
            "agreement_end_date": lease.agreement_end_date.isoformat(),
        },
    )
    session.commit()
    session.refresh(lease)
    return lease


def update_lease_agreement(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    lease_agreement_id: uuid.UUID,
    payload: LeaseAgreementUpdate,
    actor: User,
) -> LeaseAgreement:
    lease = get_lease_agreement_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        lease_agreement_id=lease_agreement_id,
    )
    ensure_owner_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        owner_id=payload.owner_id,
    )
    ensure_resident_exists(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        flat_id=flat_id,
        resident_id=payload.resident_id,
    )
    target_status = "terminated" if payload.move_out_date else "active"
    if target_status == "active":
        ensure_active_lease_unique(
            session,
            tenant_context=tenant_context,
            society_id=society_id,
            flat_id=flat_id,
            existing_lease_id=lease.id,
        )

    previous_values = {
        "owner_id": str(lease.owner_id),
        "resident_id": str(lease.resident_id) if lease.resident_id else None,
        "tenant_name": lease.tenant_name,
        "agreement_start_date": lease.agreement_start_date.isoformat(),
        "agreement_end_date": lease.agreement_end_date.isoformat(),
        "status": lease.status,
    }

    lease.owner_id = payload.owner_id
    lease.resident_id = payload.resident_id
    lease.tenant_name = payload.tenant_name
    lease.tenant_email = str(payload.tenant_email) if payload.tenant_email else None
    lease.tenant_mobile_number = payload.tenant_mobile_number
    lease.agreement_start_date = payload.agreement_start_date
    lease.agreement_end_date = payload.agreement_end_date
    lease.move_in_date = payload.move_in_date
    lease.move_out_date = payload.move_out_date
    lease.monthly_rent = payload.monthly_rent
    lease.security_deposit = payload.security_deposit
    lease.police_verification_status = payload.police_verification_status
    lease.document_reference = payload.document_reference
    lease.notes = payload.notes
    lease.status = target_status

    record_audit_log(
        session,
        action="lease_agreement.updated",
        entity_type="LeaseAgreement",
        entity_id=lease.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Lease agreement updated: {lease.tenant_name}",
        metadata={"previous": previous_values, "current_status": lease.status},
    )
    session.commit()
    session.refresh(lease)
    return lease


def terminate_lease_agreement(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    flat_id: uuid.UUID,
    lease_agreement_id: uuid.UUID,
    move_out_date: date,
    reason: str,
    actor: User,
) -> LeaseAgreement:
    lease = get_lease_agreement_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        lease_agreement_id=lease_agreement_id,
    )
    if move_out_date < lease.move_in_date:
        raise LeaseAgreementInvalidDateError("move_out_date must be on or after move_in_date.")

    previous_status = lease.status
    lease.move_out_date = move_out_date
    lease.status = "terminated"

    record_audit_log(
        session,
        action="lease_agreement.terminated",
        entity_type="LeaseAgreement",
        entity_id=lease.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Lease agreement terminated: {lease.tenant_name}",
        metadata={
            "previous_status": previous_status,
            "current_status": lease.status,
            "move_out_date": lease.move_out_date.isoformat(),
            "reason": reason,
        },
    )
    session.commit()
    session.refresh(lease)
    return lease
