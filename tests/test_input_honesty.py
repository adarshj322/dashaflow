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


class TestTimeSensitivity:
    def test_stable_chart_is_robust(self):
        s = dashaflow.get_time_sensitivity(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
            query_date="2026-01-01")
        assert s["verdict"] == "robust"
        assert s["lagna_stable"] is True
        assert s["moon_pada_stable"] is True

    def test_cusp_chart_is_fragile(self):
        s = dashaflow.get_time_sensitivity(
            "1990-04-15", "04:30", 28.6139, 77.2090, "Asia/Kolkata",
            query_date="2026-01-01")
        assert s["verdict"] == "fragile"
        assert s["lagna_stable"] is False
        assert any("Pisces" in n for n in s["notes"])

    def test_near_cusp_chart_is_borderline(self):
        s = dashaflow.get_time_sensitivity(
            "1990-04-15", "03:00", 28.6139, 77.2090, "Asia/Kolkata",
            query_date="2026-01-01")
        assert s["verdict"] == "borderline"
        assert s["lagna_stable"] is True

    def test_wider_window_escalates_borderline(self):
        narrow = dashaflow.get_time_sensitivity(
            "1990-04-15", "03:00", 28.6139, 77.2090, "Asia/Kolkata",
            query_date="2026-01-01", window_minutes=4)
        wide = dashaflow.get_time_sensitivity(
            "1990-04-15", "03:00", 28.6139, 77.2090, "Asia/Kolkata",
            query_date="2026-01-01", window_minutes=8)
        assert narrow["verdict"] == "borderline"
        assert wide["verdict"] == "fragile"
        assert wide["lagna_stable"] is False


class TestSensitivityEdges:
    def test_invalid_window_rejected(self):
        import pytest

        with pytest.raises(InvalidInputError):
            dashaflow.get_time_sensitivity(
                "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
                window_minutes=0)
        with pytest.raises(InvalidInputError):
            dashaflow.get_time_sensitivity(
                "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
                window_minutes=-5)

    def test_midnight_rollover(self):
        s = dashaflow.get_time_sensitivity(
            "1990-04-16", "00:02", 28.6139, 77.2090, "Asia/Kolkata",
            query_date="2026-01-01")
        assert s["verdict"] in ("robust", "borderline", "fragile")
        assert s["window_minutes"] == 4
