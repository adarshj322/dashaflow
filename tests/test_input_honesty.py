"""Tests for Slice 2 input honesty — seconds precision and time sensitivity."""

import dashaflow
from dashaflow import InvalidInputError


def _chart(time="14:30"):
    return dashaflow.cast_chart(
        "1990-04-15", time, 28.6139, 77.2090, "Asia/Kolkata",
        query_date="2026-01-01",
    )


class TestSecondsPrecision:
    def test_seconds_accepted(self):
        chart = _chart("14:30:45")
        assert chart["lagna"]["sign"] == "Leo"

    def test_hhmm_equivalent_to_hhmmss_zero(self):
        plain = _chart("14:30")
        zeroed = _chart("14:30:00")
        for chart in (plain, zeroed):
            chart["metadata"].pop("computed_at_utc")
            chart["metadata"].pop("time")  # echoes raw input; computation must match
        assert plain == zeroed

    def test_bad_seconds_rejected(self):
        import pytest

        with pytest.raises(InvalidInputError):
            _chart("14:30:61")

    def test_bad_hour_rejected(self):
        import pytest

        with pytest.raises(InvalidInputError):
            _chart("24:00:00")
