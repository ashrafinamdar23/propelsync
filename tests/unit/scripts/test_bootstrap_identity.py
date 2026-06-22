import pytest

from app.scripts.bootstrap_identity import get_bootstrap_username, split_full_name


def test_split_full_name_with_first_and_last_name() -> None:
    assert split_full_name("Platform Admin") == ("Platform", "Admin")


def test_split_full_name_with_single_name() -> None:
    assert split_full_name("Admin") == ("Admin", "")


def test_get_bootstrap_username_prefers_email() -> None:
    assert get_bootstrap_username("admin@propelsync.local", "+919876543210") == (
        "admin@propelsync.local"
    )


def test_get_bootstrap_username_falls_back_to_mobile_number() -> None:
    assert get_bootstrap_username(None, "+919876543210") == "+919876543210"


def test_get_bootstrap_username_requires_identity() -> None:
    with pytest.raises(ValueError):
        get_bootstrap_username(None, None)
