import uuid

from app.models import Building


def test_building_model_defaults_and_scope() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    building = Building(
        tenant_id=tenant_id,
        society_id=society_id,
        name="Tower A",
        code="A",
    )

    assert building.tenant_id == tenant_id
    assert building.society_id == society_id
    assert building.name == "Tower A"
    assert building.code == "A"
    assert building.status is None or building.status == "active"
