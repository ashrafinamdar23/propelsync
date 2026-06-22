from app.models import User


def test_user_model_supports_email_identity() -> None:
    user = User(
        keycloak_subject="keycloak-user-1",
        email="admin@propelsync.local",
        full_name="Platform Admin",
    )

    assert user.keycloak_subject == "keycloak-user-1"
    assert user.email == "admin@propelsync.local"
    assert user.mobile_number is None
    assert user.full_name == "Platform Admin"
    assert user.status is None or user.status == "active"
    assert user.is_platform_superuser is None or user.is_platform_superuser is False


def test_user_model_supports_mobile_identity() -> None:
    user = User(
        keycloak_subject="keycloak-user-2",
        mobile_number="+919876543210",
        full_name="Mobile User",
    )

    assert user.email is None
    assert user.mobile_number == "+919876543210"
