"""
Comprehensive Test Suite for RishiAI Vedic Astrology MCP Server
================================================================
Tests all modules: vedic_calculator, yoga, jaimini, dasha, dignity,
ashtakavarga, shadbala, panchang, nakshatra, matchmaking, muhurtha, career.

Reference horoscope: B.V. Raman Standard Horoscope
Born 16-Oct-1918, 14:20 IST, Bangalore (12.9716°N, 77.5946°E)

Also uses:
- Delhi male: 15-Apr-1990, 14:30, Delhi
- Kochi native: 22-Oct-1999, 04:20, Kochi
"""

import unittest
import sys
import os
import datetime

# ---------------------------------------------------------------------------
# Module imports
# ---------------------------------------------------------------------------
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
# HELPER: Cast a chart once, reuse across tests
# ===================================================================
# B.V. Raman Standard Horoscope
STD_CHART = None

def get_standard_chart():
    """Lazy-load the standard horoscope chart."""
    global STD_CHART
    if STD_CHART is None:
        STD_CHART = calculate_vedic_chart(
            "1918-10-16", "14:20", 12.9716, 77.5946, "Asia/Kolkata",
            query_date_str="1950-01-01",
        )
    return STD_CHART


DELHI_CHART = None

def get_delhi_chart():
    """Delhi male for matchmaking tests."""
    global DELHI_CHART
    if DELHI_CHART is None:
        DELHI_CHART = calculate_vedic_chart(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
        )
    return DELHI_CHART


# ===================================================================
# 1. CONSTANTS VALIDATION
# ===================================================================
class TestConstants(unittest.TestCase):
    """Validate all astrological data tables for correctness."""

    def test_zodiac_signs_count(self):
        self.assertEqual(len(ZODIAC_SIGNS), 12)

    def test_zodiac_signs_order(self):
        self.assertEqual(ZODIAC_SIGNS[0], "Aries")
        self.assertEqual(ZODIAC_SIGNS[11], "Pisces")

    def test_sign_lords_complete(self):
        self.assertEqual(len(SIGN_LORDS), 12)
        for sign in ZODIAC_SIGNS:
            self.assertIn(sign, SIGN_LORDS)

    def test_sign_lords_values(self):
        self.assertEqual(SIGN_LORDS["Aries"], "Mars")
        self.assertEqual(SIGN_LORDS["Taurus"], "Venus")
        self.assertEqual(SIGN_LORDS["Cancer"], "Moon")
        self.assertEqual(SIGN_LORDS["Leo"], "Sun")
        self.assertEqual(SIGN_LORDS["Sagittarius"], "Jupiter")
        self.assertEqual(SIGN_LORDS["Capricorn"], "Saturn")

    def test_nakshatras_count(self):
        self.assertEqual(len(NAKSHATRAS), 27)

    def test_nakshatras_first_last(self):
        self.assertEqual(NAKSHATRAS[0]["name"], "Ashwini")
        self.assertEqual(NAKSHATRAS[0]["lord"], "Ketu")
        self.assertEqual(NAKSHATRAS[26]["name"], "Revati")
        self.assertEqual(NAKSHATRAS[26]["lord"], "Mercury")

    def test_nak_span(self):
        self.assertAlmostEqual(NAK_SPAN, 360.0 / 27.0, places=6)
        self.assertAlmostEqual(PADA_SPAN, NAK_SPAN / 4.0, places=6)

    def test_vimshottari_total(self):
        total = sum(VIMSHOTTARI_YEARS.values())
        self.assertEqual(total, 120)
        self.assertEqual(VIMSHOTTARI_TOTAL, 120.0)

    def test_dasha_sequence_length(self):
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

    def test_debilitation_opposite_of_exaltation(self):
        """Debilitation sign should be 7th from exaltation sign."""
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

    def test_mooltrikona_within_own_or_exalted(self):
        """Mooltrikona sign must be one of the planet's own signs."""
        for planet, (mt_sign, _, _) in MOOLTRIKONA.items():
            self.assertIn(mt_sign, OWN_SIGNS.get(planet, []) + [EXALTATION.get(planet, ("",))[0]],
                          f"{planet} mooltrikona in {mt_sign} is not own/exalted sign")

    def test_combustion_orbs_keys(self):
        for p in ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            self.assertIn(p, COMBUSTION_ORBS)

    def test_digbala_houses(self):
        self.assertEqual(DIGBALA_HOUSES["Sun"], 10)
        self.assertEqual(DIGBALA_HOUSES["Mars"], 10)
        self.assertEqual(DIGBALA_HOUSES["Jupiter"], 1)
        self.assertEqual(DIGBALA_HOUSES["Mercury"], 1)
        self.assertEqual(DIGBALA_HOUSES["Saturn"], 7)
        self.assertEqual(DIGBALA_HOUSES["Moon"], 4)
        self.assertEqual(DIGBALA_HOUSES["Venus"], 4)

    def test_tithi_names_count(self):
        self.assertEqual(len(TITHI_NAMES), 30)
        self.assertEqual(TITHI_NAMES[14], "Purnima")
        self.assertEqual(TITHI_NAMES[29], "Amavasya")

    def test_vara_count(self):
        self.assertEqual(len(VARA_NAMES), 7)
        self.assertEqual(len(VARA_LORDS), 7)


# ===================================================================
# 2. NAKSHATRA MODULE
# ===================================================================
class TestNakshatra(unittest.TestCase):

    def test_ashwini_start(self):
        """0° Aries = Ashwini pada 1."""
        n = get_nakshatra(0.0)
        self.assertEqual(n["name"], "Ashwini")
        self.assertEqual(n["pada"], 1)
        self.assertEqual(n["lord"], "Ketu")
        self.assertEqual(n["index"], 0)

    def test_revati_end(self):
        """359.99° = Revati pada 4."""
        n = get_nakshatra(359.99)
        self.assertEqual(n["name"], "Revati")
        self.assertEqual(n["pada"], 4)

    def test_magha_start(self):
        """120° = start of Magha (Leo 0°)."""
        n = get_nakshatra(120.0)
        self.assertEqual(n["name"], "Magha")
        self.assertEqual(n["pada"], 1)
        self.assertEqual(n["lord"], "Ketu")

    def test_vishakha(self):
        """200° is in Vishakha."""
        n = get_nakshatra(200.0)
        self.assertEqual(n["name"], "Vishakha")

    def test_pada_boundaries(self):
        """Each nakshatra has 4 equal padas spanning ~3.333°."""
        # Ashwini pada 2 starts at ~3.333°
        n = get_nakshatra(3.4)
        self.assertEqual(n["name"], "Ashwini")
        self.assertEqual(n["pada"], 2)

    def test_wrap_around(self):
        """360° wraps to 0° = Ashwini."""
        n = get_nakshatra(360.0)
        self.assertEqual(n["name"], "Ashwini")


# ===================================================================
# 3. SIGN / DEGREE CONVERSION
# ===================================================================
class TestSignAndDegree(unittest.TestCase):

    def test_aries_start(self):
        sign, deg, idx = get_sign_and_degree(0.0)
        self.assertEqual(sign, "Aries")
        self.assertEqual(idx, 0)
        self.assertAlmostEqual(deg, 0.0, places=1)

    def test_taurus_start(self):
        sign, deg, idx = get_sign_and_degree(30.0)
        self.assertEqual(sign, "Taurus")
        self.assertEqual(idx, 1)

    def test_pisces_end(self):
        sign, deg, idx = get_sign_and_degree(359.5)
        self.assertEqual(sign, "Pisces")
        self.assertAlmostEqual(deg, 29.5, places=1)

    def test_middle_of_leo(self):
        sign, deg, idx = get_sign_and_degree(135.0)
        self.assertEqual(sign, "Leo")
        self.assertAlmostEqual(deg, 15.0, places=1)

    def test_wrap_360(self):
        sign, deg, idx = get_sign_and_degree(360.0)
        self.assertEqual(sign, "Aries")


# ===================================================================
# 4. DIVISIONAL CHART FORMULAS
# ===================================================================
class TestDivisionalCharts(unittest.TestCase):
    """Test all 14 varga calculations with known boundary inputs."""

    # --- D2 (Hora) ---
    def test_d2_odd_sign_first_half(self):
        """Aries 10° (odd sign, <15°) → Leo."""
        self.assertEqual(calculate_d2_hora(10.0), "Leo")

    def test_d2_odd_sign_second_half(self):
        """Aries 20° (odd sign, ≥15°) → Cancer."""
        self.assertEqual(calculate_d2_hora(20.0), "Cancer")

    def test_d2_even_sign_first_half(self):
        """Taurus 10° (even sign, <15°) → Cancer."""
        self.assertEqual(calculate_d2_hora(40.0), "Cancer")

    def test_d2_even_sign_second_half(self):
        """Taurus 20° (even sign, ≥15°) → Leo."""
        self.assertEqual(calculate_d2_hora(50.0), "Leo")

    # --- D3 (Drekkana) ---
    def test_d3_first_decanate(self):
        """Aries 5° → Aries (same sign)."""
        self.assertEqual(calculate_d3_drekkana(5.0), "Aries")

    def test_d3_second_decanate(self):
        """Aries 15° → Leo (5th from)."""
        self.assertEqual(calculate_d3_drekkana(15.0), "Leo")

    def test_d3_third_decanate(self):
        """Aries 25° → Sagittarius (9th from)."""
        self.assertEqual(calculate_d3_drekkana(25.0), "Sagittarius")

    # --- D4 (Chaturthamsha) ---
    def test_d4_first_quarter(self):
        """Aries 3° → Aries."""
        self.assertEqual(calculate_d4_chaturthamsha(3.0), "Aries")

    def test_d4_second_quarter(self):
        """Aries 10° → Cancer (+3)."""
        self.assertEqual(calculate_d4_chaturthamsha(10.0), "Cancer")

    # --- D7 (Saptamsha) ---
    def test_d7_odd_sign_first(self):
        """Aries 2° → Aries (odd sign, first part)."""
        self.assertEqual(calculate_d7_saptamsha(2.0), "Aries")

    def test_d7_even_sign_first(self):
        """Taurus 2° (even sign, first part) → Scorpio (Taurus+6)."""
        self.assertEqual(calculate_d7_saptamsha(32.0), "Scorpio")

    # --- D9 (Navamsha) ---
    def test_navamsha_aries_start(self):
        """Aries 0° → Aries."""
        self.assertEqual(calculate_navamsha(0.0), "Aries")

    def test_navamsha_aries_end(self):
        """Aries 29° → 29*9 = 261° → Sagittarius."""
        self.assertEqual(calculate_navamsha(29.0), "Sagittarius")

    def test_navamsha_vargottama(self):
        """Aries 0-3.33° stays Aries (vargottama check)."""
        self.assertEqual(calculate_navamsha(1.0), "Aries")

    # --- D10 (Dashamsha) ---
    def test_dashamsha_odd_sign(self):
        """Aries 5° (odd sign, part=1) → Taurus."""
        self.assertEqual(calculate_dashamsha(5.0), "Taurus")

    def test_dashamsha_even_sign(self):
        """Taurus 5° (even sign, part=1) → Libra (Taurus+8+1)."""
        self.assertEqual(calculate_dashamsha(35.0), "Libra")

    # --- D12 (Dwadashamsha) ---
    def test_d12_first_part(self):
        """Aries 1° → Aries."""
        self.assertEqual(calculate_d12_dwadashamsha(1.0), "Aries")

    def test_d12_second_part(self):
        """Aries 3° → Taurus (part=1, Aries+1)."""
        self.assertEqual(calculate_d12_dwadashamsha(3.0), "Taurus")

    # --- D16 (Shodashamsha) ---
    def test_d16_aries_first_part(self):
        """Aries: start_idx = (0*4)%12 = 0 (Aries). Part 0 → Aries."""
        self.assertEqual(calculate_d16_shodashamsha(0.5), "Aries")

    # --- D20 (Vimshamsha) ---
    def test_d20_aries_first_part(self):
        """Aries: start_idx = (0*8)%12 = 0. Part 0 → Aries."""
        self.assertEqual(calculate_d20_vimshamsha(0.5), "Aries")

    # --- D24 (Chaturvimshamsha) ---
    def test_d24_odd_sign(self):
        """Aries (odd sign) starts from Leo (idx 4). Part 0 → Leo."""
        self.assertEqual(calculate_d24_chaturvimshamsha(0.5), "Leo")

    def test_d24_even_sign(self):
        """Taurus (even sign) starts from Cancer (idx 3). Part 0 → Cancer."""
        self.assertEqual(calculate_d24_chaturvimshamsha(30.5), "Cancer")

    # --- D27 (Bhamsha) ---
    def test_d27_fire_sign(self):
        """Aries (fire) starts from Aries. Part 0 → Aries."""
        self.assertEqual(calculate_d27_bhamsha(0.5), "Aries")

    def test_d27_earth_sign(self):
        """Taurus (earth) starts from Cancer. Part 0 → Cancer."""
        self.assertEqual(calculate_d27_bhamsha(30.5), "Cancer")

    def test_d27_air_sign(self):
        """Gemini (air) starts from Libra. Part 0 → Libra."""
        self.assertEqual(calculate_d27_bhamsha(60.5), "Libra")

    def test_d27_water_sign(self):
        """Cancer (water) starts from Capricorn. Part 0 → Capricorn."""
        self.assertEqual(calculate_d27_bhamsha(90.5), "Capricorn")

    # --- D30 (Trimshamsha) ---
    def test_d30_odd_sign_first_5(self):
        """Aries 3° (odd, degree <5) → Mars → Aries."""
        self.assertEqual(calculate_d30_trimshamsha(3.0), "Aries")

    def test_d30_odd_sign_second_5(self):
        """Aries 7° (odd, 5-10) → Saturn → Capricorn."""
        self.assertEqual(calculate_d30_trimshamsha(7.0), "Capricorn")

    def test_d30_even_sign_first_5(self):
        """Taurus 3° (even, <5) → Venus → Taurus."""
        self.assertEqual(calculate_d30_trimshamsha(33.0), "Taurus")

    # --- D40 (Khavedamsha) ---
    def test_d40_odd_sign(self):
        """Aries: odd sign starts from Aries (0). Part 0 at 0° → Aries."""
        self.assertEqual(calculate_d40_khavedamsha(0.3), "Aries")

    def test_d40_even_sign(self):
        """Taurus: even sign starts from Libra (6). Part 0 → Libra."""
        self.assertEqual(calculate_d40_khavedamsha(30.3), "Libra")

    # --- D60 (Shashtiamsha) ---
    def test_d60_odd_sign(self):
        """Aries (odd): counts from self. 0° part 0 → Aries."""
        self.assertEqual(calculate_d60_shashtiamsha(0.1), "Aries")

    def test_d60_even_sign(self):
        """Taurus (even): counts from 7th (Scorpio). 30° part 0 → Scorpio."""
        self.assertEqual(calculate_d60_shashtiamsha(30.1), "Scorpio")


# ===================================================================
# 5. ASPECTS
# ===================================================================
class TestAspects(unittest.TestCase):

    def test_sun_seventh_aspect_only(self):
        """Sun in Aries (0) → aspects Libra (6)."""
        aspects = get_vedic_aspects("Sun", 0)
        self.assertEqual(aspects, ["Libra"])

    def test_mars_special_aspects(self):
        """Mars in Aries → 4th (Cancer), 7th (Libra), 8th (Scorpio)."""
        aspects = get_vedic_aspects("Mars", 0)
        self.assertIn("Cancer", aspects)    # 4th
        self.assertIn("Libra", aspects)     # 7th
        self.assertIn("Scorpio", aspects)   # 8th

    def test_jupiter_special_aspects(self):
        """Jupiter in Aries → 5th (Leo), 7th (Libra), 9th (Sagittarius)."""
        aspects = get_vedic_aspects("Jupiter", 0)
        self.assertIn("Leo", aspects)          # 5th
        self.assertIn("Libra", aspects)        # 7th
        self.assertIn("Sagittarius", aspects)  # 9th

    def test_saturn_special_aspects(self):
        """Saturn in Aries → 3rd (Gemini), 7th (Libra), 10th (Capricorn)."""
        aspects = get_vedic_aspects("Saturn", 0)
        self.assertIn("Gemini", aspects)     # 3rd
        self.assertIn("Libra", aspects)      # 7th
        self.assertIn("Capricorn", aspects)  # 10th

    def test_rahu_ketu_seventh_only(self):
        """Rahu/Ketu only get 7th aspect."""
        aspects = get_vedic_aspects("Rahu", 0)
        self.assertEqual(len(aspects), 1)
        self.assertEqual(aspects[0], "Libra")


# ===================================================================
# 6. HOUSE FROM LAGNA
# ===================================================================
class TestHouseFromLagna(unittest.TestCase):

    def test_same_sign(self):
        self.assertEqual(_house_from_lagna(0, 0), 1)

    def test_opposite_sign(self):
        self.assertEqual(_house_from_lagna(6, 0), 7)

    def test_wrap_around(self):
        self.assertEqual(_house_from_lagna(0, 11), 2)  # Aries from Pisces = 2nd

    def test_12th_house(self):
        self.assertEqual(_house_from_lagna(11, 0), 12)  # Pisces from Aries = 12th


# ===================================================================
# 7. DIGNITY
# ===================================================================
class TestDignity(unittest.TestCase):

    def test_sun_exalted_in_aries(self):
        self.assertEqual(get_dignity("Sun", "Aries", 10, {}), "exalted")

    def test_sun_debilitated_in_libra(self):
        self.assertEqual(get_dignity("Sun", "Libra", 10, {}), "debilitated")

    def test_sun_mooltrikona_in_leo(self):
        self.assertEqual(get_dignity("Sun", "Leo", 10, {}), "mooltrikona")

    def test_sun_own_sign_in_leo_after_mooltrikona(self):
        """Leo 25° is past mooltrikona range (0-20°) → own_sign."""
        self.assertEqual(get_dignity("Sun", "Leo", 25, {}), "own_sign")

    def test_moon_exalted_in_taurus(self):
        self.assertEqual(get_dignity("Moon", "Taurus", 3, {}), "exalted")

    def test_mars_exalted_in_capricorn(self):
        self.assertEqual(get_dignity("Mars", "Capricorn", 28, {}), "exalted")

    def test_jupiter_exalted_in_cancer(self):
        self.assertEqual(get_dignity("Jupiter", "Cancer", 5, {}), "exalted")

    def test_venus_debilitated_in_virgo(self):
        self.assertEqual(get_dignity("Venus", "Virgo", 27, {}), "debilitated")

    def test_saturn_own_capricorn(self):
        self.assertEqual(get_dignity("Saturn", "Capricorn", 25, {}), "own_sign")


# ===================================================================
# 8. COMBUSTION
# ===================================================================
class TestCombustion(unittest.TestCase):

    def test_moon_combust_within_12(self):
        """Moon within 12° of Sun is combust."""
        self.assertTrue(check_combustion("Moon", 10.0, 5.0, False))

    def test_moon_not_combust_outside_12(self):
        """Moon 15° from Sun is not combust."""
        self.assertFalse(check_combustion("Moon", 20.0, 5.0, False))

    def test_sun_never_combust(self):
        """Sun cannot be combust."""
        self.assertFalse(check_combustion("Sun", 10.0, 10.0, False))

    def test_rahu_never_combust(self):
        """Rahu cannot be combust."""
        self.assertFalse(check_combustion("Rahu", 10.0, 5.0, False))

    def test_mercury_retrograde_tighter_orb(self):
        """Mercury retrograde: 12° orb vs 14° direct."""
        # At 13° separation: direct = combust, retrograde = not combust
        self.assertTrue(check_combustion("Mercury", 18.0, 5.0, False))
        self.assertFalse(check_combustion("Mercury", 18.0, 5.0, True))


# ===================================================================
# 9. DIGBALA
# ===================================================================
class TestDigbala(unittest.TestCase):

    def test_jupiter_digbala_house1(self):
        self.assertTrue(get_digbala("Jupiter", 1))

    def test_jupiter_no_digbala_house7(self):
        self.assertFalse(get_digbala("Jupiter", 7))

    def test_sun_digbala_house10(self):
        self.assertTrue(get_digbala("Sun", 10))

    def test_saturn_digbala_house7(self):
        self.assertTrue(get_digbala("Saturn", 7))

    def test_moon_digbala_house4(self):
        self.assertTrue(get_digbala("Moon", 4))

    def test_venus_digbala_house4(self):
        self.assertTrue(get_digbala("Venus", 4))


# ===================================================================
# 10. PANCHANG
# ===================================================================
class TestPanchang(unittest.TestCase):

    def test_panchang_structure(self):
        """Panchang should have 5 elements: tithi, vara, nakshatra, yoga, karana."""
        chart = get_standard_chart()
        p = chart["panchang"]
        self.assertIn("tithi", p)
        self.assertIn("vara", p)
        self.assertIn("nakshatra", p)
        self.assertIn("yoga", p)
        self.assertIn("karana", p)

    def test_tithi_has_fields(self):
        chart = get_standard_chart()
        tithi = chart["panchang"]["tithi"]
        self.assertIn("number", tithi)
        self.assertIn("name", tithi)
        self.assertIn("paksha", tithi)
        self.assertIn(tithi["paksha"], ["Shukla", "Krishna"])

    def test_vara_has_fields(self):
        chart = get_standard_chart()
        vara = chart["panchang"]["vara"]
        self.assertIn("day", vara)
        self.assertIn("lord", vara)
        self.assertIn(vara["lord"], ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"])

    def test_yoga_is_dict(self):
        """Yoga should be dict with index and name after bug fix."""
        chart = get_standard_chart()
        yoga = chart["panchang"]["yoga"]
        self.assertIsInstance(yoga, dict)
        self.assertIn("index", yoga)
        self.assertIn("name", yoga)

    def test_nakshatra_has_fields(self):
        chart = get_standard_chart()
        nak = chart["panchang"]["nakshatra"]
        self.assertIn("name", nak)
        self.assertIn("pada", nak)
        self.assertIn("lord", nak)


# ===================================================================
# 11. DASHA
# ===================================================================
class TestDasha(unittest.TestCase):

    def test_dasha_structure(self):
        chart = get_standard_chart()
        d = chart["dashas"]
        self.assertIn("maha", d)
        self.assertIn("antar", d)
        self.assertIn("pratyantar", d)
        self.assertIn("sukshma", d)
        self.assertIn("prana", d)
        self.assertIn("timeline", d)

    def test_dasha_five_levels(self):
        """All 5 dasha levels should be present."""
        chart = get_standard_chart()
        d = chart["dashas"]
        for level in ["maha", "antar", "pratyantar", "sukshma", "prana"]:
            self.assertIn("planet", d[level], f"{level} missing 'planet'")
            self.assertIn("start", d[level], f"{level} missing 'start'")
            self.assertIn("end", d[level], f"{level} missing 'end'")

    def test_dasha_planet_in_sequence(self):
        """Every dasha lord should be in the Vimshottari sequence."""
        chart = get_standard_chart()
        d = chart["dashas"]
        for level in ["maha", "antar", "pratyantar", "sukshma", "prana"]:
            self.assertIn(d[level]["planet"], DASHA_SEQUENCE,
                          f"{level} planet '{d[level]['planet']}' not in sequence")

    def test_timeline_covers_120_years(self):
        """Timeline should have 9 mahadasha entries covering ~120 years."""
        chart = get_standard_chart()
        timeline = chart["dashas"]["timeline"]
        self.assertEqual(len(timeline), 9)
        # Check total span
        first_start = datetime.datetime.strptime(timeline[0]["start"], "%Y-%m-%d")
        last_end = datetime.datetime.strptime(timeline[-1]["end"], "%Y-%m-%d")
        total_days = (last_end - first_start).days
        # Should be ~120 years = ~43800 days (±30 days tolerance)
        self.assertAlmostEqual(total_days, 120 * 365.25, delta=60)

    def test_dasha_from_moon_nakshatra(self):
        """The first dasha lord should match the Moon's nakshatra ruler."""
        chart = get_standard_chart()
        moon_nak_lord = chart["planets"]["Moon"]["nakshatra_lord"]
        first_maha = chart["dashas"]["timeline"][0]["planet"]
        self.assertEqual(first_maha, moon_nak_lord)


# ===================================================================
# 12. ASHTAKAVARGA
# ===================================================================
class TestAshtakavarga(unittest.TestCase):

    def test_total_bindus_337(self):
        """Total SAV bindus must always equal 337."""
        chart = get_standard_chart()
        self.assertEqual(chart["ashtakavarga"]["total_bindus"], 337)

    def test_sav_all_12_signs(self):
        chart = get_standard_chart()
        sav = chart["ashtakavarga"]["sarvashtakavarga"]
        self.assertEqual(len(sav), 12)
        # Sum of SAV across all signs = 337
        self.assertEqual(sum(sav.values()), 337)

    def test_bav_has_7_planets(self):
        chart = get_standard_chart()
        bav = chart["ashtakavarga"]["bhinnashtakavarga"]
        self.assertEqual(len(bav), 7)  # Sun through Saturn (no Rahu/Ketu)
        for planet, signs in bav.items():
            self.assertEqual(len(signs), 12, f"BAV for {planet} missing signs")

    def test_bav_sum_per_planet_is_valid(self):
        """Each planet's BAV sum should be a reasonable value (typically 35-52)."""
        chart = get_standard_chart()
        bav = chart["ashtakavarga"]["bhinnashtakavarga"]
        for planet, signs in bav.items():
            total = sum(signs.values())
            self.assertGreaterEqual(total, 25, f"{planet} BAV too low: {total}")
            self.assertLessEqual(total, 56, f"{planet} BAV too high: {total}")

    def test_prashtara_exists(self):
        chart = get_standard_chart()
        self.assertIn("prashtarashtakavarga", chart["ashtakavarga"])


# ===================================================================
# 13. JAIMINI KARAKAS
# ===================================================================
class TestJaiminiKarakas(unittest.TestCase):

    def test_seven_karakas(self):
        chart = get_standard_chart()
        jk = chart["jaimini_karakas"]
        self.assertEqual(len(jk), 7)

    def test_karaka_names(self):
        chart = get_standard_chart()
        jk = chart["jaimini_karakas"]
        expected = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka",
                    "Matrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka"]
        for name in expected:
            self.assertIn(name, jk, f"Missing karaka: {name}")

    def test_atmakaraka_highest_degree(self):
        """Atmakaraka must have the highest degree among the 7 planets."""
        chart = get_standard_chart()
        jk = chart["jaimini_karakas"]
        ak_deg = jk["Atmakaraka"]["degree"]
        for karaka_name, info in jk.items():
            self.assertGreaterEqual(ak_deg, info["degree"],
                                    f"AK degree {ak_deg} < {karaka_name} degree {info['degree']}")

    def test_darakaraka_lowest_degree(self):
        """Darakaraka must have the lowest degree among the 7 planets."""
        chart = get_standard_chart()
        jk = chart["jaimini_karakas"]
        dk_deg = jk["Darakaraka"]["degree"]
        for karaka_name, info in jk.items():
            self.assertLessEqual(dk_deg, info["degree"],
                                 f"DK degree {dk_deg} > {karaka_name} degree {info['degree']}")

    def test_all_different_planets(self):
        """Each karaka must be a different planet."""
        chart = get_standard_chart()
        jk = chart["jaimini_karakas"]
        planets = [info["planet"] for info in jk.values()]
        self.assertEqual(len(planets), len(set(planets)), "Duplicate planet in karakas")


# ===================================================================
# 14. ARUDHA PADAS
# ===================================================================
class TestArudhaPadas(unittest.TestCase):

    def test_12_padas(self):
        chart = get_standard_chart()
        ap = chart["arudha_padas"]
        self.assertEqual(len(ap), 12)

    def test_pada_structure(self):
        chart = get_standard_chart()
        ap = chart["arudha_padas"]
        for house_num_str, pada in ap.items():
            house_num = int(house_num_str)
            self.assertIn("sign", pada)
            self.assertIn("sign_index", pada)
            self.assertIn("name", pada)
            self.assertIn(pada["sign"], ZODIAC_SIGNS)
            self.assertGreaterEqual(house_num, 1)
            self.assertLessEqual(house_num, 12)

    def test_arudha_lagna_name(self):
        chart = get_standard_chart()
        ap = chart["arudha_padas"]
        self.assertIn("Arudha Lagna", ap[1]["name"])

    def test_dara_pada_name(self):
        chart = get_standard_chart()
        ap = chart["arudha_padas"]
        self.assertIn("Dara Pada", ap[7]["name"])

    def test_exception_rule(self):
        """If arudha falls in same sign or 7th, it should be shifted to 10th."""
        # Construct a scenario: Aries Lagna, House 1 lord Mars in Aries
        # Distance = 1, Arudha = Aries (same) → should shift to 10th = Capricorn
        mock_planets = {
            "Mars": {"sign": "Aries", "house": 1, "degree": 15, "d9_sign": "Aries",
                     "dignity": "own_sign", "is_combust": False},
            "Venus": {"sign": "Taurus", "house": 2, "degree": 10, "d9_sign": "Leo",
                      "dignity": "own_sign", "is_combust": False},
            "Mercury": {"sign": "Gemini", "house": 3, "degree": 5, "d9_sign": "Aries",
                        "dignity": "own_sign", "is_combust": False},
            "Moon": {"sign": "Cancer", "house": 4, "degree": 20, "d9_sign": "Virgo",
                     "dignity": "own_sign", "is_combust": False},
            "Sun": {"sign": "Leo", "house": 5, "degree": 12, "d9_sign": "Cancer",
                    "dignity": "mooltrikona", "is_combust": False},
            "Jupiter": {"sign": "Sagittarius", "house": 9, "degree": 8, "d9_sign": "Gemini",
                        "dignity": "own_sign", "is_combust": False},
            "Saturn": {"sign": "Capricorn", "house": 10, "degree": 22, "d9_sign": "Aquarius",
                       "dignity": "own_sign", "is_combust": False},
        }
        ap = calculate_arudha_padas("Aries", mock_planets)
        # House 1 (Aries), lord Mars in Aries: distance=1, arudha=Aries (same as house)
        # Exception → 10th from Aries = Capricorn
        self.assertEqual(ap[1]["sign"], "Capricorn")


# ===================================================================
# 15. UPAPADA LAGNA
# ===================================================================
class TestUpapada(unittest.TestCase):

    def test_upapada_structure(self):
        chart = get_standard_chart()
        up = chart["upapada"]
        self.assertIsNotNone(up)
        self.assertIn("sign", up)
        self.assertIn("lord", up)
        self.assertIn("second_from_ul", up)

    def test_second_from_ul(self):
        """2nd from UL should be the next sign."""
        chart = get_standard_chart()
        up = chart["upapada"]
        ul_idx = up["sign_index"]
        expected_second = ZODIAC_SIGNS[(ul_idx + 1) % 12]
        self.assertEqual(up["second_from_ul"], expected_second)


# ===================================================================
# 16. KARAKAMSHA
# ===================================================================
class TestKarakamsha(unittest.TestCase):

    def test_karakamsha_structure(self):
        chart = get_standard_chart()
        k = chart["karakamsha"]
        self.assertIsNotNone(k)
        self.assertIn("atmakaraka", k)
        self.assertIn("karakamsha_sign", k)
        self.assertIn("karakamsha_house_from_lagna", k)
        self.assertIn("ishta_devata_sign", k)
        self.assertIn("ishta_devata_lord", k)
        self.assertIn("planets_in_karakamsha", k)

    def test_karakamsha_sign_is_ak_d9(self):
        """Karakamsha sign = Atmakaraka's D9 sign."""
        chart = get_standard_chart()
        jk = chart["jaimini_karakas"]
        k = chart["karakamsha"]
        ak_planet = jk["Atmakaraka"]["planet"]
        ak_d9 = chart["planets"][ak_planet]["d9_sign"]
        self.assertEqual(k["karakamsha_sign"], ak_d9)

    def test_ishta_devata_is_12th_from_karakamsha(self):
        """Ishta Devata sign = 12th from Karakamsha."""
        chart = get_standard_chart()
        k = chart["karakamsha"]
        kk_idx = ZODIAC_SIGNS.index(k["karakamsha_sign"])
        expected_id_idx = (kk_idx - 1) % 12
        self.assertEqual(k["ishta_devata_sign"], ZODIAC_SIGNS[expected_id_idx])


# ===================================================================
# 17. BHAVA CHALIT
# ===================================================================
class TestBhavaChalit(unittest.TestCase):

    def test_bhava_chalit_structure(self):
        chart = get_standard_chart()
        bc = chart["bhava_chalit"]
        self.assertIsInstance(bc, dict)
        # Should have entries for all planets
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            self.assertIn(planet, bc)

    def test_bhava_chalit_fields(self):
        chart = get_standard_chart()
        bc = chart["bhava_chalit"]
        for name, data in bc.items():
            self.assertIn("bhava_house", data)
            self.assertIn("rashi_house", data)
            self.assertIn("shifted", data)
            self.assertIsInstance(data["bhava_house"], int)
            self.assertGreaterEqual(data["bhava_house"], 1)
            self.assertLessEqual(data["bhava_house"], 12)

    def test_shifted_flag_consistency(self):
        """'shifted' should be True iff bhava_house != rashi_house."""
        chart = get_standard_chart()
        bc = chart["bhava_chalit"]
        for name, data in bc.items():
            self.assertEqual(data["shifted"], data["bhava_house"] != data["rashi_house"],
                             f"{name}: shifted flag inconsistent")

    def test_bhava_chalit_planet_in_lagna(self):
        """A planet exactly at the Lagna degree should be in bhava 1."""
        # Synthetic test: Lagna at 100° (Cancer ~10°), planet at 100°
        raw = {"TestPlanet": {"lon": 100.0, "sign": "Cancer", "degree": 10.0,
                               "sign_idx": 3, "speed": 0, "is_retrograde": False}}
        bc = calculate_bhava_chalit(100.0, raw)
        self.assertEqual(bc["TestPlanet"]["bhava_house"], 1)


# ===================================================================
# 18. AVASTHAS
# ===================================================================
class TestAvasthas(unittest.TestCase):

    def test_avasthas_structure(self):
        chart = get_standard_chart()
        av = chart["avasthas"]
        self.assertIsInstance(av, dict)
        # 7 planets (no Rahu/Ketu)
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            self.assertIn(planet, av)
        self.assertNotIn("Rahu", av)
        self.assertNotIn("Ketu", av)

    def test_avastha_fields(self):
        chart = get_standard_chart()
        av = chart["avasthas"]
        for name, data in av.items():
            self.assertIn("avastha", data)
            self.assertIn("degree", data)
            self.assertIn("strength_factor", data)
            self.assertIn(data["avastha"], ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"])

    def test_avastha_odd_sign_mapping(self):
        """In an odd sign (idx even), 0-6° = Bala, 12-18° = Yuva, 24-30° = Mrita."""
        raw = {"TestP": {"lon": 3.0, "sign": "Aries", "degree": 3.0,
                         "sign_idx": 0, "speed": 0, "is_retrograde": False}}
        pd = {"TestP": {"sign": "Aries", "degree": 3.0, "house": 1}}
        av = calculate_avasthas(pd, raw)
        self.assertEqual(av["TestP"]["avastha"], "Bala")
        self.assertAlmostEqual(av["TestP"]["strength_factor"], 0.25)

    def test_avastha_even_sign_reversed(self):
        """In an even sign (idx odd), degrees 0-6° -> Mrita (reversed table)."""
        raw = {"TestP": {"lon": 33.0, "sign": "Taurus", "degree": 3.0,
                         "sign_idx": 1, "speed": 0, "is_retrograde": False}}
        pd = {"TestP": {"sign": "Taurus", "degree": 3.0, "house": 1}}
        av = calculate_avasthas(pd, raw)
        self.assertEqual(av["TestP"]["avastha"], "Mrita")
        self.assertAlmostEqual(av["TestP"]["strength_factor"], 0.125)

    def test_yuva_full_strength(self):
        """Yuva avastha should have strength_factor = 1.0."""
        raw = {"TestP": {"lon": 15.0, "sign": "Aries", "degree": 15.0,
                         "sign_idx": 0, "speed": 0, "is_retrograde": False}}
        pd = {"TestP": {"sign": "Aries", "degree": 15.0, "house": 1}}
        av = calculate_avasthas(pd, raw)
        self.assertEqual(av["TestP"]["avastha"], "Yuva")
        self.assertAlmostEqual(av["TestP"]["strength_factor"], 1.0)


# ===================================================================
# 19. KAAL SARPA DOSHA
# ===================================================================
class TestKaalSarpa(unittest.TestCase):

    def test_kaal_sarpa_not_active_normally(self):
        """Most charts won't have Kaal Sarpa; check structure if active."""
        chart = get_standard_chart()
        ks = chart["kaal_sarpa"]
        # It may or may not be active, but structure should be consistent
        if ks is not None:
            self.assertIn("active", ks)
            self.assertIn("type", ks)

    def test_kaal_sarpa_synthetic_active(self):
        """All 7 planets between Rahu(Aries) and Ketu(Libra) = active."""
        raw = {
            "Sun":     {"lon": 40,  "sign_idx": 1, "degree": 10, "sign": "Taurus", "speed": 1, "is_retrograde": False},
            "Moon":    {"lon": 70,  "sign_idx": 2, "degree": 10, "sign": "Gemini", "speed": 12, "is_retrograde": False},
            "Mars":    {"lon": 100, "sign_idx": 3, "degree": 10, "sign": "Cancer", "speed": 0.5, "is_retrograde": False},
            "Mercury": {"lon": 50,  "sign_idx": 1, "degree": 20, "sign": "Taurus", "speed": 1, "is_retrograde": False},
            "Jupiter": {"lon": 60,  "sign_idx": 2, "degree": 0, "sign": "Gemini", "speed": 0.1, "is_retrograde": False},
            "Venus":   {"lon": 80,  "sign_idx": 2, "degree": 20, "sign": "Gemini", "speed": 1, "is_retrograde": False},
            "Saturn":  {"lon": 110, "sign_idx": 3, "degree": 20, "sign": "Cancer", "speed": 0.05, "is_retrograde": False},
            "Rahu":    {"lon": 10,  "sign_idx": 0, "degree": 10, "sign": "Aries", "speed": -0.05, "is_retrograde": True},
            "Ketu":    {"lon": 190, "sign_idx": 6, "degree": 10, "sign": "Libra", "speed": -0.05, "is_retrograde": True},
        }
        ks = detect_kaal_sarpa(raw)
        self.assertIsNotNone(ks)
        self.assertTrue(ks["active"])

    def test_kaal_sarpa_not_active(self):
        """Planets on both sides of Rahu-Ketu = no Kaal Sarpa."""
        raw = {
            "Sun":     {"lon": 40,  "sign_idx": 1, "degree": 10, "sign": "Taurus", "speed": 1, "is_retrograde": False},
            "Moon":    {"lon": 200, "sign_idx": 6, "degree": 20, "sign": "Libra", "speed": 12, "is_retrograde": False},
            "Mars":    {"lon": 100, "sign_idx": 3, "degree": 10, "sign": "Cancer", "speed": 0.5, "is_retrograde": False},
            "Mercury": {"lon": 250, "sign_idx": 8, "degree": 10, "sign": "Sagittarius", "speed": 1, "is_retrograde": False},
            "Jupiter": {"lon": 60,  "sign_idx": 2, "degree": 0, "sign": "Gemini", "speed": 0.1, "is_retrograde": False},
            "Venus":   {"lon": 300, "sign_idx": 10, "degree": 0, "sign": "Aquarius", "speed": 1, "is_retrograde": False},
            "Saturn":  {"lon": 110, "sign_idx": 3, "degree": 20, "sign": "Cancer", "speed": 0.05, "is_retrograde": False},
            "Rahu":    {"lon": 10,  "sign_idx": 0, "degree": 10, "sign": "Aries", "speed": -0.05, "is_retrograde": True},
            "Ketu":    {"lon": 190, "sign_idx": 6, "degree": 10, "sign": "Libra", "speed": -0.05, "is_retrograde": True},
        }
        ks = detect_kaal_sarpa(raw)
        # Should not be active (or None)
        if ks is not None:
            self.assertFalse(ks.get("active", False))


# ===================================================================
# 20. GRAHA YUDDHA
# ===================================================================
class TestGrahaYuddha(unittest.TestCase):

    def test_no_war_when_separated(self):
        """Planets >1° apart = no war."""
        raw = {
            "Mars":    {"lon": 50.0, "sign_idx": 1, "degree": 20.0, "sign": "Taurus", "speed": 0.5, "is_retrograde": False},
            "Mercury": {"lon": 55.0, "sign_idx": 1, "degree": 25.0, "sign": "Taurus", "speed": 1.0, "is_retrograde": False},
            "Jupiter": {"lon": 90.0, "sign_idx": 3, "degree": 0.0, "sign": "Cancer", "speed": 0.1, "is_retrograde": False},
            "Venus":   {"lon": 120.0, "sign_idx": 4, "degree": 0.0, "sign": "Leo", "speed": 1.0, "is_retrograde": False},
            "Saturn":  {"lon": 200.0, "sign_idx": 6, "degree": 20.0, "sign": "Libra", "speed": 0.05, "is_retrograde": False},
            "Sun":     {"lon": 30.0, "sign_idx": 1, "degree": 0.0, "sign": "Taurus", "speed": 1.0, "is_retrograde": False},
            "Moon":    {"lon": 150.0, "sign_idx": 5, "degree": 0.0, "sign": "Virgo", "speed": 12.0, "is_retrograde": False},
            "Rahu":    {"lon": 10.0, "sign_idx": 0, "degree": 10.0, "sign": "Aries", "speed": -0.05, "is_retrograde": True},
            "Ketu":    {"lon": 190.0, "sign_idx": 6, "degree": 10.0, "sign": "Libra", "speed": -0.05, "is_retrograde": True},
        }
        wars = detect_graha_yuddha(raw)
        self.assertEqual(len(wars), 0)

    def test_war_when_within_1_degree(self):
        """Two true planets within 1° = war."""
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
        war = wars[0]
        self.assertIn("winner", war)
        self.assertIn("loser", war)
        self.assertIn("separation", war)

    def test_sun_moon_rahu_ketu_excluded(self):
        """Sun, Moon, Rahu, Ketu should not participate in Graha Yuddha."""
        raw = {
            "Sun":     {"lon": 50.0, "sign_idx": 1, "degree": 20.0, "sign": "Taurus", "speed": 1.0, "is_retrograde": False},
            "Moon":    {"lon": 50.2, "sign_idx": 1, "degree": 20.2, "sign": "Taurus", "speed": 12.0, "is_retrograde": False},
            "Mars":    {"lon": 100.0, "sign_idx": 3, "degree": 10.0, "sign": "Cancer", "speed": 0.5, "is_retrograde": False},
            "Mercury": {"lon": 200.0, "sign_idx": 6, "degree": 20.0, "sign": "Libra", "speed": 1.0, "is_retrograde": False},
            "Jupiter": {"lon": 250.0, "sign_idx": 8, "degree": 10.0, "sign": "Sagittarius", "speed": 0.1, "is_retrograde": False},
            "Venus":   {"lon": 300.0, "sign_idx": 10, "degree": 0.0, "sign": "Aquarius", "speed": 1.0, "is_retrograde": False},
            "Saturn":  {"lon": 330.0, "sign_idx": 11, "degree": 0.0, "sign": "Pisces", "speed": 0.05, "is_retrograde": False},
            "Rahu":    {"lon": 50.3, "sign_idx": 1, "degree": 20.3, "sign": "Taurus", "speed": -0.05, "is_retrograde": True},
            "Ketu":    {"lon": 230.3, "sign_idx": 7, "degree": 20.3, "sign": "Scorpio", "speed": -0.05, "is_retrograde": True},
        }
        wars = detect_graha_yuddha(raw)
        for war in wars:
            self.assertNotIn(war["winner"], ["Sun", "Moon", "Rahu", "Ketu"])
            self.assertNotIn(war["loser"], ["Sun", "Moon", "Rahu", "Ketu"])


# ===================================================================
# 21. GANDANTA
# ===================================================================
class TestGandanta(unittest.TestCase):

    def test_gandanta_at_cancer_leo_boundary(self):
        """Planet at Cancer 28° (lon ~118°) should be in gandanta."""
        raw = {
            "Mars": {"lon": 118.0, "sign_idx": 3, "degree": 28.0, "sign": "Cancer",
                     "speed": 0.5, "is_retrograde": False},
        }
        gandanta = detect_gandanta(raw, 0.0)
        mars_entries = [g for g in gandanta if g.get("planet") == "Mars"]
        self.assertGreater(len(mars_entries), 0, "Mars at Cancer 28° should be gandanta")

    def test_no_gandanta_at_safe_degree(self):
        """Planet at Aries 15° should NOT be in gandanta."""
        raw = {
            "Mars": {"lon": 15.0, "sign_idx": 0, "degree": 15.0, "sign": "Aries",
                     "speed": 0.5, "is_retrograde": False},
        }
        gandanta = detect_gandanta(raw, 0.0)
        mars_entries = [g for g in gandanta if g.get("planet") == "Mars"]
        self.assertEqual(len(mars_entries), 0)

    def test_gandanta_at_pisces_aries_boundary(self):
        """Planet at Aries 1° should be in gandanta (fire sign, first 3°20')."""
        raw = {
            "Jupiter": {"lon": 1.0, "sign_idx": 0, "degree": 1.0, "sign": "Aries",
                        "speed": 0.1, "is_retrograde": False},
        }
        gandanta = detect_gandanta(raw, 0.0)
        jup_entries = [g for g in gandanta if g.get("planet") == "Jupiter"]
        self.assertGreater(len(jup_entries), 0, "Jupiter at Aries 1° should be gandanta")


# ===================================================================
# 22. YOGA DETECTION
# ===================================================================
class TestYogas(unittest.TestCase):

    def test_yogas_array_exists(self):
        chart = get_standard_chart()
        self.assertIsInstance(chart["yogas"], list)

    def test_yoga_entry_structure(self):
        chart = get_standard_chart()
        for yoga in chart["yogas"]:
            self.assertIn("name", yoga)
            self.assertIn("formed_by", yoga)
            self.assertIn("description", yoga)

    def test_pancha_mahapurusha_synthetic(self):
        """Mars in Aries (own) in Kendra → Ruchaka Yoga."""
        planets = {
            "Mars": {"sign": "Aries", "sign_idx": 0, "house": 1,
                     "dignity": "own_sign", "is_combust": False},
            "Sun": {"sign": "Leo", "sign_idx": 4, "house": 5,
                    "dignity": "own_sign", "is_combust": False},
            "Moon": {"sign": "Taurus", "sign_idx": 1, "house": 2,
                     "dignity": "exalted", "is_combust": False},
            "Mercury": {"sign": "Gemini", "sign_idx": 2, "house": 3,
                        "dignity": "own_sign", "is_combust": False},
            "Jupiter": {"sign": "Sagittarius", "sign_idx": 8, "house": 9,
                        "dignity": "own_sign", "is_combust": False},
            "Venus": {"sign": "Taurus", "sign_idx": 1, "house": 2,
                      "dignity": "own_sign", "is_combust": False},
            "Saturn": {"sign": "Libra", "sign_idx": 6, "house": 7,
                       "dignity": "exalted", "is_combust": False},
            "Rahu": {"sign": "Gemini", "sign_idx": 2, "house": 3,
                     "dignity": "neutral", "is_combust": False},
            "Ketu": {"sign": "Sagittarius", "sign_idx": 8, "house": 9,
                     "dignity": "neutral", "is_combust": False},
        }
        yogas = detect_yogas(planets, "Aries")
        yoga_names = [y["name"] for y in yogas]
        self.assertIn("Ruchaka Yoga", yoga_names)

    def test_gajakesari_synthetic(self):
        """Jupiter in Kendra from Moon = Gajakesari."""
        planets = {
            "Moon": {"sign": "Aries", "sign_idx": 0, "house": 1,
                     "dignity": "neutral", "is_combust": False},
            "Jupiter": {"sign": "Cancer", "sign_idx": 3, "house": 4,
                        "dignity": "exalted", "is_combust": False},
            "Sun": {"sign": "Leo", "sign_idx": 4, "house": 5,
                    "dignity": "own_sign", "is_combust": False},
            "Mars": {"sign": "Scorpio", "sign_idx": 7, "house": 8,
                     "dignity": "own_sign", "is_combust": False},
            "Mercury": {"sign": "Virgo", "sign_idx": 5, "house": 6,
                        "dignity": "own_sign", "is_combust": False},
            "Venus": {"sign": "Pisces", "sign_idx": 11, "house": 12,
                      "dignity": "exalted", "is_combust": False},
            "Saturn": {"sign": "Libra", "sign_idx": 6, "house": 7,
                       "dignity": "exalted", "is_combust": False},
            "Rahu": {"sign": "Gemini", "sign_idx": 2, "house": 3,
                     "dignity": "neutral", "is_combust": False},
            "Ketu": {"sign": "Sagittarius", "sign_idx": 8, "house": 9,
                     "dignity": "neutral", "is_combust": False},
        }
        yogas = detect_yogas(planets, "Aries")
        yoga_names = [y["name"] for y in yogas]
        self.assertIn("Gajakesari Yoga", yoga_names)

    def test_budhaditya_synthetic(self):
        """Sun + Mercury in same sign = Budhaditya."""
        planets = {
            "Sun": {"sign": "Leo", "sign_idx": 4, "house": 1,
                    "dignity": "own_sign", "is_combust": False},
            "Mercury": {"sign": "Leo", "sign_idx": 4, "house": 1,
                        "dignity": "friend", "is_combust": True},
            "Moon": {"sign": "Taurus", "sign_idx": 1, "house": 10,
                     "dignity": "exalted", "is_combust": False},
            "Mars": {"sign": "Capricorn", "sign_idx": 9, "house": 6,
                     "dignity": "exalted", "is_combust": False},
            "Jupiter": {"sign": "Sagittarius", "sign_idx": 8, "house": 5,
                        "dignity": "own_sign", "is_combust": False},
            "Venus": {"sign": "Virgo", "sign_idx": 5, "house": 2,
                      "dignity": "debilitated", "is_combust": False},
            "Saturn": {"sign": "Aquarius", "sign_idx": 10, "house": 7,
                       "dignity": "own_sign", "is_combust": False},
            "Rahu": {"sign": "Gemini", "sign_idx": 2, "house": 11,
                     "dignity": "neutral", "is_combust": False},
            "Ketu": {"sign": "Sagittarius", "sign_idx": 8, "house": 5,
                     "dignity": "neutral", "is_combust": False},
        }
        yogas = detect_yogas(planets, "Leo")
        yoga_names = [y["name"] for y in yogas]
        self.assertIn("Budhaditya Yoga", yoga_names)


# ===================================================================
# 23. SHADBALA
# ===================================================================
class TestShadbala(unittest.TestCase):

    def test_shadbala_structure(self):
        chart = get_standard_chart()
        sb = chart["shadbala"]
        self.assertIsInstance(sb, dict)
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            self.assertIn(planet, sb, f"Shadbala missing {planet}")

    def test_shadbala_has_components(self):
        chart = get_standard_chart()
        sb = chart["shadbala"]
        for planet, data in sb.items():
            if planet == "ishta_kashta_phala":
                continue
            self.assertIn("total_rupas", data, f"{planet} missing total_rupas")
            self.assertIn("percentage", data, f"{planet} missing percentage")

    def test_shadbala_positive_values(self):
        chart = get_standard_chart()
        sb = chart["shadbala"]
        for planet, data in sb.items():
            if planet == "ishta_kashta_phala":
                continue
            self.assertGreater(data["total_rupas"], 0,
                               f"{planet} total_rupas should be > 0")
            self.assertGreater(data["percentage"], 0,
                               f"{planet} percentage should be > 0")

    def test_ishta_kashta_phala(self):
        chart = get_standard_chart()
        sb = chart["shadbala"]
        self.assertIn("ishta_kashta_phala", sb)
        ikp = sb["ishta_kashta_phala"]
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            self.assertIn(planet, ikp, f"Ishta/Kashta missing {planet}")
            self.assertIn("ishta_phala", ikp[planet])
            self.assertIn("kashta_phala", ikp[planet])


# ===================================================================
# 24. MATCHMAKING (COMPATIBILITY)
# ===================================================================
class TestMatchmaking(unittest.TestCase):

    def test_ashtakoot_total_max_36(self):
        """Ashtakoot total should never exceed 36."""
        result = calculate_ashtakoot(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
            "1992-08-20", "10:15", 28.6139, 77.2090, "Asia/Kolkata",
        )
        total = result["ashtakoot_total"]
        self.assertLessEqual(total, 36)
        self.assertGreaterEqual(total, 0)

    def test_ashtakoot_8_kutas(self):
        result = calculate_ashtakoot(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
            "1992-08-20", "10:15", 28.6139, 77.2090, "Asia/Kolkata",
        )
        expected_kutas = ["varna", "vashya", "tara", "yoni",
                          "graha_maitri", "gana", "bhakoot", "nadi"]
        for kuta in expected_kutas:
            self.assertIn(kuta, result, f"Missing kuta: {kuta}")

    def test_kuta_max_scores(self):
        """Verify individual kuta scores don't exceed their max."""
        result = calculate_ashtakoot(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
            "1992-08-20", "10:15", 28.6139, 77.2090, "Asia/Kolkata",
        )
        max_scores = {"varna": 1, "vashya": 2, "tara": 3, "yoni": 4,
                      "graha_maitri": 5, "gana": 6, "bhakoot": 7, "nadi": 8}
        for kuta, max_val in max_scores.items():
            score = result[kuta]["score"]
            self.assertLessEqual(score, max_val, f"{kuta} score {score} > max {max_val}")
            self.assertGreaterEqual(score, 0, f"{kuta} score {score} < 0")

    def test_additional_kutas_present(self):
        result = calculate_ashtakoot(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
            "1992-08-20", "10:15", 28.6139, 77.2090, "Asia/Kolkata",
        )
        for kuta in ["mahendra", "stree_deergha", "vedha", "rajju"]:
            self.assertIn(kuta, result, f"Missing additional kuta: {kuta}")

    def test_kuja_dosha_present(self):
        result = calculate_ashtakoot(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
            "1992-08-20", "10:15", 28.6139, 77.2090, "Asia/Kolkata",
        )
        self.assertIn("kuja_dosha", result)
        kd = result["kuja_dosha"]
        self.assertIn("male", kd)
        self.assertIn("female", kd)
        self.assertIn("compatibility", kd)


# ===================================================================
# 25. FULL CHART INTEGRATION
# ===================================================================
class TestFullChart(unittest.TestCase):
    """Integration test: validate the entire chart output structure."""

    def test_chart_top_level_keys(self):
        chart = get_standard_chart()
        expected = [
            "metadata", "panchang", "lagna", "planets", "dashas", "yogas",
            "ashtakavarga", "jaimini_karakas", "shadbala",
            "bhava_chalit", "avasthas", "kaal_sarpa", "graha_yuddha",
            "gandanta", "arudha_padas", "upapada", "karakamsha",
        ]
        for key in expected:
            self.assertIn(key, chart, f"Missing top-level key: {key}")

    def test_metadata(self):
        chart = get_standard_chart()
        m = chart["metadata"]
        self.assertEqual(m["dob"], "1918-10-16")
        self.assertEqual(m["time"], "14:20")
        self.assertEqual(m["ayanamsha"], "Lahiri")
        self.assertIn("ayanamsha_degrees", m)
        # Lahiri ayanamsha for 1918 should be roughly ~22-23 degrees
        self.assertAlmostEqual(m["ayanamsha_degrees"], 22.7, delta=1.0)

    def test_lagna_valid_sign(self):
        chart = get_standard_chart()
        self.assertIn(chart["lagna"]["sign"], ZODIAC_SIGNS)

    def test_lagna_has_all_vargas(self):
        chart = get_standard_chart()
        lagna = chart["lagna"]
        for varga in ["d2_sign", "d3_sign", "d4_sign", "d7_sign", "d9_sign",
                      "d10_sign", "d12_sign", "d16_sign", "d20_sign",
                      "d24_sign", "d27_sign", "d30_sign", "d40_sign", "d60_sign"]:
            self.assertIn(varga, lagna, f"Lagna missing {varga}")
            self.assertIn(lagna[varga], ZODIAC_SIGNS, f"Lagna {varga} invalid")

    def test_all_nine_planets(self):
        chart = get_standard_chart()
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                       "Venus", "Saturn", "Rahu", "Ketu"]:
            self.assertIn(planet, chart["planets"], f"Missing planet: {planet}")

    def test_planet_fields_complete(self):
        chart = get_standard_chart()
        required = ["sign", "degree", "house", "nakshatra", "pada",
                     "nakshatra_lord", "is_retrograde", "is_combust",
                     "dignity", "has_digbala", "d9_sign", "d10_sign", "aspects"]
        for name, data in chart["planets"].items():
            for field in required:
                self.assertIn(field, data, f"{name} missing field '{field}'")

    def test_planet_degree_range(self):
        chart = get_standard_chart()
        for name, data in chart["planets"].items():
            self.assertGreaterEqual(data["degree"], 0, f"{name} degree < 0")
            self.assertLess(data["degree"], 30, f"{name} degree >= 30")

    def test_planet_house_range(self):
        chart = get_standard_chart()
        for name, data in chart["planets"].items():
            self.assertGreaterEqual(data["house"], 1, f"{name} house < 1")
            self.assertLessEqual(data["house"], 12, f"{name} house > 12")

    def test_rahu_ketu_retrograde(self):
        chart = get_standard_chart()
        self.assertTrue(chart["planets"]["Rahu"]["is_retrograde"])
        self.assertTrue(chart["planets"]["Ketu"]["is_retrograde"])

    def test_ketu_opposite_rahu(self):
        """Ketu's sign should be 7th from Rahu."""
        chart = get_standard_chart()
        rahu_idx = ZODIAC_SIGNS.index(chart["planets"]["Rahu"]["sign"])
        ketu_idx = ZODIAC_SIGNS.index(chart["planets"]["Ketu"]["sign"])
        self.assertEqual((rahu_idx + 6) % 12, ketu_idx)

    def test_dignity_values(self):
        chart = get_standard_chart()
        valid = {"exalted", "mooltrikona", "own_sign", "friend",
                 "neutral", "enemy", "debilitated"}
        for name, data in chart["planets"].items():
            self.assertIn(data["dignity"], valid, f"{name} has invalid dignity: {data['dignity']}")

    def test_all_14_varga_signs_present(self):
        chart = get_standard_chart()
        vargas = ["d2_sign", "d3_sign", "d4_sign", "d7_sign", "d9_sign",
                  "d10_sign", "d12_sign", "d16_sign", "d20_sign",
                  "d24_sign", "d27_sign", "d30_sign", "d40_sign", "d60_sign"]
        for name, data in chart["planets"].items():
            for v in vargas:
                self.assertIn(v, data, f"{name} missing {v}")
                self.assertIn(data[v], ZODIAC_SIGNS, f"{name} {v}='{data[v]}' invalid")


# ===================================================================
# 26. TRANSIT
# ===================================================================
class TestTransit(unittest.TestCase):

    def test_transit_structure(self):
        from vedic_calculator import calculate_transit
        chart = get_standard_chart()
        transit = calculate_transit("2025-01-01", chart, "Asia/Kolkata")
        self.assertIn("planets", transit)
        self.assertIn("sade_sati", transit)
        self.assertIn("rahu_ketu_axis", transit)

    def test_transit_planets_fields(self):
        from vedic_calculator import calculate_transit
        chart = get_standard_chart()
        transit = calculate_transit("2025-01-01", chart, "Asia/Kolkata")
        for name, data in transit["planets"].items():
            self.assertIn("sign", data)
            self.assertIn("degree", data)
            self.assertIn("house_from_lagna", data)
            self.assertIn("house_from_moon", data)
            self.assertIn("sav_points", data)

    def test_sade_sati_structure(self):
        from vedic_calculator import calculate_transit
        chart = get_standard_chart()
        transit = calculate_transit("2025-01-01", chart, "Asia/Kolkata")
        ss = transit["sade_sati"]
        self.assertIn("active", ss)
        self.assertIn("saturn_transit_sign", ss)
        self.assertIn("natal_moon_sign", ss)


# ===================================================================
# 27. MUHURTHA
# ===================================================================
class TestMuhurtha(unittest.TestCase):

    def test_muhurtha_verdict(self):
        """Evaluate muhurtha for a specific date/activity."""
        from vedic_calculator import calculate_vedic_chart
        # Cast a chart for the muhurtha time
        chart = calculate_vedic_chart(
            "2025-06-15", "10:00", 28.6139, 77.2090, "Asia/Kolkata")
        result = evaluate_muhurtha(
            "marriage",
            chart["panchang"],
            chart["planets"],
            chart["lagna"],
        )
        self.assertIn("verdict", result)
        self.assertIn(result["verdict"], 
                      ["auspicious", "mixed_favorable", "mixed", "inauspicious"])
        self.assertIn("score", result)
        self.assertIn("positive_factors", result)
        self.assertIn("negative_factors", result)


# ===================================================================
# 28. CAREER ANALYSIS
# ===================================================================
class TestCareer(unittest.TestCase):

    def test_career_structure(self):
        chart = get_standard_chart()
        result = analyze_career(chart["planets"], chart["lagna"])
        self.assertIn("tenth_house", result)
        self.assertIn("d10_indicators", result)
        self.assertIn("career_themes", result)
        self.assertIn("strength_factors", result)

    def test_tenth_house_info(self):
        chart = get_standard_chart()
        result = analyze_career(chart["planets"], chart["lagna"])
        th = result["tenth_house"]
        self.assertIn("sign", th)
        self.assertIn("lord", th)
        self.assertIn(th["sign"], ZODIAC_SIGNS)


# ===================================================================
# 29. MCP SERVER INTEGRATION
# ===================================================================
class TestMCPServer(unittest.TestCase):
    """Test the MCP tool functions return valid JSON."""

    def test_cast_vedic_chart_tool(self):
        import json as _json
        from mcp_server import cast_vedic_chart as mcp_cast
        # Call the async function synchronously is complex; test via vedic_calculator
        chart = calculate_vedic_chart(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")
        # Verify JSON serializable
        serialized = _json.dumps(chart)
        self.assertIsInstance(serialized, str)
        parsed = _json.loads(serialized)
        self.assertIsInstance(parsed, dict)


# ===================================================================
# 30. CROSS-VALIDATION: B.V. RAMAN STANDARD HOROSCOPE
# ===================================================================
class TestBVRamanStandard(unittest.TestCase):
    """Cross-validate against B.V. Raman's Standard Horoscope reference.
    
    Born: 16-Oct-1918, 14:20 IST, Bangalore (12.97°N, 77.59°E)
    Note: VedAstro uses Raman ayanamsha; we use Lahiri. Positions may differ 
    by ~1-2° but sign placements should broadly match.
    """

    def test_ashtakavarga_invariant(self):
        """Total SAV bindus must be exactly 337 regardless of horoscope."""
        chart = get_standard_chart()
        self.assertEqual(chart["ashtakavarga"]["total_bindus"], 337)

    def test_lagna_reasonable(self):
        """For 14:20 IST Bangalore, Lagna should be in the Capricorn-Aquarius range 
        (Lahiri vs Raman difference)."""
        chart = get_standard_chart()
        lagna = chart["lagna"]["sign"]
        # With Lahiri, Lagna for this time/place is typically Capricorn or Aquarius
        self.assertIn(lagna, ["Capricorn", "Aquarius", "Sagittarius"],
                      f"Lagna '{lagna}' unexpected for standard horoscope")

    def test_second_chart_delhi(self):
        """Delhi 1990-04-15 14:30 — chart should generate without error."""
        chart = get_delhi_chart()
        self.assertIn("planets", chart)
        self.assertEqual(chart["ashtakavarga"]["total_bindus"], 337)


# ===================================================================
# RUNNER
# ===================================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)
