import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Society, User, Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate
from app.services.audit import record_audit_log
from app.tenants.context import TenantContext


class VendorAlreadyExistsError(Exception):
    pass


class VendorNotFoundError(Exception):
    pass


class VendorSocietyNotFoundError(Exception):
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
        raise VendorSocietyNotFoundError("Society not found.")


def ensure_vendor_code_unique(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_code: str,
    existing_vendor_id: uuid.UUID | None = None,
) -> None:
    statement = select(Vendor).where(
        Vendor.tenant_id == tenant_context.tenant_id,
        Vendor.society_id == society_id,
        Vendor.vendor_code == vendor_code,
    )
    if existing_vendor_id is not None:
        statement = statement.where(Vendor.id != existing_vendor_id)

    if session.scalar(statement) is not None:
        raise VendorAlreadyExistsError("Vendor code already exists in this society.")


def list_vendors(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
) -> list[Vendor]:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    return list(
        session.scalars(
            select(Vendor)
            .where(
                Vendor.tenant_id == tenant_context.tenant_id,
                Vendor.society_id == society_id,
            )
            .order_by(Vendor.vendor_name)
        )
    )


def get_vendor_or_raise(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_id: uuid.UUID,
) -> Vendor:
    vendor = session.scalar(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.tenant_id == tenant_context.tenant_id,
            Vendor.society_id == society_id,
        )
    )
    if vendor is None:
        raise VendorNotFoundError("Vendor not found.")
    return vendor


def create_vendor(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    payload: VendorCreate,
    actor: User,
) -> Vendor:
    ensure_society_exists(session, tenant_context=tenant_context, society_id=society_id)
    ensure_vendor_code_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_code=payload.vendor_code,
    )

    vendor = Vendor(
        tenant_id=tenant_context.tenant_id,
        society_id=society_id,
        vendor_code=payload.vendor_code,
        vendor_name=payload.vendor_name,
        vendor_type=payload.vendor_type,
        contact_person=payload.contact_person,
        email=str(payload.email) if payload.email else None,
        mobile_number=payload.mobile_number,
        tax_identifier=payload.tax_identifier,
        billing_address=payload.billing_address,
        status="active",
    )
    session.add(vendor)
    session.flush()

    record_audit_log(
        session,
        action="vendor.created",
        entity_type="Vendor",
        entity_id=vendor.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Vendor created: {vendor.vendor_name}",
        metadata={
            "society_id": str(society_id),
            "vendor_code": vendor.vendor_code,
            "vendor_type": vendor.vendor_type,
        },
    )
    session.commit()
    session.refresh(vendor)
    return vendor


def update_vendor(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_id: uuid.UUID,
    payload: VendorUpdate,
    actor: User,
) -> Vendor:
    vendor = get_vendor_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_id=vendor_id,
    )
    ensure_vendor_code_unique(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_code=payload.vendor_code,
        existing_vendor_id=vendor.id,
    )

    previous_values = {
        "vendor_code": vendor.vendor_code,
        "vendor_name": vendor.vendor_name,
        "vendor_type": vendor.vendor_type,
        "contact_person": vendor.contact_person,
        "email": vendor.email,
        "mobile_number": vendor.mobile_number,
        "tax_identifier": vendor.tax_identifier,
    }
    vendor.vendor_code = payload.vendor_code
    vendor.vendor_name = payload.vendor_name
    vendor.vendor_type = payload.vendor_type
    vendor.contact_person = payload.contact_person
    vendor.email = str(payload.email) if payload.email else None
    vendor.mobile_number = payload.mobile_number
    vendor.tax_identifier = payload.tax_identifier
    vendor.billing_address = payload.billing_address

    record_audit_log(
        session,
        action="vendor.updated",
        entity_type="Vendor",
        entity_id=vendor.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Vendor updated: {vendor.vendor_name}",
        metadata={
            "society_id": str(society_id),
            "previous": previous_values,
            "current": {
                "vendor_code": vendor.vendor_code,
                "vendor_name": vendor.vendor_name,
                "vendor_type": vendor.vendor_type,
                "contact_person": vendor.contact_person,
                "email": vendor.email,
                "mobile_number": vendor.mobile_number,
                "tax_identifier": vendor.tax_identifier,
            },
        },
    )
    session.commit()
    session.refresh(vendor)
    return vendor


def change_vendor_status(
    session: Session,
    *,
    tenant_context: TenantContext,
    society_id: uuid.UUID,
    vendor_id: uuid.UUID,
    status: str,
    actor: User,
) -> Vendor:
    vendor = get_vendor_or_raise(
        session,
        tenant_context=tenant_context,
        society_id=society_id,
        vendor_id=vendor_id,
    )
    previous_status = vendor.status
    vendor.status = status

    action = "vendor.inactivated" if status == "inactive" else "vendor.activated"
    record_audit_log(
        session,
        action=action,
        entity_type="Vendor",
        entity_id=vendor.id,
        actor_user_id=actor.id,
        tenant_id=tenant_context.tenant_id,
        summary=f"Vendor {status}: {vendor.vendor_name}",
        metadata={
            "society_id": str(society_id),
            "previous_status": previous_status,
            "current_status": status,
        },
    )
    session.commit()
    session.refresh(vendor)
    return vendor
