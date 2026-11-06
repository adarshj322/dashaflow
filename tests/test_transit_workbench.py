"""Slice 3 transit workbench tests — ingress scanner, Sade Sati, gochara."""

import pytest

import dashaflow
from dashaflow.errors import InvalidInputError

DEMO = dict(dob="1990-04-15", time="14:30", lat=28.6139, lon=77.2090,
            timezone="Asia/Kolkata")


def test_saturn_ingress_anchor_aquarius():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2023-01-01", end_date="2023-02-01",
        bodies=["Saturn"])
    ev = [e for e in out["ingresses"] if e["to_sign"] == "Aquarius"]
    assert len(ev) == 1
    assert ev[0]["from_sign"] == "Capricorn"
    assert ev[0]["date"] in ("2023-01-16", "2023-01-17", "2023-01-18")
    assert ev[0]["house_from_lagna"] == 7
    assert ev[0]["house_from_moon"] == 4


def test_ingress_self_consistency():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2023-01-01", end_date="2025-01-01",
        bodies=["Jupiter", "Saturn", "Rahu"])
    assert out["ingresses"] == sorted(
        out["ingresses"], key=lambda e: (e["instant_utc"], e["planet"]))
    assert all(e["from_sign"] != e["to_sign"] for e in out["ingresses"])


def test_retrograde_reentry_present():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2022-04-01", end_date="2023-02-01",
        bodies=["Saturn"])
    assert any(e["direction"] == "retrograde" for e in out["ingresses"])


def test_ketu_mirrors_rahu():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2023-01-01", end_date="2025-01-01",
        bodies=["Rahu", "Ketu"])
    rahu = [e for e in out["ingresses"] if e["planet"] == "Rahu"]
    ketu = [e for e in out["ingresses"] if e["planet"] == "Ketu"]
    assert len(rahu) == len(ketu)
    for r, k in zip(rahu, ketu, strict=True):
        assert r["instant_utc"] == k["instant_utc"]
        assert k["direction"] == "retrograde"


def test_ingress_local_date_across_utc_midnight():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2026-05-25", end_date="2026-06-10",
        bodies=["Jupiter"])
    ev = [e for e in out["ingresses"] if e["to_sign"] == "Cancer"][0]
    assert ev["instant_utc"].startswith("2026-06-01T20:")
    assert ev["date"] == "2026-06-02"


@pytest.mark.parametrize("kwargs", [
    dict(start_date="2023-02-01", end_date="2023-01-01"),
    dict(start_date="2000-01-01", end_date="2020-01-01"),
    dict(start_date="2023-01-01", end_date="2023-02-01", bodies=["Moon"]),
    dict(start_date="2023-01-01", end_date="2023-02-01", bodies=["Pluto"]),
])
def test_ingress_validation(kwargs):
    with pytest.raises(InvalidInputError):
        dashaflow.get_transit_ingresses(**DEMO, **kwargs)


def test_sade_sati_spans_demo_chart():
    out = dashaflow.get_sade_sati_timeline(
        **DEMO, start_date="2010-01-01", end_date="2022-01-01")
    assert out["natal_moon_sign"] == "Scorpio"
    assert out["active_at_start"] is False
    assert out["active_at_end"] is False
    spans = out["spans"]
    assert spans[0] == {"phase": "rising", "start": "2011-11-15",
                        "end": "2014-11-01", "days": 1083, "gap_days": 80,
                        "in_phase_days": 1003, "interruptions": 1,
                        "starts_before_range": False, "ends_after_range": False}
    assert [s["phase"] for s in spans] == ["rising", "peak", "setting", "peak", "setting"]
    assert spans[-1]["start"] == "2017-10-26"
    assert spans[-1]["end"] == "2020-01-23"


def test_sade_sati_zero_merge_splits_off_gap():
    out = dashaflow.get_sade_sati_timeline(
        **DEMO, start_date="2010-01-01", end_date="2022-01-01",
        merge_gap_days=0)
    rising = [s for s in out["spans"] if s["phase"] == "rising"]
    assert len(rising) == 2
    assert rising[0]["end"] == "2012-05-15"
    assert rising[1]["start"] == "2012-08-04"


def test_sade_sati_clipped_range_flags():
    out = dashaflow.get_sade_sati_timeline(
        **DEMO, start_date="2016-01-01", end_date="2016-12-31")
    span = out["spans"][0]
    assert span["phase"] == "peak"
    assert span["starts_before_range"] is True
    assert span["ends_after_range"] is True
    assert out["active_at_start"] is True
    assert out["active_at_end"] is True


def test_sade_sati_crossings_have_phases():
    out = dashaflow.get_sade_sati_timeline(
        **DEMO, start_date="2017-01-01", end_date="2018-01-01")
    echo = [c for c in out["crossings"] if c["to_phase"] == "peak"]
    assert echo and echo[0]["date"] == "2017-06-21"
    assert echo[0]["from_phase"] == "setting"
    assert echo[0]["direction"] == "retrograde"


def test_sade_sati_negative_merge_gap_rejected():
    with pytest.raises(InvalidInputError):
        dashaflow.get_sade_sati_timeline(
            **DEMO, start_date="2010-01-01", end_date="2011-01-01",
            merge_gap_days=-1)


def test_gochara_jupiter_cancer_mixed():
    out = dashaflow.get_gochara(**DEMO, transit_date="2026-06-02")
    jup = out["planets"]["Jupiter"]
    assert jup["house_from_moon"] == 9
    assert jup["sav_points"] == 19
    assert jup["house_quality"] == "favorable"
    assert jup["weighted_verdict"] == "mixed"
    assert out["sav_average"] == 28.08


def test_gochara_saturn_pisces_unfavorable():
    out = dashaflow.get_gochara(**DEMO, transit_date="2026-06-02")
    sat = out["planets"]["Saturn"]
    assert sat["house_from_moon"] == 5
    assert sat["house_quality"] == "unfavorable"
    assert sat["weighted_verdict"] == "unfavorable"


def test_gochara_node_notes_label_raman():
    out = dashaflow.get_gochara(**DEMO, transit_date="2026-06-02")
    assert any("Raman convention (nodes)" in n for n in out["planets"]["Rahu"]["notes"])
    assert all("Raman convention" not in n for n in out["planets"]["Sun"]["notes"])
