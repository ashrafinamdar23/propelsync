import uuid

from app.models import SocietyMembership, TenantMembership


def test_tenant_membership_supports_tenant_admin_role() -> None:
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership = TenantMembership(
        tenant_id=tenant_id,
        user_id=user_id,
        role="tenant_admin",
    )

    assert membership.tenant_id == tenant_id
    assert membership.user_id == user_id
    assert membership.role == "tenant_admin"
    assert membership.status is None or membership.status == "active"


def test_society_membership_supports_admin_and_flat_owner_roles() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    user_id = uuid.uuid4()
    admin_membership = SocietyMembership(
        tenant_id=tenant_id,
        society_id=society_id,
        user_id=user_id,
        role="society_admin",
    )
    owner_membership = SocietyMembership(
        tenant_id=tenant_id,
        society_id=society_id,
        user_id=user_id,
        role="flat_owner",
    )

    assert admin_membership.role == "society_admin"
    assert owner_membership.role == "flat_owner"
    assert owner_membership.tenant_id == tenant_id
    assert owner_membership.society_id == society_id
    assert owner_membership.user_id == user_id
