"""
Comprehensive Test Suite for RishiAI Vedic Astrology MCP Server
================================================================
Tests all modules against KNOWN reference values computed from two horoscopes.

Reference Chart 1: B.V. Raman Standard Horoscope
  Born 16-Oct-1918, 14:20 IST, Bangalore (12.9716N, 77.5946E)
  Cross-validated against VedAstro (Lahiri ayanamsha) reference values.

Reference Chart 2: Delhi Native
  Born 15-Apr-1990, 14:30 IST, Delhi (28.6139N, 77.2090E)

Testing Strategy:
  - Cast charts with known birth data
  - Assert SPECIFIC planetary positions (sign, degree, nakshatra)
  - Assert SPECIFIC dignities, houses, dashas, yogas
  - Cross-validate with B.V. Raman / VedAstro published values
  - Unit-test pure functions (divisional charts, nakshatra math)
"""

import unittest
import datetime

from constants import (
    ZODIAC_SIGNS, SIGN_LORDS, NAKSHATRAS, NAK_SPAN, PADA_SPAN,
    VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL, DASHA_SEQUENCE,
    EXALTATION, DEBILITATION, OWN_SIGNS, MOOLTRIKONA,
    NATURAL_FRIENDS, NATURAL_ENEMIES, COMBUSTION_ORBS,
    TITHI_NAMES, VARA_NAMES, VARA_LORDS, PANCHANG_YOGA_NAMES,
    DIGBALA_HOUSES,
)
from nakshatra import get_nakshatra
from vedic_calculator import (
    get_sign_and_degree, calculate_navamsha, calculate_d2_hora,
    calculate_dashamsha, calculate_d3_drekkana, calculate_d4_chaturthamsha,
    calculate_d7_saptamsha, calculate_d12_dwadashamsha,
    calculate_d16_shodashamsha, calculate_d20_vimshamsha,
    calculate_d24_chaturvimshamsha, calculate_d27_bhamsha,
    calculate_d30_trimshamsha, calculate_d40_khavedamsha,
    calculate_d60_shashtiamsha, get_vedic_aspects, _house_from_lagna,
    calculate_bhava_chalit, calculate_avasthas,
    calculate_vedic_chart,
)
from dignity import get_dignity, check_combustion, get_digbala
from dasha import calculate_dashas
from panchang import calculate_panchang
from ashtakavarga import calculate_ashtakavarga
from jaimini import (
    calculate_jaimini_karakas, calculate_arudha_padas,
    calculate_upapada, calculate_karakamsha,
)
from shadbala import calculate_shadbala
from yoga import detect_yogas, detect_kaal_sarpa, detect_graha_yuddha, detect_gandanta
from matchmaking import calculate_ashtakoot
from muhurtha import evaluate_muhurtha
from career import analyze_career


# ===================================================================
# LAZY CHART CACHING -- cast once, reuse across all tests
# ===================================================================
_BVR_CHART = None
_DELHI_CHART = None


def bvr():
    """B.V. Raman Standard Horoscope (with query_date for dasha context)."""
    global _BVR_CHART
    if _BVR_CHART is None:
        _BVR_CHART = calculate_vedic_chart(
            "1918-10-16", "14:20", 12.9716, 77.5946, "Asia/Kolkata",
            query_date_str="1950-01-01",
        )
    return _BVR_CHART


def delhi():
    """Delhi native chart."""
    global _DELHI_CHART
    if _DELHI_CHART is None:
        _DELHI_CHART = calculate_vedic_chart(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
        )
    return _DELHI_CHART


# ===================================================================
# 1. CONSTANTS VALIDATION -- astrological data tables
# ===================================================================
class TestConstants(unittest.TestCase):

    def test_zodiac_12_signs_aries_to_pisces(self):
        self.assertEqual(len(ZODIAC_SIGNS), 12)
        self.assertEqual(ZODIAC_SIGNS[0], "Aries")
        self.assertEqual(ZODIAC_SIGNS[11], "Pisces")

    def test_sign_lords_all_12(self):
        self.assertEqual(len(SIGN_LORDS), 12)
        self.assertEqual(SIGN_LORDS["Aries"], "Mars")
        self.assertEqual(SIGN_LORDS["Taurus"], "Venus")
        self.assertEqual(SIGN_LORDS["Cancer"], "Moon")
        self.assertEqual(SIGN_LORDS["Leo"], "Sun")
        self.assertEqual(SIGN_LORDS["Sagittarius"], "Jupiter")
        self.assertEqual(SIGN_LORDS["Capricorn"], "Saturn")

    def test_27_nakshatras_ashwini_to_revati(self):
        self.assertEqual(len(NAKSHATRAS), 27)
        self.assertEqual(NAKSHATRAS[0]["name"], "Ashwini")
        self.assertEqual(NAKSHATRAS[0]["lord"], "Ketu")
        self.assertEqual(NAKSHATRAS[26]["name"], "Revati")
        self.assertEqual(NAKSHATRAS[26]["lord"], "Mercury")

    def test_nakshatra_span_13_deg_20_min(self):
        self.assertAlmostEqual(NAK_SPAN, 360.0 / 27.0, places=6)
        self.assertAlmostEqual(PADA_SPAN, NAK_SPAN / 4.0, places=6)

    def test_vimshottari_total_120_years(self):
        self.assertEqual(sum(VIMSHOTTARI_YEARS.values()), 120)
        self.assertEqual(VIMSHOTTARI_TOTAL, 120.0)

    def test_dasha_sequence_ketu_to_mercury(self):
        self.assertEqual(len(DASHA_SEQUENCE), 9)
        self.assertEqual(DASHA_SEQUENCE[0], "Ketu")
        self.assertEqual(DASHA_SEQUENCE[-1], "Mercury")

    def test_exaltation_signs(self):
        self.assertEqual(EXALTATION["Sun"][0], "Aries")
        self.assertEqual(EXALTATION["Moon"][0], "Taurus")
        self.assertEqual(EXALTATION["Mars"][0], "Capricorn")
        self.assertEqual(EXALTATION["Jupiter"][0], "Cancer")
        self.assertEqual(EXALTATION["Venus"][0], "Pisces")
        self.assertEqual(EXALTATION["Saturn"][0], "Libra")

    def test_debilitation_7th_from_exaltation(self):
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            exalt_idx = ZODIAC_SIGNS.index(EXALTATION[planet][0])
            debil_idx = ZODIAC_SIGNS.index(DEBILITATION[planet][0])
            self.assertEqual((exalt_idx + 6) % 12, debil_idx,
                             f"{planet}: debilitation not 7th from exaltation")

    def test_own_signs(self):
        self.assertIn("Leo", OWN_SIGNS["Sun"])
        self.assertIn("Cancer", OWN_SIGNS["Moon"])
        self.assertIn("Aries", OWN_SIGNS["Mars"])
        self.assertIn("Scorpio", OWN_SIGNS["Mars"])

    def test_mooltrikona_in_own_sign(self):
        for planet, (mt_sign, _, _) in MOOLTRIKONA.items():
            self.assertIn(mt_sign, OWN_SIGNS.get(planet, []) +
                          [EXALTATION.get(planet, [None])[0]],
                          f"{planet} mooltrikona {mt_sign} not in own/exalt signs")

    def test_combustion_orbs_keys(self):
        for planet in ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            self.assertIn(planet, COMBUSTION_ORBS)
        self.assertNotIn("Sun", COMBUSTION_ORBS)

    def test_tithi_and_vara_counts(self):
        self.assertEqual(len(TITHI_NAMES), 30)
        self.assertEqual(len(VARA_NAMES), 7)
        self.assertEqual(len(VARA_LORDS), 7)

    def test_digbala_houses(self):
        self.assertEqual(DIGBALA_HOUSES["Sun"], 10)
        self.assertEqual(DIGBALA_HOUSES["Jupiter"], 1)
        self.assertEqual(DIGBALA_HOUSES["Saturn"], 7)
        self.assertEqual(DIGBALA_HOUSES["Moon"], 4)


# ===================================================================
# 2. NAKSHATRA CALCULATION -- pure math tests
# ===================================================================
class TestNakshatra(unittest.TestCase):

    def test_ashwini_at_0_degrees(self):
        nak = get_nakshatra(0.0)
        self.assertEqual(nak["name"], "Ashwini")
        self.assertEqual(nak["pada"], 1)

    def test_revati_at_359(self):
        nak = get_nakshatra(359.99)
        self.assertEqual(nak["name"], "Revati")
        self.assertEqual(nak["pada"], 4)

    def test_magha_at_120(self):
        nak = get_nakshatra(120.5)
        self.assertEqual(nak["name"], "Magha")

    def test_vishakha_at_200(self):
        nak = get_nakshatra(200.0)
        self.assertEqual(nak["name"], "Vishakha")

    def test_wrap_360_to_0(self):
        nak = get_nakshatra(360.0)
        self.assertEqual(nak["name"], "Ashwini")

    def test_pada_boundaries(self):
        span = NAK_SPAN
        pada_span = span / 4
        nak1 = get_nakshatra(pada_span - 0.01)
        self.assertEqual(nak1["pada"], 1)
        nak2 = get_nakshatra(pada_span + 0.01)
        self.assertEqual(nak2["pada"], 2)


# ===================================================================
# 3. SIGN AND DEGREE CONVERSION
# ===================================================================
class TestSignAndDegree(unittest.TestCase):

    def test_aries_start(self):
        sign, deg, idx = get_sign_and_degree(0.0)
        self.assertEqual(sign, "Aries")
        self.assertAlmostEqual(deg, 0.0)
        self.assertEqual(idx, 0)

    def test_taurus_start(self):
        sign, _, idx = get_sign_and_degree(30.0)
        self.assertEqual(sign, "Taurus")
        self.assertEqual(idx, 1)

    def test_leo_middle(self):
        sign, deg, _ = get_sign_and_degree(135.0)
        self.assertEqual(sign, "Leo")
        self.assertAlmostEqual(deg, 15.0)

    def test_pisces_end(self):
        sign, deg, _ = get_sign_and_degree(359.99)
        self.assertEqual(sign, "Pisces")
        self.assertAlmostEqual(deg, 29.99, places=1)

    def test_360_wraps_to_aries(self):
        sign, _, _ = get_sign_and_degree(360.0)
        self.assertEqual(sign, "Aries")


# ===================================================================
# 4. DIVISIONAL CHARTS -- pure function tests
#    Cross-validated against VedAstro D2/D3 for BVR chart
# ===================================================================
class TestDivisionalCharts(unittest.TestCase):

    # --- D2 (Hora) --- VedAstro: Sun=Leo, Moon=Leo, Jupiter=Cancer
    def test_d2_sun_bvr_leo(self):
        """Sun at Virgo 29.46 -> D2 Leo (VedAstro confirmed)."""
        self.assertEqual(calculate_d2_hora(5 * 30 + 29.46), "Leo")

    def test_d2_jupiter_bvr_cancer(self):
        """Jupiter at Gemini 22.56 -> D2 Cancer (VedAstro confirmed)."""
        self.assertEqual(calculate_d2_hora(2 * 30 + 22.56), "Cancer")

    def test_d2_odd_sign_first_half(self):
        self.assertEqual(calculate_d2_hora(5.0), "Leo")

    def test_d2_odd_sign_second_half(self):
        self.assertEqual(calculate_d2_hora(20.0), "Cancer")

    def test_d2_even_sign_first_half(self):
        self.assertEqual(calculate_d2_hora(35.0), "Cancer")

    def test_d2_even_sign_second_half(self):
        self.assertEqual(calculate_d2_hora(50.0), "Leo")

    # --- D3 (Drekkana) --- VedAstro: Sun=Taurus, Moon=Aquarius, Mars=Pisces, Saturn=Leo
    def test_d3_sun_bvr_taurus(self):
        """Sun at Virgo 29.46 -> D3 Taurus (VedAstro confirmed)."""
        self.assertEqual(calculate_d3_drekkana(5 * 30 + 29.46), "Taurus")

    def test_d3_moon_bvr_aquarius(self):
        """Moon at Aquarius 9.77 -> D3 Aquarius (VedAstro confirmed)."""
        self.assertEqual(calculate_d3_drekkana(10 * 30 + 9.77), "Aquarius")

    def test_d3_saturn_bvr_leo(self):
        """Saturn at Leo 2.93 -> D3 Leo (VedAstro confirmed)."""
        self.assertEqual(calculate_d3_drekkana(4 * 30 + 2.93), "Leo")

    def test_d3_mars_bvr_pisces(self):
        """Mars at Scorpio 18.01 -> D3 Pisces (VedAstro confirmed)."""
        self.assertEqual(calculate_d3_drekkana(7 * 30 + 18.01), "Pisces")

    # --- D9 (Navamsha) ---
    def test_navamsha_sun_bvr_virgo(self):
        """Sun at Virgo 29.46 -> D9 Virgo."""
        self.assertEqual(calculate_navamsha(5 * 30 + 29.46), "Virgo")

    def test_navamsha_mercury_bvr_libra(self):
        """Mercury at Libra 0.05 -> D9 Libra."""
        self.assertEqual(calculate_navamsha(6 * 30 + 0.05), "Libra")

    def test_navamsha_vargottama(self):
        """Planet in the same D1 and D9 sign = Vargottama."""
        self.assertEqual(calculate_navamsha(1.0), "Aries")

    # --- D10 (Dashamsha) ---
    def test_d10_odd_sign(self):
        """Aries 5 deg (odd sign, part=1) -> Taurus."""
        self.assertEqual(calculate_dashamsha(5.0), "Taurus")

    def test_d10_even_sign(self):
        """Taurus 5 deg (even sign, part=1) -> Aquarius (idx=1+8+1=10)."""
        self.assertEqual(calculate_dashamsha(35.0), "Aquarius")

    # --- D4 ---
    def test_d4_first_quarter(self):
        self.assertEqual(calculate_d4_chaturthamsha(1.0), "Aries")

    def test_d4_second_quarter(self):
        self.assertEqual(calculate_d4_chaturthamsha(10.0), "Cancer")

    # --- D7 ---
    def test_d7_odd_sign_first(self):
        self.assertEqual(calculate_d7_saptamsha(0.5), "Aries")

    def test_d7_even_sign_first(self):
        self.assertEqual(calculate_d7_saptamsha(30.5), "Scorpio")

    # --- D12 ---
    def test_d12_first_part(self):
        self.assertEqual(calculate_d12_dwadashamsha(1.0), "Aries")

    def test_d12_second_part(self):
        self.assertEqual(calculate_d12_dwadashamsha(3.0), "Taurus")

    # --- D16, D20, D24 ---
    def test_d16_aries_first_part(self):
        self.assertEqual(calculate_d16_shodashamsha(0.5), "Aries")

    def test_d20_aries_first_part(self):
        self.assertEqual(calculate_d20_vimshamsha(0.5), "Aries")

    def test_d24_odd_sign_starts_leo(self):
        self.assertEqual(calculate_d24_chaturvimshamsha(0.5), "Leo")

    def test_d24_even_sign_starts_cancer(self):
        self.assertEqual(calculate_d24_chaturvimshamsha(30.5), "Cancer")

    # --- D27 ---
    def test_d27_fire_sign(self):
        self.assertEqual(calculate_d27_bhamsha(0.5), "Aries")

    def test_d27_earth_sign(self):
        self.assertEqual(calculate_d27_bhamsha(30.5), "Cancer")

    def test_d27_air_sign(self):
        self.assertEqual(calculate_d27_bhamsha(60.5), "Libra")

    def test_d27_water_sign(self):
        self.assertEqual(calculate_d27_bhamsha(90.5), "Capricorn")

    # --- D30 ---
    def test_d30_odd_sign_first_5(self):
        self.assertEqual(calculate_d30_trimshamsha(2.0), "Aries")

    def test_d30_odd_sign_second_5(self):
        self.assertEqual(calculate_d30_trimshamsha(7.0), "Capricorn")

    def test_d30_even_sign_first_5(self):
        self.assertEqual(calculate_d30_trimshamsha(32.0), "Taurus")

    # --- D40 ---
    def test_d40_odd_sign(self):
        self.assertEqual(calculate_d40_khavedamsha(0.3), "Aries")

    def test_d40_even_sign(self):
        self.assertEqual(calculate_d40_khavedamsha(30.3), "Libra")

    # --- D60 ---
    def test_d60_odd_sign(self):
        self.assertEqual(calculate_d60_shashtiamsha(0.2), "Aries")

    def test_d60_even_sign(self):
        self.assertEqual(calculate_d60_shashtiamsha(30.2), "Scorpio")


# ===================================================================
# 5. ASPECTS -- pure function tests
# ===================================================================
class TestAspects(unittest.TestCase):
    """get_vedic_aspects returns a list of sign NAMES (not indices)."""

    def test_mars_special_aspects(self):
        aspects = get_vedic_aspects("Mars", 0)  # Mars in Aries
        self.assertIn("Cancer", aspects)    # 4th
        self.assertIn("Libra", aspects)     # 7th
        self.assertIn("Scorpio", aspects)   # 8th
        self.assertEqual(len(aspects), 3)

    def test_jupiter_special_aspects(self):
        aspects = get_vedic_aspects("Jupiter", 0)  # Jupiter in Aries
        self.assertIn("Leo", aspects)       # 5th
        self.assertIn("Libra", aspects)     # 7th
        self.assertIn("Sagittarius", aspects)  # 9th
        self.assertEqual(len(aspects), 3)

    def test_saturn_special_aspects(self):
        aspects = get_vedic_aspects("Saturn", 0)  # Saturn in Aries
        self.assertIn("Gemini", aspects)    # 3rd
        self.assertIn("Libra", aspects)     # 7th
        self.assertIn("Capricorn", aspects) # 10th
        self.assertEqual(len(aspects), 3)

    def test_sun_only_7th_aspect(self):
        aspects = get_vedic_aspects("Sun", 0)
        self.assertIn("Libra", aspects)     # 7th from Aries
        self.assertEqual(len(aspects), 1)

    def test_rahu_ketu_7th_only(self):
        for node in ["Rahu", "Ketu"]:
            aspects = get_vedic_aspects(node, 0)
            self.assertIn("Libra", aspects)
            self.assertEqual(len(aspects), 1)


# ===================================================================
# 6. HOUSE FROM LAGNA -- pure function
# ===================================================================
class TestHouseFromLagna(unittest.TestCase):

    def test_same_sign_is_house_1(self):
        self.assertEqual(_house_from_lagna(0, 0), 1)

    def test_opposite_is_house_7(self):
        self.assertEqual(_house_from_lagna(6, 0), 7)

    def test_12th_house(self):
        self.assertEqual(_house_from_lagna(11, 0), 12)

    def test_wrap_around(self):
        self.assertEqual(_house_from_lagna(0, 3), 10)


# ===================================================================
# 7. BVR CHART -- PLANETARY POSITIONS (cross-ref VedAstro Lahiri)
#    VedAstro reference: Sun=Virgo 29deg28', Moon=Aquarius 9deg46',
#    Mars=Scorpio 18deg01', Mercury=Libra 0deg04', Jupiter=Gemini 22deg34',
#    Venus=Virgo 19deg43', Saturn=Leo 2deg56'
# ===================================================================
class TestBVRPlanetPositions(unittest.TestCase):
    """Assert planetary signs and degrees against VedAstro Lahiri values.
    Tolerance: 0.5 deg for degrees (minor ephemeris differences)."""

    TOLERANCE = 0.5

    def test_sun_in_virgo_29deg(self):
        sun = bvr()["planets"]["Sun"]
        self.assertEqual(sun["sign"], "Virgo")
        self.assertAlmostEqual(sun["degree"], 29.46, delta=self.TOLERANCE)

    def test_moon_in_aquarius_10deg(self):
        moon = bvr()["planets"]["Moon"]
        self.assertEqual(moon["sign"], "Aquarius")
        self.assertAlmostEqual(moon["degree"], 9.77, delta=self.TOLERANCE)

    def test_mars_in_scorpio_18deg(self):
        mars = bvr()["planets"]["Mars"]
        self.assertEqual(mars["sign"], "Scorpio")
        self.assertAlmostEqual(mars["degree"], 18.01, delta=self.TOLERANCE)

    def test_mercury_in_libra_0deg(self):
        merc = bvr()["planets"]["Mercury"]
        self.assertEqual(merc["sign"], "Libra")
        self.assertAlmostEqual(merc["degree"], 0.05, delta=self.TOLERANCE)

    def test_jupiter_in_gemini_22deg(self):
        jup = bvr()["planets"]["Jupiter"]
        self.assertEqual(jup["sign"], "Gemini")
        self.assertAlmostEqual(jup["degree"], 22.56, delta=self.TOLERANCE)

    def test_venus_in_virgo_20deg(self):
        ven = bvr()["planets"]["Venus"]
        self.assertEqual(ven["sign"], "Virgo")
        self.assertAlmostEqual(ven["degree"], 19.70, delta=self.TOLERANCE)

    def test_saturn_in_leo_3deg(self):
        sat = bvr()["planets"]["Saturn"]
        self.assertEqual(sat["sign"], "Leo")
        self.assertAlmostEqual(sat["degree"], 2.93, delta=self.TOLERANCE)

    def test_rahu_in_scorpio(self):
        self.assertEqual(bvr()["planets"]["Rahu"]["sign"], "Scorpio")

    def test_ketu_opposite_rahu(self):
        c = bvr()
        rahu_idx = ZODIAC_SIGNS.index(c["planets"]["Rahu"]["sign"])
        ketu_idx = ZODIAC_SIGNS.index(c["planets"]["Ketu"]["sign"])
        self.assertEqual((rahu_idx + 6) % 12, ketu_idx)
        self.assertEqual(c["planets"]["Ketu"]["sign"], "Taurus")

    def test_rahu_ketu_always_retrograde(self):
        for node in ["Rahu", "Ketu"]:
            self.assertTrue(bvr()["planets"][node]["is_retrograde"])


# ===================================================================
# 8. BVR CHART -- LAGNA
#    VedAstro: House 1 middle ~294deg57' = Capricorn ~24deg57'
# ===================================================================
class TestBVRLagna(unittest.TestCase):

    def test_lagna_sign_capricorn(self):
        self.assertEqual(bvr()["lagna"]["sign"], "Capricorn")

    def test_lagna_degree_near_25(self):
        self.assertAlmostEqual(bvr()["lagna"]["degree"], 25.35, delta=1.0)

    def test_lagna_nakshatra_dhanishta(self):
        self.assertEqual(bvr()["lagna"]["nakshatra"], "Dhanishta")

    def test_lagna_has_all_varga_signs(self):
        vargas = ["d2_sign", "d3_sign", "d4_sign", "d7_sign", "d9_sign",
                  "d10_sign", "d12_sign", "d16_sign", "d20_sign",
                  "d24_sign", "d27_sign", "d30_sign", "d40_sign", "d60_sign"]
        for v in vargas:
            self.assertIn(bvr()["lagna"][v], ZODIAC_SIGNS)

    def test_lagna_d9_leo(self):
        self.assertEqual(bvr()["lagna"]["d9_sign"], "Leo")


# ===================================================================
# 9. BVR CHART -- NAKSHATRAS
# ===================================================================
class TestBVRNakshatras(unittest.TestCase):

    def test_sun_in_chitra(self):
        self.assertEqual(bvr()["planets"]["Sun"]["nakshatra"], "Chitra")

    def test_moon_in_shatabhisha(self):
        self.assertEqual(bvr()["planets"]["Moon"]["nakshatra"], "Shatabhisha")

    def test_mars_in_jyeshtha(self):
        self.assertEqual(bvr()["planets"]["Mars"]["nakshatra"], "Jyeshtha")

    def test_mercury_in_chitra(self):
        self.assertEqual(bvr()["planets"]["Mercury"]["nakshatra"], "Chitra")

    def test_jupiter_in_punarvasu(self):
        self.assertEqual(bvr()["planets"]["Jupiter"]["nakshatra"], "Punarvasu")

    def test_venus_in_hasta(self):
        self.assertEqual(bvr()["planets"]["Venus"]["nakshatra"], "Hasta")

    def test_saturn_in_magha(self):
        self.assertEqual(bvr()["planets"]["Saturn"]["nakshatra"], "Magha")


# ===================================================================
# 10. BVR CHART -- HOUSES (whole-sign from Capricorn)
# ===================================================================
class TestBVRHouses(unittest.TestCase):

    def test_sun_house_9(self):
        self.assertEqual(bvr()["planets"]["Sun"]["house"], 9)

    def test_moon_house_2(self):
        self.assertEqual(bvr()["planets"]["Moon"]["house"], 2)

    def test_mars_house_11(self):
        self.assertEqual(bvr()["planets"]["Mars"]["house"], 11)

    def test_mercury_house_10(self):
        self.assertEqual(bvr()["planets"]["Mercury"]["house"], 10)

    def test_jupiter_house_6(self):
        self.assertEqual(bvr()["planets"]["Jupiter"]["house"], 6)

    def test_saturn_house_8(self):
        self.assertEqual(bvr()["planets"]["Saturn"]["house"], 8)


# ===================================================================
# 11. BVR CHART -- DIGNITIES (compound relationships)
# ===================================================================
class TestBVRDignities(unittest.TestCase):

    VALID_DIGNITIES = {"exalted", "mooltrikona", "own_sign", "great_friend",
                       "friend", "neutral", "enemy", "great_enemy", "debilitated"}

    def test_mars_own_sign_in_scorpio(self):
        self.assertEqual(bvr()["planets"]["Mars"]["dignity"], "own_sign")

    def test_venus_debilitated_in_virgo(self):
        self.assertEqual(bvr()["planets"]["Venus"]["dignity"], "debilitated")

    def test_mercury_great_friend_in_libra(self):
        self.assertEqual(bvr()["planets"]["Mercury"]["dignity"], "great_friend")

    def test_jupiter_great_enemy_in_gemini(self):
        self.assertEqual(bvr()["planets"]["Jupiter"]["dignity"], "great_enemy")

    def test_sun_friend_in_virgo(self):
        self.assertEqual(bvr()["planets"]["Sun"]["dignity"], "friend")

    def test_all_dignities_valid(self):
        for name, data in bvr()["planets"].items():
            self.assertIn(data["dignity"], self.VALID_DIGNITIES,
                          f"{name} has invalid dignity: {data['dignity']}")


# ===================================================================
# 12. BVR CHART -- COMBUSTION
# ===================================================================
class TestBVRCombustion(unittest.TestCase):

    def test_mercury_combust(self):
        self.assertTrue(bvr()["planets"]["Mercury"]["is_combust"])

    def test_venus_combust(self):
        self.assertTrue(bvr()["planets"]["Venus"]["is_combust"])

    def test_sun_never_combust(self):
        self.assertFalse(bvr()["planets"]["Sun"]["is_combust"])

    def test_mars_not_combust(self):
        self.assertFalse(bvr()["planets"]["Mars"]["is_combust"])

    def test_rahu_never_combust(self):
        self.assertFalse(bvr()["planets"]["Rahu"]["is_combust"])

    def test_combustion_pure_function(self):
        self.assertTrue(check_combustion("Moon", 100.0, 108.0, False))
        self.assertFalse(check_combustion("Moon", 100.0, 115.0, False))
        self.assertFalse(check_combustion("Sun", 100.0, 100.0, False))


# ===================================================================
# 13. BVR CHART -- DIGBALA
# ===================================================================
class TestBVRDigbala(unittest.TestCase):

    def test_no_planet_has_digbala_in_standard_chart(self):
        for name, data in bvr()["planets"].items():
            if name in ("Rahu", "Ketu"):
                continue
            expected_house = DIGBALA_HOUSES.get(name)
            if expected_house and data["house"] != expected_house:
                self.assertFalse(data["has_digbala"])

    def test_digbala_pure_function(self):
        self.assertTrue(get_digbala("Sun", 10))
        self.assertTrue(get_digbala("Jupiter", 1))
        self.assertFalse(get_digbala("Sun", 4))
        self.assertFalse(get_digbala("Jupiter", 7))


# ===================================================================
# 14. BVR CHART -- PANCHANG
#    Born: Wednesday (Mercury), Shukla Ekadashi, Shatabhisha nak
# ===================================================================
class TestBVRPanchang(unittest.TestCase):

    def test_vara_wednesday(self):
        vara = bvr()["panchang"]["vara"]
        self.assertEqual(vara["name"], "Wednesday")
        self.assertEqual(vara["lord"], "Mercury")

    def test_tithi_shukla_ekadashi(self):
        tithi = bvr()["panchang"]["tithi"]
        self.assertEqual(tithi["name"], "Ekadashi")
        self.assertEqual(tithi["paksha"], "Shukla")
        self.assertEqual(tithi["number"], 11)

    def test_nakshatra_shatabhisha(self):
        nak = bvr()["panchang"]["nakshatra"]
        self.assertEqual(nak["name"], "Shatabhisha")
        self.assertEqual(nak["lord"], "Rahu")

    def test_yoga_ganda(self):
        yoga = bvr()["panchang"]["yoga"]
        self.assertIsInstance(yoga, dict)
        self.assertEqual(yoga["name"], "Ganda")

    def test_karana_vishti(self):
        self.assertEqual(bvr()["panchang"]["karana"], "Vishti")


# ===================================================================
# 15. BVR CHART -- DASHAS
#    Moon in Shatabhisha (lord = Rahu) -> first dasha = Rahu
#    VedAstro: Mercury dasha begins ~1964 (Raman ayanamsha)
# ===================================================================
class TestBVRDashas(unittest.TestCase):

    def test_first_dasha_lord_is_rahu(self):
        first = bvr()["dashas"]["timeline"][0]
        self.assertEqual(first["planet"], "Rahu")

    def test_maha_dasha_at_1950_is_saturn(self):
        self.assertEqual(bvr()["dashas"]["maha"]["planet"], "Saturn")

    def test_antar_dasha_at_1950_is_saturn(self):
        self.assertEqual(bvr()["dashas"]["antar"]["planet"], "Saturn")

    def test_five_dasha_levels(self):
        d = bvr()["dashas"]
        for level in ["maha", "antar", "pratyantar", "sukshma", "prana"]:
            self.assertIn(level, d)
            self.assertIn(d[level]["planet"], DASHA_SEQUENCE)

    def test_timeline_covers_120_years(self):
        tl = bvr()["dashas"]["timeline"]
        self.assertGreaterEqual(len(tl), 9)
        first_start = datetime.datetime.strptime(tl[0]["start"], "%Y-%m-%d")
        last_end = datetime.datetime.strptime(tl[-1]["end"], "%Y-%m-%d")
        total_days = (last_end - first_start).days
        # Timeline includes partial first + 8 full + partial last cycle
        # covering ~120-138 years depending on start offset
        self.assertGreater(total_days, 100 * 365)
        self.assertLessEqual(total_days, 140 * 366)

    def test_mercury_dasha_starts_near_1967(self):
        for entry in bvr()["dashas"]["timeline"]:
            if entry["planet"] == "Mercury":
                start_year = int(entry["start"][:4])
                self.assertAlmostEqual(start_year, 1967, delta=4)
                break

    def test_dasha_sequence_order(self):
        tl = bvr()["dashas"]["timeline"]
        rahu_idx = DASHA_SEQUENCE.index("Rahu")
        for i, entry in enumerate(tl):
            expected = DASHA_SEQUENCE[(rahu_idx + i) % 9]
            self.assertEqual(entry["planet"], expected,
                             f"Entry {i}: expected {expected}, got {entry['planet']}")


# ===================================================================
# 16. BVR CHART -- ASHTAKAVARGA
# ===================================================================
class TestBVRAshtakavarga(unittest.TestCase):

    def test_total_bindus_337(self):
        self.assertEqual(bvr()["ashtakavarga"]["total_bindus"], 337)

    def test_sav_has_12_signs(self):
        sav = bvr()["ashtakavarga"]["sarvashtakavarga"]
        self.assertEqual(len(sav), 12)
        for sign in ZODIAC_SIGNS:
            self.assertIn(sign, sav)

    def test_sav_sum_is_337(self):
        sav = bvr()["ashtakavarga"]["sarvashtakavarga"]
        self.assertEqual(sum(sav.values()), 337)

    def test_bav_has_7_planets(self):
        bav = bvr()["ashtakavarga"]["bhinnashtakavarga"]
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            self.assertIn(planet, bav)

    def test_prashtara_exists(self):
        self.assertIn("prashtarashtakavarga", bvr()["ashtakavarga"])


# ===================================================================
# 17. BVR CHART -- JAIMINI KARAKAS
#    Sun (29.46) = AK, Mercury (0.05) = DK
# ===================================================================
class TestBVRJaiminiKarakas(unittest.TestCase):

    def test_atmakaraka_is_sun(self):
        ak = bvr()["jaimini_karakas"]["Atmakaraka"]
        self.assertEqual(ak["planet"], "Sun")
        self.assertAlmostEqual(ak["degree"], 29.46, delta=0.1)

    def test_darakaraka_is_mercury(self):
        dk = bvr()["jaimini_karakas"]["Darakaraka"]
        self.assertEqual(dk["planet"], "Mercury")

    def test_seven_karakas(self):
        expected = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka",
                    "Matrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka"]
        for k in expected:
            self.assertIn(k, bvr()["jaimini_karakas"])

    def test_all_different_planets(self):
        planets = [v["planet"] for v in bvr()["jaimini_karakas"].values()]
        self.assertEqual(len(set(planets)), 7)

    def test_amatyakaraka_is_jupiter(self):
        self.assertEqual(bvr()["jaimini_karakas"]["Amatyakaraka"]["planet"], "Jupiter")


# ===================================================================
# 18. BVR CHART -- ARUDHA PADAS
# ===================================================================
class TestBVRArudhaPadas(unittest.TestCase):

    def test_12_padas(self):
        self.assertEqual(len(bvr()["arudha_padas"]), 12)

    def test_arudha_lagna_pisces(self):
        al = bvr()["arudha_padas"][1]
        self.assertEqual(al["name"], "Arudha Lagna (AL)")
        self.assertEqual(al["sign"], "Pisces")

    def test_pada_structure(self):
        for house, pada in bvr()["arudha_padas"].items():
            self.assertIn("sign", pada)
            self.assertIn("name", pada)


# ===================================================================
# 19. BVR CHART -- UPAPADA
# ===================================================================
class TestBVRUpapada(unittest.TestCase):

    def test_upapada_sign_virgo(self):
        self.assertEqual(bvr()["upapada"]["sign"], "Virgo")

    def test_upapada_lord_mercury(self):
        self.assertEqual(bvr()["upapada"]["lord"], "Mercury")

    def test_second_from_ul_libra(self):
        self.assertEqual(bvr()["upapada"]["second_from_ul"], "Libra")


# ===================================================================
# 20. BVR CHART -- KARAKAMSHA
# ===================================================================
class TestBVRKarakamsha(unittest.TestCase):

    def test_karakamsha_sign_virgo(self):
        """AK = Sun, Sun's D9 = Virgo -> Karakamsha = Virgo."""
        self.assertEqual(bvr()["karakamsha"]["karakamsha_sign"], "Virgo")

    def test_karakamsha_structure(self):
        kk = bvr()["karakamsha"]
        for key in ["atmakaraka", "karakamsha_sign", "ishta_devata_sign", "ishta_devata_lord"]:
            self.assertIn(key, kk)


# ===================================================================
# 21. BVR CHART -- BHAVA CHALIT
# ===================================================================
class TestBVRBhavaChalit(unittest.TestCase):

    def test_all_planets_present(self):
        bc = bvr()["bhava_chalit"]
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            self.assertIn(planet, bc)

    def test_sun_bhava_house_9(self):
        self.assertEqual(bvr()["bhava_chalit"]["Sun"]["bhava_house"], 9)

    def test_shifted_flag_boolean(self):
        for name, data in bvr()["bhava_chalit"].items():
            self.assertIsInstance(data["shifted"], bool)

    def test_rashi_house_matches_planet_house(self):
        for name, data in bvr()["bhava_chalit"].items():
            self.assertEqual(data["rashi_house"], bvr()["planets"][name]["house"])


# ===================================================================
# 22. BVR CHART -- AVASTHAS
# ===================================================================
class TestBVRAvasthas(unittest.TestCase):

    VALID_AVASTHAS = {"Bala", "Kumara", "Yuva", "Vriddha", "Mrita"}

    def test_sun_mrita_at_29deg(self):
        self.assertEqual(bvr()["avasthas"]["Sun"]["avastha"], "Mrita")

    def test_moon_kumara_at_10deg(self):
        self.assertEqual(bvr()["avasthas"]["Moon"]["avastha"], "Kumara")

    def test_saturn_bala_at_3deg(self):
        self.assertEqual(bvr()["avasthas"]["Saturn"]["avastha"], "Bala")

    def test_mercury_bala_at_0deg(self):
        self.assertEqual(bvr()["avasthas"]["Mercury"]["avastha"], "Bala")

    def test_mars_vriddha_at_18deg(self):
        self.assertEqual(bvr()["avasthas"]["Mars"]["avastha"], "Vriddha")

    def test_all_avasthas_valid(self):
        for name, data in bvr()["avasthas"].items():
            self.assertIn(data["avastha"], self.VALID_AVASTHAS)

    def test_strength_factor_positive(self):
        for name, data in bvr()["avasthas"].items():
            self.assertGreater(data["strength_factor"], 0)

    def test_yuva_pure_function(self):
        raw = {"P": {"lon": 15.0, "sign": "Aries", "degree": 15.0,
                      "sign_idx": 0, "speed": 0, "is_retrograde": False}}
        pd = {"P": {"sign": "Aries", "degree": 15.0, "house": 1}}
        av = calculate_avasthas(pd, raw)
        self.assertEqual(av["P"]["avastha"], "Yuva")
        self.assertAlmostEqual(av["P"]["strength_factor"], 1.0)


# ===================================================================
# 23. BVR CHART -- KAAL SARPA DOSHA
# ===================================================================
class TestBVRKaalSarpa(unittest.TestCase):

    def test_no_kaal_sarpa_in_bvr(self):
        self.assertIsNone(bvr()["kaal_sarpa"])

    def test_synthetic_active(self):
        raw = {
            "Sun":     {"lon": 40, "sign_idx": 1, "degree": 10, "sign": "Taurus", "speed": 1, "is_retrograde": False},
            "Moon":    {"lon": 70, "sign_idx": 2, "degree": 10, "sign": "Gemini", "speed": 12, "is_retrograde": False},
            "Mars":    {"lon": 100, "sign_idx": 3, "degree": 10, "sign": "Cancer", "speed": 0.5, "is_retrograde": False},
            "Mercury": {"lon": 50, "sign_idx": 1, "degree": 20, "sign": "Taurus", "speed": 1, "is_retrograde": False},
            "Jupiter": {"lon": 60, "sign_idx": 2, "degree": 0, "sign": "Gemini", "speed": 0.1, "is_retrograde": False},
            "Venus":   {"lon": 80, "sign_idx": 2, "degree": 20, "sign": "Gemini", "speed": 1, "is_retrograde": False},
            "Saturn":  {"lon": 110, "sign_idx": 3, "degree": 20, "sign": "Cancer", "speed": 0.05, "is_retrograde": False},
            "Rahu":    {"lon": 10, "sign_idx": 0, "degree": 10, "sign": "Aries", "speed": -0.05, "is_retrograde": True},
            "Ketu":    {"lon": 190, "sign_idx": 6, "degree": 10, "sign": "Libra", "speed": -0.05, "is_retrograde": True},
        }
        ks = detect_kaal_sarpa(raw)
        self.assertIsNotNone(ks)
        self.assertTrue(ks["present"])


# ===================================================================
# 24. BVR CHART -- GRAHA YUDDHA
# ===================================================================
class TestBVRGrahaYuddha(unittest.TestCase):

    def test_no_war_in_bvr(self):
        self.assertEqual(len(bvr()["graha_yuddha"]), 0)

    def test_synthetic_war(self):
        raw = {
            "Mars":    {"lon": 50.0, "sign_idx": 1, "degree": 20.0, "sign": "Taurus", "speed": 0.5, "is_retrograde": False},
            "Mercury": {"lon": 50.5, "sign_idx": 1, "degree": 20.5, "sign": "Taurus", "speed": 1.0, "is_retrograde": False},
            "Jupiter": {"lon": 90.0, "sign_idx": 3, "degree": 0.0, "sign": "Cancer", "speed": 0.1, "is_retrograde": False},
            "Venus":   {"lon": 120.0, "sign_idx": 4, "degree": 0.0, "sign": "Leo", "speed": 1.0, "is_retrograde": False},
            "Saturn":  {"lon": 200.0, "sign_idx": 6, "degree": 20.0, "sign": "Libra", "speed": 0.05, "is_retrograde": False},
            "Sun":     {"lon": 30.0, "sign_idx": 1, "degree": 0.0, "sign": "Taurus", "speed": 1.0, "is_retrograde": False},
            "Moon":    {"lon": 150.0, "sign_idx": 5, "degree": 0.0, "sign": "Virgo", "speed": 12.0, "is_retrograde": False},
            "Rahu":    {"lon": 10.0, "sign_idx": 0, "degree": 10.0, "sign": "Aries", "speed": -0.05, "is_retrograde": True},
            "Ketu":    {"lon": 190.0, "sign_idx": 6, "degree": 10.0, "sign": "Libra", "speed": -0.05, "is_retrograde": True},
        }
        wars = detect_graha_yuddha(raw)
        self.assertGreaterEqual(len(wars), 1)
        self.assertIn("winner", wars[0])
        self.assertIn("separation_degrees", wars[0])


# ===================================================================
# 25. BVR CHART -- GANDANTA
# ===================================================================
class TestBVRGandanta(unittest.TestCase):

    def test_saturn_gandanta_cancer_leo(self):
        gd = bvr()["gandanta"]
        saturn_gd = [g for g in gd if g["planet"] == "Saturn"]
        self.assertEqual(len(saturn_gd), 1)
        self.assertEqual(saturn_gd[0]["junction"], "Cancer-Leo")

    def test_no_gandanta_at_safe_degree(self):
        raw = {"P": {"lon": 15.0, "sign_idx": 0, "degree": 15.0, "sign": "Aries",
                      "speed": 1, "is_retrograde": False}}
        self.assertEqual(len(detect_gandanta(raw)), 0)

    def test_gandanta_at_pisces_aries(self):
        raw = {"P": {"lon": 0.5, "sign_idx": 0, "degree": 0.5, "sign": "Aries",
                      "speed": 1, "is_retrograde": False}}
        self.assertGreaterEqual(len(detect_gandanta(raw)), 1)


# ===================================================================
# 26. BVR CHART -- YOGAS
# ===================================================================
class TestBVRYogas(unittest.TestCase):

    def test_yogas_is_list(self):
        self.assertIsInstance(bvr()["yogas"], list)

    def test_yoga_entry_structure(self):
        for y in bvr()["yogas"]:
            self.assertIn("name", y)
            self.assertIn("description", y)

    def test_raj_yoga_present(self):
        names = [y["name"] for y in bvr()["yogas"]]
        self.assertIn("Raj Yoga", names)

    def test_viparita_raj_yoga_present(self):
        names = [y["name"] for y in bvr()["yogas"]]
        self.assertIn("Viparita Raj Yoga", names)

    def test_parivartana_yoga_present(self):
        names = [y["name"] for y in bvr()["yogas"]]
        self.assertTrue(any("Parivartana" in n for n in names))

    def test_budhaditya_synthetic(self):
        """Sun + Mercury in same sign, Mercury not combust -> Budhaditya."""
        planets = {
            "Sun": {"sign": "Leo", "sign_idx": 4, "house": 1, "dignity": "own_sign", "is_combust": False},
            "Mercury": {"sign": "Leo", "sign_idx": 4, "house": 1, "dignity": "friend", "is_combust": False},
            "Moon": {"sign": "Taurus", "sign_idx": 1, "house": 10, "dignity": "exalted", "is_combust": False},
            "Mars": {"sign": "Capricorn", "sign_idx": 9, "house": 6, "dignity": "exalted", "is_combust": False},
            "Jupiter": {"sign": "Sagittarius", "sign_idx": 8, "house": 5, "dignity": "own_sign", "is_combust": False},
            "Venus": {"sign": "Virgo", "sign_idx": 5, "house": 2, "dignity": "debilitated", "is_combust": False},
            "Saturn": {"sign": "Aquarius", "sign_idx": 10, "house": 7, "dignity": "own_sign", "is_combust": False},
            "Rahu": {"sign": "Gemini", "sign_idx": 2, "house": 11, "dignity": "neutral", "is_combust": False},
            "Ketu": {"sign": "Sagittarius", "sign_idx": 8, "house": 5, "dignity": "neutral", "is_combust": False},
        }
        yogas = detect_yogas(planets, "Leo")
        names = [y["name"] for y in yogas]
        self.assertIn("Budhaditya Yoga", names)


# ===================================================================
# 27. BVR CHART -- SHADBALA
#    VedAstro Ishta/Kashta (Raman ayanamsha, pg 109):
#    Sun: ishta=8.25, kashta=46.13  (our Lahiri values differ)
# ===================================================================
class TestBVRShadbala(unittest.TestCase):

    def test_all_7_planets(self):
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            self.assertIn(planet, bvr()["shadbala"])

    def test_components_present(self):
        for planet, data in bvr()["shadbala"].items():
            for key in ["sthana_bala", "dig_bala", "kala_bala",
                        "naisargika_bala", "drik_bala", "total_rupas"]:
                self.assertIn(key, data, f"{planet} missing {key}")

    def test_positive_total_rupas(self):
        for planet, data in bvr()["shadbala"].items():
            self.assertGreater(data["total_rupas"], 0)

    def test_strength_ratio_present(self):
        for planet, data in bvr()["shadbala"].items():
            self.assertIn("strength_ratio", data)
            self.assertGreater(data["strength_ratio"], 0)

    def test_ishta_kashta_at_top_level(self):
        for planet, data in bvr()["shadbala"].items():
            self.assertIn("ishta_phala", data)
            self.assertIn("kashta_phala", data)
            self.assertGreaterEqual(data["ishta_phala"], 0)
            self.assertGreaterEqual(data["kashta_phala"], 0)

    def test_sun_total_rupas_near_5(self):
        self.assertAlmostEqual(bvr()["shadbala"]["Sun"]["total_rupas"], 5.32, delta=0.5)


# ===================================================================
# 28. BVR CHART -- FULL STRUCTURE INTEGRATION
# ===================================================================
class TestBVRFullChart(unittest.TestCase):

    def test_all_top_level_keys(self):
        expected = [
            "metadata", "panchang", "lagna", "planets", "dashas", "yogas",
            "ashtakavarga", "jaimini_karakas", "shadbala",
            "bhava_chalit", "avasthas", "kaal_sarpa", "graha_yuddha",
            "gandanta", "arudha_padas", "upapada", "karakamsha",
        ]
        for key in expected:
            self.assertIn(key, bvr())

    def test_metadata(self):
        m = bvr()["metadata"]
        self.assertIn("dob", m)
        self.assertIn("time", m)
        self.assertIn("coordinates", m)
        self.assertIn("lat", m["coordinates"])
        self.assertIn("lon", m["coordinates"])
        self.assertIn("ayanamsha", m)
        self.assertEqual(m["ayanamsha"], "Lahiri")

    def test_all_nine_planets(self):
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            self.assertIn(planet, bvr()["planets"])

    def test_planet_fields_complete(self):
        required = ["sign", "degree", "house", "nakshatra", "pada",
                     "nakshatra_lord", "is_retrograde", "is_combust",
                     "dignity", "has_digbala", "d9_sign", "d10_sign"]
        for name, data in bvr()["planets"].items():
            for field in required:
                self.assertIn(field, data, f"{name} missing {field}")

    def test_all_14_varga_signs_valid(self):
        vargas = ["d2_sign", "d3_sign", "d4_sign", "d7_sign", "d9_sign",
                  "d10_sign", "d12_sign", "d16_sign", "d20_sign",
                  "d24_sign", "d27_sign", "d30_sign", "d40_sign", "d60_sign"]
        for name, data in bvr()["planets"].items():
            for v in vargas:
                self.assertIn(data[v], ZODIAC_SIGNS, f"{name} {v}='{data[v]}' invalid")

    def test_degree_range_0_to_30(self):
        for name, data in bvr()["planets"].items():
            self.assertGreaterEqual(data["degree"], 0)
            self.assertLess(data["degree"], 30)

    def test_house_range_1_to_12(self):
        for name, data in bvr()["planets"].items():
            self.assertGreaterEqual(data["house"], 1)
            self.assertLessEqual(data["house"], 12)

    def test_json_serializable(self):
        import json
        json.dumps(bvr())


# ===================================================================
# 29. DELHI CHART -- KNOWN VALUES
# ===================================================================
class TestDelhiChart(unittest.TestCase):

    def test_lagna_leo(self):
        self.assertEqual(delhi()["lagna"]["sign"], "Leo")

    def test_sun_exalted_in_aries(self):
        sun = delhi()["planets"]["Sun"]
        self.assertEqual(sun["sign"], "Aries")
        self.assertEqual(sun["dignity"], "exalted")

    def test_moon_debilitated_in_scorpio(self):
        moon = delhi()["planets"]["Moon"]
        self.assertEqual(moon["sign"], "Scorpio")
        self.assertEqual(moon["dignity"], "debilitated")

    def test_saturn_own_sign_capricorn(self):
        sat = delhi()["planets"]["Saturn"]
        self.assertEqual(sat["sign"], "Capricorn")
        self.assertEqual(sat["dignity"], "own_sign")

    def test_mars_in_aquarius(self):
        self.assertEqual(delhi()["planets"]["Mars"]["sign"], "Aquarius")

    def test_jupiter_in_gemini(self):
        self.assertEqual(delhi()["planets"]["Jupiter"]["sign"], "Gemini")

    def test_maha_dasha_is_moon(self):
        self.assertEqual(delhi()["dashas"]["maha"]["planet"], "Moon")

    def test_all_top_level_keys(self):
        for key in ["metadata", "panchang", "lagna", "planets", "dashas", "yogas",
                     "ashtakavarga", "jaimini_karakas", "shadbala"]:
            self.assertIn(key, delhi())

    def test_json_serializable(self):
        import json
        json.dumps(delhi())


# ===================================================================
# 30. MATCHMAKING -- using BVR & Delhi Moon longitudes
# ===================================================================
class TestMatchmaking(unittest.TestCase):

    @staticmethod
    def _moon_lon(chart):
        moon = chart["planets"]["Moon"]
        return ZODIAC_SIGNS.index(moon["sign"]) * 30 + moon["degree"]

    def _match(self):
        return calculate_ashtakoot(self._moon_lon(bvr()), self._moon_lon(delhi()))

    def test_total_between_0_and_36(self):
        m = self._match()
        self.assertGreaterEqual(m["total_score"], 0)
        self.assertLessEqual(m["total_score"], 36)
        self.assertEqual(m["max_score"], 36.0)

    def test_8_kutas_present(self):
        for kuta in ["Varna", "Vashya", "Tara", "Yoni", "GrahaMaitri", "Gana", "Bhakoot", "Nadi"]:
            self.assertIn(kuta, self._match()["scores"])

    def test_individual_kuta_max(self):
        maxes = {"Varna": 1, "Vashya": 2, "Tara": 3, "Yoni": 4,
                 "GrahaMaitri": 5, "Gana": 6, "Bhakoot": 7, "Nadi": 8}
        scores = self._match()["scores"]
        for kuta, mx in maxes.items():
            self.assertLessEqual(scores[kuta], mx)
            self.assertGreaterEqual(scores[kuta], 0)

    def test_additional_kutas(self):
        for kuta in ["Mahendra", "StreeDeergha", "Vedha", "Rajju"]:
            self.assertIn(kuta, self._match()["additional_kutas"])

    def test_male_female_details(self):
        m = self._match()
        for key in ["male_details", "female_details"]:
            self.assertIn("moon_sign", m[key])
            self.assertIn("nakshatra", m[key])


# ===================================================================
# 31. MUHURTHA
# ===================================================================
class TestMuhurtha(unittest.TestCase):

    def test_bvr_time_inauspicious_for_marriage(self):
        c = bvr()
        result = evaluate_muhurtha("marriage", c["panchang"], c["planets"], c["lagna"]["sign"])
        self.assertEqual(result["verdict"], "inauspicious")
        self.assertIn("score", result)
        self.assertIn("positive_factors", result)
        self.assertIn("negative_factors", result)

    def test_invalid_activity_returns_error(self):
        c = bvr()
        result = evaluate_muhurtha("xyz_invalid", c["panchang"], c["planets"], c["lagna"]["sign"])
        self.assertEqual(result["verdict"], "error")


# ===================================================================
# 32. CAREER ANALYSIS
# ===================================================================
class TestCareer(unittest.TestCase):

    def test_career_structure(self):
        result = analyze_career(bvr()["planets"], bvr()["lagna"]["sign"])
        for key in ["tenth_house", "d10_indicators", "career_themes", "strength_factors"]:
            self.assertIn(key, result)

    def test_10th_house_libra(self):
        result = analyze_career(bvr()["planets"], bvr()["lagna"]["sign"])
        self.assertEqual(result["tenth_house"]["sign"], "Libra")
        self.assertEqual(result["tenth_house"]["lord"], "Venus")

    def test_mercury_in_10th_house(self):
        result = analyze_career(bvr()["planets"], bvr()["lagna"]["sign"])
        self.assertIn("Mercury", result["tenth_house"]["occupants"])


# ===================================================================
# 33. TRANSIT
# ===================================================================
class TestTransit(unittest.TestCase):

    def test_transit_structure(self):
        from vedic_calculator import calculate_transit
        transit = calculate_transit("2025-01-01", bvr(), "Asia/Kolkata")
        self.assertIn("planets", transit)
        self.assertIn("sade_sati", transit)

    def test_transit_planet_fields(self):
        from vedic_calculator import calculate_transit
        transit = calculate_transit("2025-01-01", bvr(), "Asia/Kolkata")
        for name, data in transit["planets"].items():
            self.assertIn("sign", data)
            self.assertIn("degree", data)

    def test_sade_sati_structure(self):
        from vedic_calculator import calculate_transit
        transit = calculate_transit("2025-01-01", bvr(), "Asia/Kolkata")
        self.assertIn("active", transit["sade_sati"])


# ===================================================================
# 34. VEDASTRO CROSS-VALIDATION -- D2/D3 signs
# ===================================================================
class TestVedAstroCrossValidation(unittest.TestCase):
    """Cross-validate D2/D3 signs against VedAstro computed values (Lahiri)."""

    def test_d2_hora_all_planets(self):
        expected = {
            "Sun": "Leo", "Moon": "Leo", "Mars": "Leo",
            "Mercury": "Leo", "Jupiter": "Cancer", "Venus": "Leo",
            "Saturn": "Leo",
        }
        for planet, exp_sign in expected.items():
            actual = bvr()["planets"][planet]["d2_sign"]
            self.assertEqual(actual, exp_sign,
                             f"D2 {planet}: expected {exp_sign}, got {actual}")

    def test_d3_drekkana_all_planets(self):
        expected = {
            "Sun": "Taurus", "Moon": "Aquarius", "Mars": "Pisces",
            "Mercury": "Libra", "Jupiter": "Aquarius",
            "Venus": "Capricorn", "Saturn": "Leo",
        }
        for planet, exp_sign in expected.items():
            actual = bvr()["planets"][planet]["d3_sign"]
            self.assertEqual(actual, exp_sign,
                             f"D3 {planet}: expected {exp_sign}, got {actual}")

    def test_planet_signs_match_vedastro(self):
        expected = {
            "Sun": "Virgo", "Moon": "Aquarius", "Mars": "Scorpio",
            "Mercury": "Libra", "Jupiter": "Gemini", "Venus": "Virgo",
            "Saturn": "Leo", "Rahu": "Scorpio", "Ketu": "Taurus",
        }
        for planet, exp_sign in expected.items():
            actual = bvr()["planets"][planet]["sign"]
            self.assertEqual(actual, exp_sign,
                             f"{planet}: expected {exp_sign}, got {actual}")


if __name__ == "__main__":
    unittest.main()
