import uuid

import pytest

from app.models import Society, User, Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate
from app.services.vendors import (
    VendorAlreadyExistsError,
    VendorSocietyNotFoundError,
    change_vendor_status,
    create_vendor,
    update_vendor,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        existing_vendor: Vendor | None = None,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.existing_vendor = existing_vendor
        self.scalar_results = scalar_results
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        if self.scalar_results is not None:
            return self.scalar_results.pop(0)
        return self.existing_vendor

    def add(self, instance: object) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        for instance in self.added:
            if getattr(instance, "id", None) is None:
                instance.id = uuid.uuid4()

    def commit(self) -> None:
        self.committed = True

    def refresh(self, _: object) -> None:
        return None


def build_actor() -> User:
    return User(
        id=uuid.uuid4(),
        keycloak_subject="subject-1",
        email="admin@example.com",
        full_name="Society Admin",
    )


def build_context(tenant_id: uuid.UUID, actor: User) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant=None,  # type: ignore[arg-type]
        user=actor,
    )


def test_create_vendor_adds_vendor_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    session = FakeSession(scalar_results=[society, None])
    payload = VendorCreate(
        vendor_code="VEND-001",
        vendor_name="CleanCo Services",
        vendor_type="company",
        contact_person="Asha Mehta",
        email="billing@cleanco.example",
    )

    vendor = create_vendor(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        payload=payload,
        actor=actor,
    )

    assert vendor.tenant_id == tenant_id
    assert vendor.society_id == society_id
    assert vendor.vendor_code == "VEND-001"
    assert vendor.vendor_name == "CleanCo Services"
    assert vendor.status == "active"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_vendor_rejects_missing_society() -> None:
    actor = build_actor()
    context = build_context(uuid.uuid4(), actor)
    session = FakeSession(scalar_results=[None])
    payload = VendorCreate(vendor_code="VEND-001", vendor_name="CleanCo Services")

    with pytest.raises(VendorSocietyNotFoundError):
        create_vendor(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=uuid.uuid4(),
            payload=payload,
            actor=actor,
        )


def test_create_vendor_rejects_duplicate_code() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    society = Society(id=society_id, tenant_id=tenant_id, name="Green Heights")
    existing_vendor = Vendor(
        tenant_id=tenant_id,
        society_id=society_id,
        vendor_code="VEND-001",
        vendor_name="Existing Vendor",
    )
    session = FakeSession(scalar_results=[society, existing_vendor])
    payload = VendorCreate(vendor_code="VEND-001", vendor_name="CleanCo Services")

    with pytest.raises(VendorAlreadyExistsError):
        create_vendor(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            payload=payload,
            actor=actor,
        )


def test_update_vendor_changes_editable_fields_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    vendor = Vendor(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        vendor_code="VEND-001",
        vendor_name="CleanCo Services",
        vendor_type="company",
        status="active",
    )
    session = FakeSession(scalar_results=[vendor, None])
    payload = VendorUpdate(
        vendor_code="VEND-002",
        vendor_name="CleanCo Facility Services",
        vendor_type="firm",
        mobile_number="+919876543210",
    )

    updated = update_vendor(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        vendor_id=vendor.id,
        payload=payload,
        actor=actor,
    )

    assert updated.vendor_code == "VEND-002"
    assert updated.vendor_name == "CleanCo Facility Services"
    assert updated.vendor_type == "firm"
    assert session.committed is True
    assert len(session.added) == 1


def test_change_vendor_status_updates_status_and_adds_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    vendor = Vendor(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        vendor_code="VEND-001",
        vendor_name="CleanCo Services",
        status="active",
    )
    session = FakeSession(existing_vendor=vendor)

    updated = change_vendor_status(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        vendor_id=vendor.id,
        status="inactive",
        actor=actor,
    )

    assert updated.status == "inactive"
    assert session.committed is True
    assert len(session.added) == 1
