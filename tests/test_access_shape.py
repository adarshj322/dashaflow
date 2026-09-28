"""Tests for summarize_chart — compact chart projection for AI consumers."""

import json

import dashaflow
from dashaflow import summarize_chart


def _chart():
    return dashaflow.cast_chart(
        "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
        query_date="2026-01-01",
    )


class TestSummarizeChartCompact:
    def test_compact_under_4kb(self):
        compact = summarize_chart(_chart())
        size = len(json.dumps(compact).encode("utf-8"))
        assert size < 4096, f"compact chart is {size} bytes, want < 4096"

    def test_compact_has_five_sections(self):
        compact = summarize_chart(_chart())
        for section in ("lagna", "planets", "dashas", "yogas", "strengths"):
            assert section in compact

    def test_compact_planets_condensed(self):
        compact = summarize_chart(_chart())
        moon = compact["planets"]["Moon"]
        assert set(moon) <= {"sign", "house", "nakshatra", "dignity"}
        assert moon["sign"] == "Scorpio"

    def test_compact_dashas_active_lords_only(self):
        compact = summarize_chart(_chart())
        dashas = compact["dashas"]
        assert dashas["vimshottari"]["maha"] == "Moon"
        assert "timeline" not in dashas["vimshottari"]
        assert "yogini" in dashas and "chara" in dashas

    def test_compact_yogas_names_only(self):
        compact = summarize_chart(_chart())
        assert isinstance(compact["yogas"], list)
        assert all(isinstance(y, str) for y in compact["yogas"])
        assert "Budhaditya Yoga" in compact["yogas"]

    def test_full_returns_chart_unchanged(self):
        chart = _chart()
        assert summarize_chart(chart, detail="full") == chart


class TestGetDashaPeriods:
    def test_full_chains_all_three_systems(self):
        from dashaflow import get_dasha_periods

        periods = get_dasha_periods(_chart())
        assert set(periods) == {"vimshottari", "yogini", "chara"}
        assert periods["vimshottari"]["maha"]["planet"] == "Moon"
        assert len(periods["vimshottari"]["timeline"]) > 5
        assert periods["yogini"]["maha"]["yogini"]
        assert periods["chara"]["maha"]["sign"]


class TestGetStrengthTable:
    def test_all_components(self):
        from dashaflow import get_strength_table

        table = get_strength_table(_chart())
        assert set(table["Sun"]) >= {"shadbala_rupas", "vimshopaka", "vimshopaka_band"}
        assert table["Sun"]["shadbala_rupas"] > 0
        assert table["Sun"]["vimshopaka_band"] in (
            "nil", "weak", "medium", "full", "extra")


class TestGetYogaList:
    def test_full_entries(self):
        from dashaflow import get_yoga_list

        yogas = get_yoga_list(_chart())
        assert isinstance(yogas, list) and yogas
        assert all({"name", "formed_by"} <= set(y) for y in yogas)


class TestCastChartsBatch:
    def test_batch_equivalence(self):
        births = [
            ("1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata"),
            ("1918-10-16", "14:20", 12.9716, 77.5946, "Asia/Kolkata"),
        ]
        results = dashaflow.cast_charts(births, query_date="2026-01-01")
        assert len(results) == 2
        for (dob, t, la, lo, tz), chart in zip(births, results):
            single = dashaflow.cast_chart(dob, t, la, lo, tz, query_date="2026-01-01")
            single["metadata"].pop("computed_at_utc")
            chart["metadata"].pop("computed_at_utc")
            assert chart == single

    def test_batch_empty(self):
        assert dashaflow.cast_charts([]) == []
