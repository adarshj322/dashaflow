import datetime

import pytest  # noqa: F401 -- mandated by Task 1 brief; Task 3 uses @pytest.mark.parametrize
from hypothesis import given, settings
from hypothesis import strategies as st

import dashaflow
from dashaflow._ayanamsha import AYANAMSHA_VARIANTS
from dashaflow.constants import ZODIAC_SIGNS

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


def _absolute(planet):
    return ZODIAC_SIGNS.index(planet["sign"]) * 30 + planet["degree_precise"]


@settings(max_examples=25, deadline=None)
@given(birth_input(), st.sampled_from(VARIANTS))
def test_variant_shift_matches_ayanamsha_difference(birth, variant):
    lahiri = dashaflow.cast_chart(*birth)
    other = dashaflow.cast_chart(*birth, ayanamsha=variant)
    expected = (lahiri["metadata"]["ayanamsha_degrees"]
                - other["metadata"]["ayanamsha_degrees"]) % 360
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        delta = (_absolute(other["planets"][name])
                 - _absolute(lahiri["planets"][name])) % 360
        assert abs(delta - expected) < 0.001, (birth, variant, name)


@settings(max_examples=25, deadline=None)
@given(birth_input())
def test_dasha_timeline_integrity(birth):
    chart = dashaflow.cast_chart(*birth)
    moon = chart["planets"]["Moon"]
    timeline = chart["dashas"]["timeline"]
    assert timeline[0]["planet"] == moon["nakshatra_lord"]
    for earlier, later in zip(timeline, timeline[1:], strict=False):
        assert earlier["end"] == later["start"]


@pytest.mark.parametrize("dob", ["1900-01-01", "2100-12-31"])
def test_dasha_contiguous_at_range_edges(dob):
    chart = dashaflow.cast_chart(dob, "12:00", 28.6139, 77.2090, "Asia/Kolkata")
    timeline = chart["dashas"]["timeline"]
    for earlier, later in zip(timeline, timeline[1:], strict=False):
        assert earlier["end"] == later["start"]
