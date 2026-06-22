import uuid
from typing import TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.base import TenantOwnedMixin
from app.tenants.context import TenantContext, TenantIsolationError


TenantOwnedModel = TypeVar("TenantOwnedModel", bound=TenantOwnedMixin)


def tenant_scoped_select(
    model: type[TenantOwnedModel],
    tenant_context: TenantContext,
) -> Select[tuple[TenantOwnedModel]]:
    return select(model).where(model.tenant_id == tenant_context.tenant_id)


def assign_tenant(
    instance: TenantOwnedModel,
    tenant_context: TenantContext,
) -> TenantOwnedModel:
    existing_tenant_id = getattr(instance, "tenant_id", None)
    if existing_tenant_id is not None and existing_tenant_id != tenant_context.tenant_id:
        raise TenantIsolationError("Cannot assign data across tenants.")

    instance.tenant_id = tenant_context.tenant_id
    return instance


def add_tenant_owned(
    session: Session,
    instance: TenantOwnedModel,
    tenant_context: TenantContext,
) -> TenantOwnedModel:
    session.add(assign_tenant(instance, tenant_context))
    return instance


def ensure_tenant_access(
    tenant_id: uuid.UUID,
    tenant_context: TenantContext,
) -> None:
    if tenant_id != tenant_context.tenant_id:
        raise TenantIsolationError("Cross-tenant access is not allowed.")
