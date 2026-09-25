"""Unit tests for matchmaking, muhurtha, career, shadbala, yoga singles,
panchang edges, dignity compound grades, and dasha input handling."""

import datetime

import dashaflow
from dashaflow.career import analyze_career
from dashaflow.constants import ZODIAC_SIGNS
from dashaflow.dasha import calculate_dashas
from dashaflow.dignity import get_compound_relationship, get_dignity
from dashaflow.matchmaking import (
    calc_bad_constellations,
    calc_bhakoot,
    calc_gana,
    calc_graha_maitri,
    calc_kuja_dosha,
    calc_lagna_house7,
    calc_mahendra,
    calc_nadi,
    calc_rajju,
    calc_sex_energy,
    calc_stree_deergha,
    calc_tara,
    calc_varna,
    calc_vashya,
    calc_vedha,
    calc_yoni,
    calculate_ashtakoot,
    match_kuja_dosha,
)
from dashaflow.muhurtha import evaluate_muhurtha
from dashaflow.panchang import calculate_panchang
from dashaflow.shadbala import (
    _chesta_bala,
    _dig_bala,
    _drik_bala,
    _kala_bala,
    _uchcha_bala,
    calculate_shadbala,
)
from dashaflow.yoga import detect_yogas


def _yp(signs, houses, dignities=None, combust=None, retro=None):
    """Minimal planets_for_yoga-style dict with REAL schema (sign names)."""
    out = {}
    for name, sign in signs.items():
        idx = ZODIAC_SIGNS.index(sign)
        out[name] = {
            "sign": sign,
            "sign_idx": idx,
            "house": houses.get(name, 1),
            "dignity": (dignities or {}).get(name, "neutral"),
            "is_combust": (combust or {}).get(name, False),
            "is_retrograde": (retro or {}).get(name, False),
        }
    return out


class TestAshtakootKutas:
    def test_varna(self):
        assert calc_varna("Cancer", "Aries") == 1.0  # 1 <= 2
        assert calc_varna("Aries", "Cancer") == 0.0

    def test_vashya_same_sign(self):
        assert calc_vashya("Leo", "Leo") == 2.0

    def test_tara(self):
        assert calc_tara(0, 0) == 3.0
        assert calc_tara(0, 2) == 1.5  # male-to-female inauspicious only

    def test_yoni(self):
        assert calc_yoni(0, 0) == 4.0
        assert calc_yoni(0, 12) == 0.0  # Horse vs Buffalo enemies
        assert calc_yoni(0, 3) == 2.0  # Horse vs Serpent neutral

    def test_graha_maitri(self):
        assert calc_graha_maitri("Aries", "Aries") == 5.0  # same lord Mars
        assert calc_graha_maitri("Aries", "Taurus") == 3.0  # neutral both ways

    def test_gana(self):
        assert calc_gana(0, 4) == 6.0  # Deva-Deva
        assert calc_gana(2, 1) == 0.0  # Rakshasa male, Manushya female

    def test_bhakoot(self):
        assert calc_bhakoot("Aries", "Aries") == 7.0
        assert calc_bhakoot("Aries", "Taurus") == 0.0

    def test_nadi(self):
        assert calc_nadi(0, 0) == 0.0
        assert calc_nadi(0, 1) == 8.0

    def test_mahendra_stree_deergha(self):
        assert calc_mahendra(3, 0) == "good"
        assert calc_mahendra(0, 0) == "bad"
        assert calc_stree_deergha(8, 0) == "good"
        assert calc_stree_deergha(0, 0) == "bad"

    def test_vedha(self):
        assert calc_vedha(0, 17) == "bad"
        assert calc_vedha(0, 1) == "good"

    def test_rajju(self):
        assert calc_rajju(0, 8)["result"] == "bad"  # both Pada
        assert calc_rajju(0, 1)["result"] == "good"

    def test_bad_constellations(self):
        bad = calc_bad_constellations(18, 1, 0, 1)
        assert bad["result"] == "bad" and len(bad["issues"]) == 1
        assert calc_bad_constellations(0, 2, 1, 2)["result"] == "good"

    def test_kuja_scoring_and_exceptions(self):
        manglik = {"planets": {"Mars": {"house": 7, "sign": "Aries"}}}
        res = calc_kuja_dosha(manglik)
        assert res["is_manglik"] and res["total_score"] == 60.0  # Mars own, high house
        exempt = {"planets": {"Mars": {"house": 2, "sign": "Gemini"}}}
        assert calc_kuja_dosha(exempt)["total_score"] == 0.0  # Mars exception
        assert calc_kuja_dosha({"planets": {}})["total_score"] == 0.0

    def test_match_kuja_branches(self):
        assert match_kuja_dosha(10, 12)["result"] == "good"
        assert match_kuja_dosha(0, 100)["result"] == "bad"
        assert match_kuja_dosha(100, 90)["result"] == "acceptable"
        assert match_kuja_dosha(100, 0)["result"] == "bad"

    def test_lagna_house7_and_sex_energy(self):
        c1 = {"lagna": {"sign": "Aries"}, "planets": {"Moon": {"sign": "Taurus"}}}
        c2 = {"lagna": {"sign": "Taurus"}, "planets": {"Moon": {"sign": "Aries"}}}
        assert calc_lagna_house7(c1, c2)["result"] == "good"
        s1 = {"planets": {"Mars": {"house": 7}, "Venus": {"house": 1}}}
        s2 = {"planets": {"Mars": {"house": 7}, "Venus": {"house": 2}}}
        assert calc_sex_energy(s1, s2)["result"] == "good"

    def test_top_level_compatibility(self):
        res = dashaflow.calculate_compatibility(
            "1990-04-15", "14:30", 28.61, 77.21, "Asia/Kolkata",
            "1992-08-20", "09:15", 19.07, 72.87, "Asia/Kolkata",
        )
        assert res["max_score"] == 36.0
        assert 0 <= res["total_score"] <= 36.0
        assert "kuja_dosha" in res and "male" in res["kuja_dosha"]

    def test_ashtakoot_direct(self):
        res = calculate_ashtakoot(100.0, 200.0)
        assert set(res["scores"]) == {"Varna", "Vashya", "Tara", "Yoni",
                                      "GrahaMaitri", "Gana", "Bhakoot", "Nadi"}


class TestMuhurthaActivities:
    def _benign(self, **over):
        panchang = {
            "tithi": {"number": 2, "name": "Dwitiya"},
            "vara": {"name": "Monday", "lord": "Moon"},
            "nakshatra": {"name": "Ashwini", "pada": 1, "lord": "Ketu"},
            "yoga": {"index": 1, "name": "Priti"},
            "karana": "Bava",
        }
        panchang.update(over)
        return panchang

    def test_all_activities_return_valid_verdicts(self):
        for activity in ("marriage", "travel", "business", "education", "house_entry", "medical"):
            res = evaluate_muhurtha(activity, self._benign(), {}, "Aries")
            assert res["verdict"] in ("auspicious", "mixed_favorable", "mixed", "inauspicious")
            assert res["score"] >= 0

    def test_mixed_favorable_path(self):
        # 3 positives (tithi, weekday, moon) vs 1 negative (off-list nakshatra).
        p = self._benign(nakshatra={"name": "Bharani", "pada": 1, "lord": "Venus"})
        res = evaluate_muhurtha("business", p, {"Moon": {"sign": "Taurus"}}, None)
        assert res["verdict"] == "mixed_favorable"

    def test_marriage_dosha_hard_reject(self):
        planets = {"Moon": {"sign": "Aries", "house": 1}, "Mars": {"sign": "Aries", "house": 1}}
        res = evaluate_muhurtha("marriage", self._benign(), planets, "Taurus")
        assert res["verdict"] == "inauspicious"
        assert any("DOSHA:" in n for n in res["negative_factors"])


class TestCareerBranches:
    def _planets(self, entries):
        return entries

    def test_empty_tenth_house(self):
        planets = {"Saturn": {"house": 1, "sign": "Aries", "d10_sign": "Aries",
                              "dignity": "neutral", "is_retrograde": False}}
        res = analyze_career(planets, "Aries")  # 10th Capricorn, lord Saturn
        assert res["tenth_house"]["occupants"] == []
        assert "Saturn" in res["primary_planets"]

    def test_dusthana_and_d10_strong(self):
        planets = {
            "Saturn": {"house": 8, "sign": "Leo", "d10_sign": "Capricorn",
                       "dignity": "neutral", "is_retrograde": False},
            "Mars": {"house": 1, "sign": "Aries", "d10_sign": "Aries",
                     "dignity": "own_sign", "is_retrograde": False},
        }
        res = analyze_career(planets, "Aries")
        assert any("dusthana" in f for f in res["strength_factors"])
        assert "Mars" in res["d10_strong_planets"]

    def test_sixth_lord_in_tenth(self):
        planets = {
            "Mercury": {"house": 10, "sign": "Capricorn", "d10_sign": "Gemini",
                        "dignity": "neutral", "is_retrograde": False},
            "Saturn": {"house": 1, "sign": "Aries", "d10_sign": "Aries",
                       "dignity": "neutral", "is_retrograde": False},
        }
        res = analyze_career(planets, "Aries")  # 6th Virgo lord Mercury in 10th
        assert any("6th lord" in f for f in res["strength_factors"])
        assert "Mercury" in res["tenth_house"]["occupants"]

    def test_missing_d10_sign_skipped(self):
        planets = {"Saturn": {"house": 1, "sign": "Aries", "dignity": "neutral"}}
        res = analyze_career(planets, "Aries")
        assert res["d10_indicators"] == {}


class TestShadbalaUnits:
    def test_uchcha_extremes(self):
        assert _uchcha_bala("Sun", 10.0) == 60.0  # deep exaltation Aries 10°
        assert _uchcha_bala("Sun", 190.0) == 0.0  # deep debilitation Libra 10°

    def test_dig_extremes(self):
        assert _dig_bala("Sun", 10) == 60.0
        assert _dig_bala("Sun", 4) == 0.0  # opposite house
        assert _dig_bala("Rahu", 1) == 0.0  # nodes have no digbala

    def test_chesta_bands(self):
        assert _chesta_bala("Mars", -0.5, True) == 60.0
        assert _chesta_bala("Mars", 0.001, False) == 45.0  # near-stationary
        assert _chesta_bala("Mars", 0.524, False) == 30.0  # avg speed
        assert _chesta_bala("Sun", 1.0, False) == 30.0
        assert _chesta_bala("Rahu", -0.05, True) == 0.0

    def test_kala_day_night(self):
        day = _kala_bala("Sun", True, 0.0, 100.0)
        night = _kala_bala("Sun", False, 0.0, 100.0)
        assert day > night  # Sun gains Natonnata by day

    def test_drik_bounded(self):
        planets = {
            "Sun": {"sign": "Aries"},
            "Jupiter": {"sign": "Libra"},  # 7th aspect on Sun
            "Saturn": {"sign": "Aries"},
        }
        score = _drik_bala("Sun", 1, planets)
        assert 0.0 <= score <= 60.0

    def test_full_output_shape(self):
        chart = dashaflow.cast_chart("1990-04-15", "14:30", 28.61, 77.21,
                                     "Asia/Kolkata", query_date="2026-01-01")
        sh = calculate_shadbala(chart["planets"],
                                {p: {"lon": 0.0, "sign_idx": 0, "speed": 0.0} for p in
                                 ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]},
                                True)
        assert set(sh) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert all("ishta_phala" in v and "required_rupas" in v for v in sh.values())


class TestYogaSingles:
    def _names(self, yogas):
        return [y["name"] for y in yogas]

    def test_adhi(self):
        p = _yp({"Moon": "Aries", "Mercury": "Virgo", "Jupiter": "Libra",
                 "Venus": "Scorpio", "Mars": "Gemini", "Saturn": "Cancer"},
                {"Moon": 1, "Mercury": 6, "Jupiter": 7, "Venus": 10, "Mars": 3, "Saturn": 4})
        assert "Adhi Yoga" in self._names(detect_yogas(p, "Aries"))

    def test_chandra_mangal(self):
        p = _yp({"Moon": "Scorpio", "Mars": "Scorpio"}, {"Moon": 1, "Mars": 1})
        assert "Chandra-Mangal Yoga" in self._names(detect_yogas(p, "Aries"))

    def test_gajakesari_weakened_note(self):
        p = _yp({"Moon": "Aries", "Jupiter": "Cancer"}, {"Moon": 1, "Jupiter": 4},
                dignities={"Jupiter": "debilitated"})
        yogas = detect_yogas(p, "Leo")
        gaja = [y for y in yogas if y["name"] == "Gajakesari Yoga"]
        assert len(gaja) == 1 and "weakened" in gaja[0]["description"]

    def test_budhaditya_suppressed_when_debilitated(self):
        p = _yp({"Sun": "Virgo", "Mercury": "Virgo"}, {"Sun": 1, "Mercury": 1},
                dignities={"Mercury": "debilitated"})
        assert "Budhaditya Yoga" not in self._names(detect_yogas(p, "Aries"))

    def test_sunapha_anapha_durudhura(self):
        assert "Sunapha Yoga" in self._names(detect_yogas(
            _yp({"Moon": "Aries", "Mars": "Taurus"}, {"Moon": 5, "Mars": 6}), "Leo"))
        assert "Anapha Yoga" in self._names(detect_yogas(
            _yp({"Moon": "Aries", "Mars": "Pisces"}, {"Moon": 5, "Mars": 6}), "Leo"))
        assert "Durudhura Yoga" in self._names(detect_yogas(
            _yp({"Moon": "Aries", "Mars": "Taurus", "Venus": "Pisces"},
                {"Moon": 5, "Mars": 6, "Venus": 4}), "Leo"))

    def test_veshi_voshi_ubhayachari(self):
        assert "Veshi Yoga" in self._names(detect_yogas(
            _yp({"Sun": "Aries", "Mars": "Taurus"}, {"Sun": 1, "Mars": 2}), "Aries"))
        assert "Voshi Yoga" in self._names(detect_yogas(
            _yp({"Sun": "Taurus", "Mars": "Aries"}, {"Sun": 2, "Mars": 1}), "Aries"))
        assert "Ubhayachari Yoga" in self._names(detect_yogas(
            _yp({"Sun": "Taurus", "Mars": "Gemini", "Venus": "Aries"},
                {"Sun": 2, "Mars": 3, "Venus": 1}), "Aries"))

    def test_amala(self):
        p = _yp({"Venus": "Capricorn"}, {"Venus": 10})
        assert "Amala Yoga" in self._names(detect_yogas(p, "Aries"))

    def test_saraswati_and_lakshmi(self):
        p = _yp({"Jupiter": "Cancer", "Venus": "Taurus", "Mercury": "Libra"},
                {"Jupiter": 4, "Venus": 2, "Mercury": 7},
                dignities={"Jupiter": "exalted"})
        names = self._names(detect_yogas(p, "Aries"))
        assert "Saraswati Yoga" in names
        p2 = _yp({"Jupiter": "Sagittarius", "Venus": "Libra"},
                 {"Jupiter": 9, "Venus": 7},
                 dignities={"Jupiter": "own_sign"})
        assert "Lakshmi Yoga" in self._names(detect_yogas(p2, "Aries"))

    def test_viparita_and_neecha_bhanga(self):
        # Lagna Aries: 6th lord Mercury in 8th (not its own 6th) → Viparita.
        p = _yp({"Mercury": "Scorpio"}, {"Mercury": 8})
        assert "Viparita Raj Yoga" in self._names(detect_yogas(p, "Aries"))
        # Debilitated Venus in Virgo, dispositor Mercury in kendra → Neecha Bhanga.
        p2 = _yp({"Venus": "Virgo", "Mercury": "Cancer"}, {"Venus": 6, "Mercury": 4},
                 dignities={"Venus": "debilitated"})
        assert "Neecha Bhanga Raja Yoga" in self._names(detect_yogas(p2, "Aries"))

    def test_parivartana_maha_and_dhana(self):
        p = _yp({"Mars": "Taurus", "Venus": "Aries"}, {"Mars": 10, "Venus": 9})
        names = self._names(detect_yogas(p, "Leo"))
        assert any("Parivartana Yoga (Maha)" in n for n in names)
        p2 = _yp({"Venus": "Aries", "Saturn": "Cancer"}, {"Venus": 1, "Saturn": 4})
        assert "Dhana Yoga" in self._names(detect_yogas(p2, "Aries"))

    def test_raj_dual_lord(self):
        # Lagna Taurus: Saturn rules 9th + 10th; placed in kendra → Raj Yoga.
        p = _yp({"Saturn": "Scorpio"}, {"Saturn": 7})
        assert "Raj Yoga" in self._names(detect_yogas(p, "Taurus"))


class TestPanchangEdges:
    def test_vara_known_saturday(self):
        p = calculate_panchang(2451545.0, 0.0, 3.0)
        assert p["vara"]["name"] == "Saturday"

    def test_tithi_and_karana_boundaries(self):
        p = calculate_panchang(2451545.0, 0.0, 3.0)  # diff 3°
        assert p["tithi"]["name"] == "Pratipada" and p["tithi"]["paksha"] == "Shukla"
        assert p["karana"] == "Kimstughna"  # first half of Shukla Pratipada
        p2 = calculate_panchang(2451545.0, 0.0, 345.0)  # karana 57
        assert p2["karana"] == "Shakuni"

    def test_yoga_zero(self):
        p = calculate_panchang(2451545.0, 0.0, 0.0)
        assert p["yoga"]["name"] == "Vishkambha"


class TestDignityCompound:
    def test_great_friend_and_enemy(self):
        # Mercury in Libra (friend lord Venus); Venus placed 2nd from Mercury → great_friend.
        assert get_compound_relationship(
            "Mercury", "Libra", {"Mercury": 6, "Venus": 7}) == "great_friend"
        # Mars in Gemini (enemy lord Mercury); Mercury conjoined → great_enemy.
        assert get_compound_relationship(
            "Mars", "Gemini", {"Mars": 2, "Mercury": 2}) == "great_enemy"

    def test_natural_fallback_without_signs(self):
        assert get_dignity("Sun", "Sagittarius", 10.0) == "friend"  # Jupiter friend
        assert get_dignity("Sun", "Libra", 10.0) == "debilitated"


class TestDashaInputs:
    def test_tz_aware_and_lon_wrap(self):
        import pytz
        tz = pytz.timezone("Asia/Kolkata")
        birth = tz.localize(datetime.datetime(1990, 4, 15, 14, 30))
        query = tz.localize(datetime.datetime(2000, 1, 1))
        d = calculate_dashas(100.0, birth, query)
        assert d["maha"] is not None
        d2 = calculate_dashas(100.0 + 720.0, datetime.datetime(1990, 4, 15), query)
        assert d2["maha"]["planet"] == d["maha"]["planet"]

    def test_non_datetime_rejected(self):
        import pytest
        with pytest.raises(ValueError):
            calculate_dashas(100.0, "1990-04-15")


class TestMuhurthaMissingData:
    def _benign(self, **over):
        panchang = {
            "tithi": {"number": 2, "name": "Dwitiya"},
            "vara": {"name": "Monday", "lord": "Moon"},
            "nakshatra": {"name": "Ashwini", "pada": 1, "lord": "Ketu"},
            "yoga": {"index": 1, "name": "Priti"},
            "karana": "Bava",
        }
        panchang.update(over)
        return panchang

    def test_missing_vara_not_penalized(self):
        p = self._benign()
        del p["vara"]
        res = evaluate_muhurtha("business", p, {"Moon": {"sign": "Taurus"}}, None)
        assert res["verdict"] == "auspicious"
        assert not any("Weekday" in n for n in res["negative_factors"])

    def test_missing_moon_not_penalized(self):
        res = evaluate_muhurtha("business", self._benign(), {}, None)
        assert res["verdict"] == "auspicious"
        assert not any("Moon in" in n for n in res["negative_factors"])

    def test_no_sagraha_without_moon(self):
        res = evaluate_muhurtha("marriage", self._benign(),
                                {"Mars": {"sign": "", "house": 1}}, "Taurus")
        assert not any("Sagraha" in n for n in res["negative_factors"])

    def test_lagna_typo_raises(self):
        import pytest

        from dashaflow import InvalidInputError
        with pytest.raises(InvalidInputError):
            evaluate_muhurtha("travel", self._benign(), {}, "Tauras")


class TestContractRoundingArtifact:
    def test_degree_30_tolerated(self):
        import copy

        import dashaflow
        from dashaflow.vedic_calculator import _validate_chart_contract
        chart = dashaflow.cast_chart("1990-04-15", "14:30", 28.61, 77.21,
                                     "Asia/Kolkata", query_date="2026-01-01")
        mutated = copy.deepcopy(chart)
        mutated["planets"]["Sun"]["degree"] = 30.0  # round(x, 2) artifact sliver
        _validate_chart_contract(mutated)  # must not raise


class TestFailFastEntries:
    def test_jaimini_precise_only_entry(self):
        from dashaflow.jaimini import calculate_jaimini_karakas
        pd = {p: {"degree_precise": 10.0 + i, "sign": "Aries", "house": 1,
                  "d9_sign": "Taurus"}
              for i, p in enumerate(["Sun", "Moon", "Mars", "Mercury",
                                     "Jupiter", "Venus", "Saturn"])}
        k = calculate_jaimini_karakas(pd)
        assert k["Atmakaraka"]["planet"] == "Saturn"  # highest precise degree

    def test_jaimini_non_dict_entry(self):
        import pytest
        from dashaflow.jaimini import calculate_jaimini_karakas
        with pytest.raises(ValueError):
            calculate_jaimini_karakas({"Sun": "not-a-dict"})

    def test_kuja_absent_vs_corrupt(self):
        import pytest
        from dashaflow import InvalidInputError
        from dashaflow.matchmaking import calc_kuja_dosha
        assert calc_kuja_dosha({"planets": {}})["total_score"] == 0.0
        with pytest.raises(InvalidInputError):
            calc_kuja_dosha({"planets": {"Mars": "oops"}})

    def test_sex_energy_corrupt_entry(self):
        import pytest
        from dashaflow import InvalidInputError
        from dashaflow.matchmaking import calc_sex_energy
        with pytest.raises(InvalidInputError):
            calc_sex_energy({"planets": {"Mars": "oops"}}, {"planets": {}})
