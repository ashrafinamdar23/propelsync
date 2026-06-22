import uuid
from datetime import date
from decimal import Decimal

from app.models import FlatOwnership


def test_flat_ownership_model_supports_current_primary_owner() -> None:
    tenant_id = uuid.uuid4()
    society_id = uuid.uuid4()
    flat_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    ownership = FlatOwnership(
        tenant_id=tenant_id,
        society_id=society_id,
        flat_id=flat_id,
        owner_id=owner_id,
        ownership_type="primary_owner",
        ownership_percentage=Decimal("100.00"),
        effective_from=date(2026, 4, 1),
    )

    assert ownership.tenant_id == tenant_id
    assert ownership.society_id == society_id
    assert ownership.flat_id == flat_id
    assert ownership.owner_id == owner_id
    assert ownership.ownership_type == "primary_owner"
    assert ownership.ownership_percentage == Decimal("100.00")
    assert ownership.effective_from == date(2026, 4, 1)
    assert ownership.effective_to is None
    assert ownership.status is None or ownership.status == "active"


def test_flat_ownership_model_supports_historical_co_owner() -> None:
    ownership = FlatOwnership(
        tenant_id=uuid.uuid4(),
        society_id=uuid.uuid4(),
        flat_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        ownership_type="co_owner",
        effective_from=date(2025, 4, 1),
        effective_to=date(2026, 3, 31),
        status="inactive",
    )

    assert ownership.ownership_type == "co_owner"
    assert ownership.effective_to == date(2026, 3, 31)
    assert ownership.status == "inactive"
