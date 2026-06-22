import uuid

from app.models import Society


def test_society_model_defaults_and_tenant_ownership() -> None:
    tenant_id = uuid.uuid4()
    society = Society(name="Green Heights CHS", tenant_id=tenant_id)

    assert society.name == "Green Heights CHS"
    assert society.tenant_id == tenant_id
    assert society.country is None or society.country == "India"
    assert society.timezone is None or society.timezone == "Asia/Kolkata"
    assert society.locale is None or society.locale == "en-IN"
    assert society.currency is None or society.currency == "INR"
    assert society.financial_year_start_month is None or society.financial_year_start_month == 4
    assert society.status is None or society.status == "active"
