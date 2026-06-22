import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tenant, User
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.services.audit import record_audit_log


class TenantAlreadyExistsError(Exception):
    pass


class TenantNotFoundError(Exception):
    pass


def list_tenants(session: Session) -> list[Tenant]:
    return list(session.scalars(select(Tenant).order_by(Tenant.created_at.desc(), Tenant.name)))


def get_tenant_or_raise(session: Session, tenant_id: uuid.UUID) -> Tenant:
    tenant = session.get(Tenant, tenant_id)
    if tenant is None:
        raise TenantNotFoundError("Tenant not found.")
    return tenant


def create_tenant(
    session: Session,
    *,
    payload: TenantCreate,
    actor: User,
) -> Tenant:
    existing_tenant = session.scalar(select(Tenant).where(Tenant.slug == payload.slug))
    if existing_tenant is not None:
        raise TenantAlreadyExistsError("Tenant slug already exists.")

    tenant = Tenant(
        name=payload.name,
        slug=payload.slug,
        status="active",
        subscription_plan=payload.subscription_plan,
        billing_email=str(payload.billing_email) if payload.billing_email else None,
        phone=payload.phone,
        timezone=payload.timezone,
        locale=payload.locale,
        currency=payload.currency.upper(),
        metadata_=payload.metadata,
    )
    session.add(tenant)
    session.flush()

    record_audit_log(
        session,
        action="tenant.created",
        entity_type="Tenant",
        entity_id=tenant.id,
        actor_user_id=actor.id,
        tenant_id=None,
        summary=f"Tenant created: {tenant.name}",
        metadata={
            "slug": tenant.slug,
            "subscription_plan": tenant.subscription_plan,
        },
    )
    session.commit()
    session.refresh(tenant)
    return tenant


def update_tenant(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    payload: TenantUpdate,
    actor: User,
) -> Tenant:
    tenant = get_tenant_or_raise(session, tenant_id)
    previous_values = {
        "name": tenant.name,
        "subscription_plan": tenant.subscription_plan,
        "billing_email": tenant.billing_email,
        "phone": tenant.phone,
        "timezone": tenant.timezone,
        "locale": tenant.locale,
        "currency": tenant.currency,
        "metadata": tenant.metadata_,
    }

    tenant.name = payload.name
    tenant.subscription_plan = payload.subscription_plan
    tenant.billing_email = str(payload.billing_email) if payload.billing_email else None
    tenant.phone = payload.phone
    tenant.timezone = payload.timezone
    tenant.locale = payload.locale
    tenant.currency = payload.currency.upper()
    tenant.metadata_ = payload.metadata

    record_audit_log(
        session,
        action="tenant.updated",
        entity_type="Tenant",
        entity_id=tenant.id,
        actor_user_id=actor.id,
        tenant_id=None,
        summary=f"Tenant updated: {tenant.name}",
        metadata={
            "slug": tenant.slug,
            "previous": previous_values,
            "current": {
                "name": tenant.name,
                "subscription_plan": tenant.subscription_plan,
                "billing_email": tenant.billing_email,
                "phone": tenant.phone,
                "timezone": tenant.timezone,
                "locale": tenant.locale,
                "currency": tenant.currency,
                "metadata": tenant.metadata_,
            },
        },
    )
    session.commit()
    session.refresh(tenant)
    return tenant


def change_tenant_status(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    status: str,
    actor: User,
) -> Tenant:
    tenant = get_tenant_or_raise(session, tenant_id)
    previous_status = tenant.status
    tenant.status = status

    action = "tenant.suspended" if status == "suspended" else "tenant.activated"
    record_audit_log(
        session,
        action=action,
        entity_type="Tenant",
        entity_id=tenant.id,
        actor_user_id=actor.id,
        tenant_id=None,
        summary=f"Tenant {status}: {tenant.name}",
        metadata={
            "slug": tenant.slug,
            "previous_status": previous_status,
            "current_status": status,
        },
    )
    session.commit()
    session.refresh(tenant)
    return tenant
