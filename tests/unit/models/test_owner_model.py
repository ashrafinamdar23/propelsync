import uuid

from app.models import Owner


def test_owner_model_supports_offline_owner_without_user_account() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    owner = Owner(
        tenant_id=tenant_id,
        society_id=society_id,
        full_name="Asha Mehta",
        email="asha@example.com",
        mobile_number="+919876543210",
    )

    assert owner.tenant_id == tenant_id
    assert owner.society_id == society_id
    assert owner.user_id is None
    assert owner.full_name == "Asha Mehta"
    assert owner.email == "asha@example.com"
    assert owner.mobile_number == "+919876543210"
    assert owner.owner_type is None or owner.owner_type == "individual"
    assert owner.status is None or owner.status == "active"


def test_owner_model_can_link_to_user_for_portal_access() -> None:
    user_id = uuid.uuid4()
    owner = Owner(
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        user_id=user_id,
        full_name="Rahul Shah",
    )

    assert owner.user_id == user_id
