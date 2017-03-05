from datetime import datetime

import pytz
import pytest

from mobius.helpers import week_day_range, normalize_to_midnight
from .helpers import ApiSpoof


def test_week_day_range_throws_error_for_invalid_day():
    with pytest.raises(ValueError):
        week_day_range("miercoles")


def test_week_day_range_succeeds_with_no_input():
    week_day_range()


def test_days_of_week_returns_correct_days_of_week_order():
    expected = ["wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
                "monday",
                "tuesday", ]
    actual = week_day_range(expected[0])
    assert actual == expected


def test_normalize_to_midnight():
    start = datetime(
        1990, 12, 9, 6,
        22, 11, tzinfo=pytz.timezone("US/Eastern"))
    expected = datetime(
        1990, 12, 9, 0,
        0, 0, tzinfo=pytz.timezone("US/Eastern"))
    assert normalize_to_midnight(start) == expected
