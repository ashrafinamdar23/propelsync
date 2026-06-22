from app.models import Tenant


def test_tenant_model_defaults() -> None:
    tenant = Tenant(name="Green Heights CHS Account", slug="green-heights")

    assert tenant.name == "Green Heights CHS Account"
    assert tenant.slug == "green-heights"
    assert tenant.status is None or tenant.status == "active"
    assert tenant.subscription_plan is None or tenant.subscription_plan == "starter"
    assert tenant.timezone is None or tenant.timezone == "Asia/Kolkata"
    assert tenant.locale is None or tenant.locale == "en-IN"
    assert tenant.currency is None or tenant.currency == "INR"
