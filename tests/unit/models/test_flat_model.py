import uuid
from decimal import Decimal

from app.models import Flat


def test_flat_model_requires_building_and_allows_no_wing() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    flat = Flat(
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        flat_number="101",
        floor_number=1,
        carpet_area_sqft=Decimal("725.50"),
        built_up_area_sqft=Decimal("900.00"),
        parking_count=1,
    )

    assert flat.tenant_id == tenant_id
    assert flat.society_id == society_id
    assert flat.building_id == building_id
    assert flat.wing_id is None
    assert flat.flat_number == "101"
    assert flat.floor_number == 1
    assert flat.carpet_area_sqft == Decimal("725.50")
    assert flat.built_up_area_sqft == Decimal("900.00")
    assert flat.parking_count == 1
    assert flat.status is None or flat.status == "active"


def test_flat_model_allows_wing_when_society_uses_wings() -> None:
    wing_id = uuid.uuid4()
    flat = Flat(
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        building_id=uuid.uuid4(),
        wing_id=wing_id,
        flat_number="A-101",
    )

    assert flat.wing_id == wing_id
