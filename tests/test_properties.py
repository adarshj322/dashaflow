import datetime

import pytest  # noqa: F401 -- mandated by Task 1 brief; Task 3 uses @pytest.mark.parametrize
from hypothesis import given, settings
from hypothesis import strategies as st

import dashaflow
from dashaflow._ayanamsha import AYANAMSHA_VARIANTS

VARIANTS = list(AYANAMSHA_VARIANTS) + ["kp", "kp_new", "LAHIRI", "lahiri-icrc"]

TIMEZONES = ["Asia/Kolkata", "UTC", "America/New_York",
             "Pacific/Auckland", "Arctic/Longyearbyen"]


@st.composite
def birth_input(draw):
    date = draw(st.dates(min_value=datetime.date(1900, 1, 1),
                         max_value=datetime.date(2100, 12, 31)))
    return (
        date.isoformat(),
        f"{draw(st.integers(0, 23)):02d}:{draw(st.integers(0, 59)):02d}",
        draw(st.floats(min_value=-66.0, max_value=66.0,
                       allow_nan=False, allow_infinity=False)),
        draw(st.floats(min_value=-180.0, max_value=180.0,
                       allow_nan=False, allow_infinity=False)),
        draw(st.sampled_from(TIMEZONES)),
    )


@settings(max_examples=25, deadline=None)
@given(birth_input(), st.sampled_from(VARIANTS))
def test_sav_totals_337(birth, variant):
    chart = dashaflow.cast_chart(*birth, ayanamsha=variant)
    assert chart["ashtakavarga"]["total_bindus"] == 337


def test_polar_chart_keeps_sav():
    chart = dashaflow.cast_chart("1990-06-15", "12:00", 78.2232, 15.6469,
                                 "Arctic/Longyearbyen")
    assert chart["ashtakavarga"]["total_bindus"] == 337


def test_leap_day_casts():
    chart = dashaflow.cast_chart("2000-02-29", "06:15", 28.6139, 77.2090,
                                 "Asia/Kolkata")
    assert chart["ashtakavarga"]["total_bindus"] == 337
