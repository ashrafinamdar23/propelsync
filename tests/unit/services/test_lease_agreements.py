import uuid
from datetime import date

import pytest

from app.models import Flat, LeaseAgreement, Owner, Resident, User
from app.schemas.lease_agreement import LeaseAgreementCreate
from app.services.lease_agreements import (
    LeaseAgreementAlreadyExistsError,
    LeaseAgreementInvalidDateError,
    LeaseAgreementOwnerNotFoundError,
    create_lease_agreement,
    terminate_lease_agreement,
)
from app.tenants.context import TenantContext


class FakeSession:
    def __init__(
        self,
        *,
        scalar_results: list[object | None] | None = None,
    ) -> None:
        self.scalar_results = scalar_results or []
        self.added: list[object] = []
        self.committed = False

    def scalar(self, *_: object) -> object | None:
        return self.scalar_results.pop(0) if self.scalar_results else None

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


def build_payload(owner_id: uuid.UUID, resident_id: uuid.UUID | None = None) -> LeaseAgreementCreate:
    return LeaseAgreementCreate(
        owner_id=owner_id,
        resident_id=resident_id,
        tenant_name="Neha Rao",
        tenant_email="neha@example.com",
        tenant_mobile_number="+919812345678",
        agreement_start_date=date(2026, 4, 1),
        agreement_end_date=date(2027, 3, 31),
        move_in_date=date(2026, 4, 1),
        monthly_rent="25000.00",
        security_deposit="100000.00",
        police_verification_status="pending",
        document_reference="LEASE-101",
    )


def test_create_lease_agreement_adds_active_lease_and_audit_log() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    resident_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(id=flat_id, tenant_id=tenant_id, society_id=society_id, building_id=building_id, flat_number="101")
    owner = Owner(id=owner_id, tenant_id=tenant_id, society_id=society_id, full_name="Asha Mehta")
    resident = Resident(
        id=resident_id,
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        resident_type="tenant",
        full_name="Neha Rao",
        move_in_date=date(2026, 4, 1),
    )
    session = FakeSession(scalar_results=[flat, owner, resident, None])

    lease = create_lease_agreement(
        session,  # type: ignore[arg-type]
        tenant_context=context,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        payload=build_payload(owner_id, resident_id),
        actor=actor,
    )

    assert lease.tenant_id == tenant_id
    assert lease.society_id == society_id
    assert lease.flat_id == flat_id
    assert lease.owner_id == owner_id
    assert lease.resident_id == resident_id
    assert lease.status == "active"
    assert session.committed is True
    assert len(session.added) == 2


def test_create_lease_agreement_rejects_missing_owner() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(id=flat_id, tenant_id=tenant_id, society_id=society_id, building_id=building_id, flat_number="101")
    owner_id = uuid.uuid4()
    session = FakeSession(scalar_results=[flat, None])

    with pytest.raises(LeaseAgreementOwnerNotFoundError):
        create_lease_agreement(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=build_payload(owner_id),
            actor=actor,
        )


def test_create_lease_agreement_rejects_second_active_lease() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    actor = build_actor()
    context = build_context(tenant_id, actor)
    flat = Flat(id=flat_id, tenant_id=tenant_id, society_id=society_id, building_id=building_id, flat_number="101")
    owner = Owner(id=owner_id, tenant_id=tenant_id, society_id=society_id, full_name="Asha Mehta")
    existing = LeaseAgreement(
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        owner_id=owner_id,
        tenant_name="Current Tenant",
        agreement_start_date=date(2026, 1, 1),
        agreement_end_date=date(2026, 12, 31),
        move_in_date=date(2026, 1, 1),
        status="active",
    )
    session = FakeSession(scalar_results=[flat, owner, existing])

    with pytest.raises(LeaseAgreementAlreadyExistsError):
        create_lease_agreement(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            payload=build_payload(owner_id),
            actor=actor,
        )


def test_terminate_lease_agreement_rejects_move_out_before_move_in() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    lease = LeaseAgreement(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_id=flat_id,
        owner_id=uuid.uuid4(),
        tenant_name="Neha Rao",
        agreement_start_date=date(2026, 4, 1),
        agreement_end_date=date(2027, 3, 31),
        move_in_date=date(2026, 4, 1),
        status="active",
    )
    actor = build_actor()
    context = build_context(tenant_id, actor)
    session = FakeSession(scalar_results=[lease])

    with pytest.raises(LeaseAgreementInvalidDateError):
        terminate_lease_agreement(
            session,  # type: ignore[arg-type]
            tenant_context=context,
            society_id=society_id,
            building_id=building_id,
            flat_id=flat_id,
            lease_agreement_id=lease.id,
            move_out_date=date(2026, 3, 31),
            reason="Incorrect agreement",
            actor=actor,
        )
