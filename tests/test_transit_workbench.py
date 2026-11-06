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
