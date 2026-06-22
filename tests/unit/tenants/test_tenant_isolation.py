import uuid

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwnedMixin, UUIDPrimaryKeyMixin
from app.tenants.context import TenantContext, TenantIsolationError
from app.tenants.repository import assign_tenant, ensure_tenant_access, tenant_scoped_select


class ExampleTenantOwned(UUIDPrimaryKeyMixin, TenantOwnedMixin, Base):
    __tablename__ = "test_tenant_owned_examples"

    name: Mapped[str] = mapped_column(String(100), nullable=False)


def build_tenant_context(tenant_id: uuid.UUID) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant=None,  # type: ignore[arg-type]
        user=None,  # type: ignore[arg-type]
    )


def test_assign_tenant_sets_missing_tenant_id() -> None:
    tenant_id = uuid.uuid4()
    context = build_tenant_context(tenant_id)
    instance = ExampleTenantOwned(name="Example")

    assign_tenant(instance, context)

    assert instance.tenant_id == tenant_id


def test_assign_tenant_rejects_cross_tenant_instance() -> None:
    context = build_tenant_context(uuid.uuid4())
    instance = ExampleTenantOwned(name="Example", tenant_id=uuid.uuid4())

    with pytest.raises(TenantIsolationError):
        assign_tenant(instance, context)


def test_ensure_tenant_access_rejects_other_tenant() -> None:
    context = build_tenant_context(uuid.uuid4())

    with pytest.raises(TenantIsolationError):
        ensure_tenant_access(uuid.uuid4(), context)


def test_tenant_scoped_select_adds_tenant_filter() -> None:
    tenant_id = uuid.uuid4()
    context = build_tenant_context(tenant_id)

    statement = tenant_scoped_select(ExampleTenantOwned, context)

    assert statement.whereclause is not None
    assert statement.whereclause.right.value == tenant_id
