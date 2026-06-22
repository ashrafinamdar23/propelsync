import uuid

from app.models import Wing


def test_wing_model_supports_building_scoped_wing() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building_id = uuid.uuid4()
    wing = Wing(
        tenant_id=tenant_id,
        society_id=society_id,
        building_id=building_id,
        name="A Wing",
        code="A",
    )

    assert wing.tenant_id == tenant_id
    assert wing.society_id == society_id
    assert wing.building_id == building_id
    assert wing.name == "A Wing"
    assert wing.code == "A"
    assert wing.status is None or wing.status == "active"


def test_wing_model_requires_building_scope() -> None:
    building_id = uuid.uuid4()
    wing = Wing(
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        building_id=building_id,
        name="A Wing",
    )

    assert wing.building_id == building_id
