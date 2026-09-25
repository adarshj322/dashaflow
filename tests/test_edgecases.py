"""Edge-case and correctness tests for Phase 3 astro fixes."""

import datetime

import pytest

from dashaflow import InvalidInputError
from dashaflow.ashtakavarga import calculate_ashtakavarga
from dashaflow.dasha import SIDEREAL_YEAR_DAYS, calculate_dashas
from dashaflow.jaimini import calculate_jaimini_karakas
from dashaflow.yoga import detect_graha_yuddha, detect_kaal_sarpa, detect_yogas


def _planets(signs, houses=None, dignities=None, combust=None):
    out = {}
    for name, sign in signs.items():
        out[name] = {
            "sign": sign,
            "sign_idx": sign,
            "house": (houses or {}).get(name, 1),
            "dignity": (dignities or {}).get(name, "neutral"),
            "is_combust": (combust or {}).get(name, False),
        }
    return out


class TestDashaEdgeCases:
    def test_sidereal_year_constant(self):
        assert abs(SIDEREAL_YEAR_DAYS - 365.2563) < 1e-9

    def test_query_before_birth_returns_nones(self):
        d = calculate_dashas(100.0, datetime.datetime(1990, 4, 15),
                             datetime.datetime(1980, 1, 1))
        assert d["maha"] is None and d["antar"] is None
        assert d["timeline"][0]["planet"] is not None

    def test_query_beyond_120_years_returns_nones(self):
        d = calculate_dashas(100.0, datetime.datetime(1900, 1, 1),
                             datetime.datetime(2050, 1, 1))
        assert d["maha"] is None

    def test_invalid_moon_longitude(self):
        import pytest
        with pytest.raises(ValueError):
            calculate_dashas(float("nan"), datetime.datetime(1990, 1, 1))
        with pytest.raises(ValueError):
            calculate_dashas("bad", datetime.datetime(1990, 1, 1))

    def test_output_json_serializable(self):
        import json
        d = calculate_dashas(100.0, datetime.datetime(1990, 4, 15),
                             datetime.datetime(2000, 1, 1))
        json.dumps(d)  # must not raise (no datetime objects leaked)


class TestKemadrumaCancellation:
    def test_bhanga_by_kendra_planet(self):
        # Moon Aries(0); Mars Taurus(1) is 2nd from Moon → support, so no yoga anyway.
        # Instead: no 2nd/12th support but Jupiter in kendra (Cancer=3, 4th from Moon).
        planets = _planets(
            {"Moon": 0, "Mars": 5, "Mercury": 6, "Jupiter": 3, "Venus": 8, "Saturn": 9,
             "Sun": 11, "Rahu": 2, "Ketu": 8},
            houses={"Moon": 1, "Mars": 6, "Mercury": 7, "Jupiter": 4, "Venus": 9,
                    "Saturn": 10, "Sun": 12, "Rahu": 3, "Ketu": 9},
        )
        # 2nd from Moon = Taurus(1): empty; 12th = Pisces(11): Sun excluded → no support
        yogas = detect_yogas(planets, "Aries")
        names = [y["name"] for y in yogas]
        # Jupiter in kendra from Moon → cancelled
        assert "Kemadruma Yoga" not in names

    def test_kemadruma_without_cancellation(self):
        # Moon Aries, no support, no kendra planets from Moon, Moon not in kendra lagna.
        # Kendra from Moon = Aries(0)/Cancer(3)/Libra(6)/Capricorn(9) — avoid all.
        planets = _planets(
            {"Moon": 0, "Mars": 5, "Mercury": 7, "Jupiter": 8, "Venus": 10, "Saturn": 2,
             "Sun": 11, "Rahu": 4, "Ketu": 10},
            houses={"Moon": 9, "Mars": 6, "Mercury": 7, "Jupiter": 9, "Venus": 10,
                    "Saturn": 11, "Sun": 12, "Rahu": 3, "Ketu": 9},
        )
        yogas = detect_yogas(planets, "Leo")  # Moon Aries vs Leo lagna: house 9, not kendra
        names = [y["name"] for y in yogas]
        assert "Kemadruma Yoga" in names


class TestKaalSarpaLongitude:
    def test_same_sign_as_node_counts_by_longitude(self):
        # Rahu 233°, Mars 228° (same sign, but inside Ketu→Rahu arc) → partial, not full.
        raw = {
            "Sun": {"lon": 179.0, "sign_idx": 5}, "Moon": {"lon": 309.0, "sign_idx": 10},
            "Mars": {"lon": 228.0, "sign_idx": 7}, "Mercury": {"lon": 180.0, "sign_idx": 6},
            "Jupiter": {"lon": 82.0, "sign_idx": 2}, "Venus": {"lon": 169.0, "sign_idx": 5},
            "Saturn": {"lon": 122.0, "sign_idx": 4},
            "Rahu": {"lon": 233.0, "sign_idx": 7}, "Ketu": {"lon": 53.0, "sign_idx": 1},
        }
        ks = detect_kaal_sarpa(raw)
        assert ks is not None and "Partial" in ks["type"]


class TestGrahaYuddhaWinner:
    def test_higher_latitude_wins(self):
        raw = {
            "Mars": {"lon": 50.0, "lat": -1.0, "sign_idx": 1},
            "Mercury": {"lon": 50.5, "lat": 2.0, "sign_idx": 1},
            "Jupiter": {"lon": 90.0, "lat": 0.0, "sign_idx": 3},
            "Venus": {"lon": 120.0, "lat": 0.0, "sign_idx": 4},
            "Saturn": {"lon": 200.0, "lat": 0.0, "sign_idx": 6},
        }
        wars = detect_graha_yuddha(raw)
        assert len(wars) == 1
        assert wars[0]["winner"] == "Mercury"  # higher latitude, not higher longitude
        assert "latitude" in wars[0]["decision"]


class TestJaiminiTies:
    def test_tie_broken_deterministically(self):
        pd = {p: {"degree": 10.0, "sign": "Aries", "house": 1, "d9_sign": "Taurus"}
              for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]}
        k1 = calculate_jaimini_karakas(pd)
        k2 = calculate_jaimini_karakas(dict(reversed(list(pd.items()))))
        assert k1["Atmakaraka"]["planet"] == k2["Atmakaraka"]["planet"] == "Sun"


class TestAshtakavargaValidation:
    def test_bad_index_raises(self):
        import pytest
        with pytest.raises(ValueError):
            calculate_ashtakavarga({"Sun": 12, "Moon": 0, "Mars": 0, "Mercury": 0,
                                    "Jupiter": 0, "Venus": 0, "Saturn": 0}, 0)
        with pytest.raises(ValueError):
            calculate_ashtakavarga({"Sun": 0}, 0)  # missing planets


class TestDashaBoundaryExactness:
    """OCR review: sub-periods tiled rounded `days`, leaving gaps where no
    level resolves. They must tile exact parent spans."""

    def test_no_gaps_across_full_timeline(self):
        birth = datetime.datetime(1990, 4, 15, 14, 30)
        d0 = calculate_dashas(100.0, birth, birth)
        assert d0["maha"] is not None
        # Re-derive internal spans via public timeline dates at day precision,
        # plus exact start instants: every sampled moment must resolve all levels.
        moments = [birth]
        for entry in d0["timeline"]:
            start = datetime.datetime.strptime(entry["start"], "%Y-%m-%d")
            end = datetime.datetime.strptime(entry["end"], "%Y-%m-%d")
            moments += [start, start + datetime.timedelta(seconds=1),
                        end - datetime.timedelta(seconds=1)]
        horizon = birth + datetime.timedelta(days=120 * SIDEREAL_YEAR_DAYS)
        for moment in moments:
            if moment < birth or moment >= horizon:
                continue
            d = calculate_dashas(100.0, birth, moment)
            assert d["maha"] is not None, f"gap at {moment}"
            assert d["antar"] is not None, f"antar gap at {moment}"
            assert d["pratyantar"] is not None, f"pratyantar gap at {moment}"
            assert d["sukshma"] is not None, f"sukshma gap at {moment}"
            assert d["prana"] is not None, f"prana gap at {moment}"

    def test_sub_periods_tile_parent_exactly(self):
        from dashaflow.dasha import _build_sub_periods
        start = datetime.datetime(2000, 1, 1, 6, 30)
        total = 6574.123456  # unrounded span
        subs = _build_sub_periods(start, total, "Rahu")
        assert abs(sum(s["days"] for s in subs) - total) < 0.01
        assert (subs[-1]["_end_dt"] - start).total_seconds() / 86400.0 == pytest.approx(total)


class TestMahapurushaWeaknessNotes:
    def test_retrograde_note_fires(self):
        planets = {
            "Saturn": {"sign": "Libra", "sign_idx": 6, "house": 7,
                       "dignity": "exalted", "is_combust": False, "is_retrograde": True},
        }
        yogas = detect_yogas(planets, "Aries")
        shasha = [y for y in yogas if y["name"] == "Shasha Yoga"]
        assert len(shasha) == 1
        assert "retrograde" in shasha[0]["description"]


class TestDSTErrorTaxonomy:
    def test_nonexistent_local_time_is_invalid_input(self):
        import dashaflow
        # 2026-03-08 02:30 never occurred in America/New_York (spring forward).
        with pytest.raises(InvalidInputError):
            dashaflow.cast_chart("2026-03-08", "02:30", 40.71, -74.0, "America/New_York")

    def test_unrepresentable_transit_noon_is_invalid_input(self):
        import dashaflow
        from dashaflow.vedic_calculator import calculate_transit
        natal = dashaflow.cast_chart("1990-04-15", "14:30", 28.61, 77.21,
                                     "Asia/Kolkata", query_date="2026-01-01")
        # Pacific/Apia skipped 2011-12-30 entirely (date-line jump).
        with pytest.raises(InvalidInputError):
            calculate_transit("2011-12-30", natal, "Pacific/Apia")


class TestGeographicAndTemporalExtremes:
    def test_poles_do_not_crash_and_serialize(self):
        import json

        import dashaflow
        for lat, lon in [(90.0, 0.0), (-90.0, 0.0), (89.9, 10.0)]:
            chart = dashaflow.cast_chart("1990-04-15", "14:30", lat, lon, "UTC",
                                         query_date="2026-01-01")
            json.dumps(chart)  # must stay serializable
            assert chart["lagna"]["sign"]

    def test_unrepresentable_years_raise_invalid_input(self):
        import pytest

        import dashaflow
        from dashaflow import InvalidInputError
        with pytest.raises(InvalidInputError):
            dashaflow.cast_chart("0001-01-01", "12:00", 28.6, 77.2, "Asia/Kolkata")
        with pytest.raises(InvalidInputError):
            dashaflow.cast_chart("9999-12-31", "12:00", 28.6, 77.2, "Asia/Kolkata")
