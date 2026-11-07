# tests/test_gold_corpus.py
import datetime
import json
from pathlib import Path

import pytest

import dashaflow
from dashaflow.constants import NAK_SPAN, VIMSHOTTARI_YEARS, ZODIAC_SIGNS
from dashaflow.dasha import SIDEREAL_YEAR_DAYS

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "gold_charts.json").read_text())
CHARTS = FIXTURE["charts"]


def _cast(entry, ayanamsha="lahiri"):
    return dashaflow.cast_chart(
        entry["dob"], entry["time"], entry["lat"], entry["lon"],
        entry["timezone"], ayanamsha=ayanamsha)


def _sidereal_absolute(planet):
    return ZODIAC_SIGNS.index(planet["sign"]) * 30 + planet["degree_precise"]


@pytest.mark.parametrize("entry", CHARTS, ids=lambda e: e["name"])
def test_planets_match_horizons(entry):
    chart = _cast(entry)
    aya = chart["metadata"]["ayanamsha_degrees"]
    for name, tropical in entry["horizons_tropical"].items():
        delta = (_sidereal_absolute(chart["planets"][name]) + aya - tropical + 180) % 360 - 180
        assert abs(delta) <= 0.05, f"{entry['name']} {name}: {delta:+.4f} deg"


def test_ayanamsha_j2000_pin():
    chart = dashaflow.cast_chart(
        "2000-01-01", "12:00", 28.6139, 77.2090, "UTC")
    # Installed backend: 23.857092; report pin: 23.853222; rung absorbs the 0.0039 gap.
    assert abs(chart["metadata"]["ayanamsha_degrees"] - 23.853222) <= 0.02


@pytest.mark.parametrize("entry", CHARTS, ids=lambda e: e["name"])
def test_categorical_anchors(entry):
    chart = _cast(entry)
    published = entry["published"] or {}
    if "lagna_sign" in published:
        assert chart["lagna"]["sign"] == published["lagna_sign"]
        assert abs(chart["lagna"]["degree"] - published["lagna_degree_in_sign"]) <= 0.50
    if "lagna_nakshatra" in published:
        assert chart["lagna"]["nakshatra"] == published["lagna_nakshatra"]
    if "moon_pada" in published:
        assert chart["planets"]["Moon"]["pada"] == published["moon_pada"]
    for planet, nakshatra in published.get("nakshatras", {}).items():
        assert chart["planets"][planet]["nakshatra"] == nakshatra


def test_variant_metadata_rung():
    entry = next(e for e in CHARTS if e["name"] == "delhi_1975")
    lahiri = _cast(entry)["metadata"]
    raman = _cast(entry, ayanamsha="raman")["metadata"]
    assert raman["ayanamsha_variant"] == "raman"
    assert raman["ayanamsha"] == "Raman"
    assert raman["ayanamsha_degrees"] != lahiri["ayanamsha_degrees"]


def test_raman_shift_matches_ayanamsha_difference():
    entry = next(e for e in CHARTS if e["name"] == "delhi_1975")
    lahiri = _cast(entry)
    raman = _cast(entry, ayanamsha="raman")
    moon_delta = (_sidereal_absolute(raman["planets"]["Moon"])
                  - _sidereal_absolute(lahiri["planets"]["Moon"])) % 360
    # Raman's ayanamsha is smaller, so its sidereal longitudes sit ahead.
    assert abs(moon_delta - 1.4463) < 0.01


def test_separation_guards():
    entry = next(e for e in CHARTS if e["name"] == "raman_standard_horoscope")
    lahiri = _cast(entry)["metadata"]["ayanamsha_degrees"]
    raman = _cast(entry, ayanamsha="raman")["metadata"]["ayanamsha_degrees"]
    icrc = _cast(entry, ayanamsha="lahiri_icrc")["metadata"]["ayanamsha_degrees"]
    citra = _cast(entry, ayanamsha="true_citra")["metadata"]["ayanamsha_degrees"]
    assert abs(lahiri - raman) >= 1.0
    assert abs(lahiri - icrc) <= 0.01
    assert abs(lahiri - citra) <= 0.05


@pytest.mark.parametrize("entry", CHARTS, ids=lambda e: e["name"])
def test_vimshottari_formula_invariant(entry):
    chart = _cast(entry)
    moon = chart["planets"]["Moon"]
    timeline = chart["dashas"]["timeline"]
    lord = moon["nakshatra_lord"]
    assert timeline[0]["planet"] == lord

    moon_abs = _sidereal_absolute(moon)
    nak_idx = int(moon_abs / NAK_SPAN)
    remaining = 1 - (moon_abs - nak_idx * NAK_SPAN) / NAK_SPAN
    expected_days = VIMSHOTTARI_YEARS[lord] * SIDEREAL_YEAR_DAYS * remaining
    actual_days = (
        datetime.date.fromisoformat(timeline[0]["end"])
        - datetime.date.fromisoformat(timeline[0]["start"])).days
    assert abs(actual_days - expected_days) <= 1.0

    for earlier, later in zip(timeline, timeline[1:], strict=False):
        assert earlier["end"] == later["start"]
