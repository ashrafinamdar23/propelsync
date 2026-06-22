import uuid
from datetime import date

from app.models import Resident


def test_resident_model_supports_tenant_without_owner_or_user_account() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    resident = Resident(
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        resident_type="tenant",
        full_name="Neha Rao",
        mobile_number="+919812345678",
        move_in_date=date(2026, 6, 1),
    )

    assert resident.tenant_id == tenant_id
    assert resident.society_id == society_id
    assert resident.flat_id == flat_id
    assert resident.owner_id is None
    assert resident.user_id is None
    assert resident.resident_type == "tenant"
    assert resident.full_name == "Neha Rao"
    assert resident.mobile_number == "+919812345678"
    assert resident.move_in_date == date(2026, 6, 1)
    assert resident.move_out_date is None
    assert resident.status is None or resident.status == "active"


def test_resident_model_supports_owner_occupier_linked_to_owner_and_user() -> None:
    owner_id = uuid.uuid4()
    user_id = uuid.uuid4()
    resident = Resident(
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        owner_id=owner_id,
        user_id=user_id,
        resident_type="owner_occupier",
        full_name="Asha Mehta",
        move_in_date=date(2026, 4, 1),
    )

    assert resident.owner_id == owner_id
    assert resident.user_id == user_id
    assert resident.resident_type == "owner_occupier"
