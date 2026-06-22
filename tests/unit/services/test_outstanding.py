from datetime import date
from decimal import Decimal

from app.services.outstanding import ageing_bucket_for_due_date, empty_ageing, money


def test_money_quantizes_to_two_decimals() -> None:
    assert money(Decimal("15.555")) == Decimal("15.56")


def test_empty_ageing_starts_at_zero() -> None:
    assert empty_ageing() == {
        "current": Decimal("0.00"),
        "days_1_30": Decimal("0.00"),
        "days_31_60": Decimal("0.00"),
        "days_61_90": Decimal("0.00"),
        "days_90_plus": Decimal("0.00"),
    }


def test_ageing_bucket_for_current_and_future_due_dates() -> None:
    as_of_date = date(2026, 6, 22)

    assert ageing_bucket_for_due_date(date(2026, 6, 22), as_of_date=as_of_date) == "current"
    assert ageing_bucket_for_due_date(date(2026, 6, 23), as_of_date=as_of_date) == "current"


def test_ageing_bucket_boundaries() -> None:
    as_of_date = date(2026, 6, 22)

    assert ageing_bucket_for_due_date(date(2026, 6, 21), as_of_date=as_of_date) == "days_1_30"
    assert ageing_bucket_for_due_date(date(2026, 5, 23), as_of_date=as_of_date) == "days_1_30"
    assert ageing_bucket_for_due_date(date(2026, 5, 22), as_of_date=as_of_date) == "days_31_60"
    assert ageing_bucket_for_due_date(date(2026, 4, 23), as_of_date=as_of_date) == "days_31_60"
    assert ageing_bucket_for_due_date(date(2026, 4, 22), as_of_date=as_of_date) == "days_61_90"
    assert ageing_bucket_for_due_date(date(2026, 3, 24), as_of_date=as_of_date) == "days_61_90"
    assert ageing_bucket_for_due_date(date(2026, 3, 23), as_of_date=as_of_date) == "days_90_plus"
