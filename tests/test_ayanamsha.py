import pytest
import swisseph as swe

import dashaflow
from dashaflow import InvalidInputError
from dashaflow._ayanamsha import AYANAMSHA_VARIANTS, resolve_ayanamsha
from dashaflow._validation import validate_ayanamsha
from dashaflow.vedic_calculator import calculate_vedic_chart

EXPECTED = {
    "lahiri": ("Lahiri", swe.SIDM_LAHIRI),
    "lahiri_icrc": ("Lahiri-ICRC", swe.SIDM_LAHIRI_ICRC),
    "true_citra": ("True Citra", swe.SIDM_TRUE_CITRA),
    "raman": ("Raman", swe.SIDM_RAMAN),
    "krishnamurti": ("Krishnamurti (KP old)", swe.SIDM_KRISHNAMURTI),
    "krishnamurti_vp291": ("Krishnamurti VP291 (KP new)", swe.SIDM_KRISHNAMURTI_VP291),
    "yukteshwar": ("Yukteshwar", swe.SIDM_YUKTESHWAR),
    "fagan_bradley": ("Fagan-Bradley", swe.SIDM_FAGAN_BRADLEY),
}


def test_variant_table_complete():
    assert AYANAMSHA_VARIANTS == EXPECTED


@pytest.mark.parametrize("value,key", [
    (None, "lahiri"), ("", "lahiri"), ("Lahiri", "lahiri"), ("LAHIRI", "lahiri"),
    ("lahiri-icrc", "lahiri_icrc"), ("icrc", "lahiri_icrc"),
    ("true chitra", "true_citra"), ("true_chitra", "true_citra"),
    ("kp", "krishnamurti"), ("kp_old", "krishnamurti"),
    ("kp_new", "krishnamurti_vp291"), ("kp_vp291", "krishnamurti_vp291"),
    ("yukteshvara", "yukteshwar"), ("fagan-bradley", "fagan_bradley"),
])
def test_resolution_and_aliases(value, key):
    assert resolve_ayanamsha(value)[0] == key


@pytest.mark.parametrize("bad", ["xyz", 42, object()])
def test_unknown_rejected(bad):
    with pytest.raises(InvalidInputError, match="Unknown ayanamsha"):
        resolve_ayanamsha(bad)


def test_error_lists_all_options():
    with pytest.raises(InvalidInputError) as exc:
        resolve_ayanamsha("xyz")
    for key in AYANAMSHA_VARIANTS:
        assert key in str(exc.value)


def test_validate_accepts_and_rejects():
    validate_ayanamsha("raman")
    with pytest.raises(InvalidInputError):
        validate_ayanamsha("nope")


DELHI_1975 = ("1975-01-15", "09:00", 28.6139, 77.2090, "Asia/Kolkata")
DELHI_1990 = ("1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")
DELHI_1990_CUSP = ("1990-04-15", "11:35", 28.6139, 77.2090, "Asia/Kolkata")


def test_default_metadata_unchanged():
    chart = calculate_vedic_chart(
        "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")
    assert chart["metadata"]["ayanamsha"] == "Lahiri"
    assert chart["metadata"]["ayanamsha_variant"] == "lahiri"
    assert chart["metadata"]["ayanamsha_degrees"] == 23.7214


def test_raman_metadata_and_ayanamsha():
    chart = calculate_vedic_chart(*DELHI_1975, ayanamsha="raman")
    assert chart["metadata"]["ayanamsha"] == "Raman"
    assert chart["metadata"]["ayanamsha_variant"] == "raman"
    assert abs(chart["metadata"]["ayanamsha_degrees"] - 22.0621) < 0.001


def test_raman_flips_cusp_chart():
    # Raman's ayanamsha is smaller, so its sidereal longitudes run ~1.4463 deg ahead.
    lahiri = calculate_vedic_chart(*DELHI_1990_CUSP)
    raman = calculate_vedic_chart(*DELHI_1990_CUSP, ayanamsha="raman")
    assert lahiri["lagna"]["sign"] == "Gemini"
    assert raman["lagna"]["sign"] == "Cancer"


def test_invalid_variant_rejected_by_direct_caller():
    with pytest.raises(InvalidInputError, match="Unknown ayanamsha"):
        calculate_vedic_chart(*DELHI_1975, ayanamsha="nope")


def test_sav_invariant_survives_variant():
    assert calculate_vedic_chart(*DELHI_1975, ayanamsha="raman")["ashtakavarga"]["total_bindus"] == 337


def test_cast_chart_variant_pass_through():
    chart = dashaflow.cast_chart(*DELHI_1990_CUSP, ayanamsha="raman")
    assert chart["metadata"]["ayanamsha_variant"] == "raman"
    assert chart["lagna"]["sign"] == "Cancer"


def test_cast_chart_invalid_variant():
    with pytest.raises(InvalidInputError, match="Unknown ayanamsha"):
        dashaflow.cast_chart(*DELHI_1975, ayanamsha="nope")


def test_cast_charts_shared_variant():
    births = [DELHI_1975, ("1995-06-15", "14:30", 19.0760, 72.8777, "Asia/Kolkata")]
    charts = dashaflow.cast_charts(births, ayanamsha="raman")
    assert [c["metadata"]["ayanamsha_variant"] for c in charts] == ["raman", "raman"]


def test_every_natal_api_forwards_variant(monkeypatch):
    calls = []
    real = dashaflow.calculate_vedic_chart

    def recording(*args, **kwargs):
        calls.append(kwargs.get("ayanamsha"))
        return real(*args, **kwargs)

    monkeypatch.setattr(dashaflow, "calculate_vedic_chart", recording)

    dashaflow.calculate_compatibility(
        "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
        "1995-06-15", "14:30", 19.0760, 72.8777, "Asia/Kolkata",
        ayanamsha="raman")
    assert calls == ["raman", "raman"]

    calls.clear()
    dashaflow.check_muhurtha("travel", "2026-06-15", "10:00",
                             28.6139, 77.2090, "Asia/Kolkata", ayanamsha="raman")
    assert calls == ["raman"]

    calls.clear()
    dashaflow.analyze_career(*DELHI_1975, ayanamsha="raman")
    assert calls == ["raman"]


def test_time_sensitivity_forwards_variant(monkeypatch):
    import dashaflow.sensitivity as sensitivity

    seen = []
    real = sensitivity.calculate_vedic_chart

    def recording(*args, **kwargs):
        seen.append(kwargs.get("ayanamsha"))
        return real(*args, **kwargs)

    monkeypatch.setattr(sensitivity, "calculate_vedic_chart", recording)
    dashaflow.get_time_sensitivity(*DELHI_1990, ayanamsha="raman")
    assert seen == ["raman", "raman", "raman"]

    with pytest.raises(InvalidInputError, match="Unknown ayanamsha"):
        dashaflow.get_time_sensitivity(*DELHI_1990, ayanamsha="nope")
