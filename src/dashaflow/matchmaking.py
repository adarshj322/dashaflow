from .constants import ZODIAC_SIGNS, SIGN_LORDS, NATURAL_FRIENDS, NATURAL_ENEMIES, EXALTATION, DEBILITATION, OWN_SIGNS
from .nakshatra import get_nakshatra
import math

# --- Data Tables ---
# 0-26 indexed Nakshatras
YONI_ANIMALS = [
    "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat", # 0-8
    "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer", # 9-17
    "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse", "Lion", "Cow", "Elephant" # 18-26
]

YONI_ENEMIES = {
    "Horse": "Buffalo", "Buffalo": "Horse",
    "Elephant": "Lion", "Lion": "Elephant",
    "Sheep": "Monkey", "Monkey": "Sheep",
    "Serpent": "Mongoose", "Mongoose": "Serpent",
    "Dog": "Deer", "Deer": "Dog",
    "Cat": "Rat", "Rat": "Cat",
    "Cow": "Tiger", "Tiger": "Cow"
}

GANA = [
    "Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa",
    "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa",
    "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"
]

NADI = [
    "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya",
    "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi",
    "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya"
]

VARNA = {
    "Cancer": 1, "Scorpio": 1, "Pisces": 1, # Brahmin
    "Aries": 2, "Leo": 2, "Sagittarius": 2, # Kshatriya
    "Taurus": 3, "Virgo": 3, "Capricorn": 3, # Vaishya
    "Gemini": 4, "Libra": 4, "Aquarius": 4 # Shudra
}

# 1. Varna (1 point)
def calc_varna(m_sign, f_sign):
    m_varna = VARNA[m_sign]
    f_varna = VARNA[f_sign]
    return 1.0 if m_varna <= f_varna else 0.0

# 2. Vashya (2 points) — Full BPHS classification
# Sign categories: Chatushpada (quadruped), Manava (human), Jalachara (water),
# Vanachara (wild/forest), Keet (insect/reptile)
VASHYA_TYPE = {
    "Aries": "Chatushpada", "Taurus": "Chatushpada",
    "Leo": "Vanachara", "Sagittarius": "Chatushpada",  # 2nd half is Manava
    "Capricorn": "Chatushpada",  # 1st half is Chatushpada
    "Gemini": "Manava", "Virgo": "Manava", "Libra": "Manava",
    "Aquarius": "Manava",  # 1st half is Manava
    "Cancer": "Jalachara", "Pisces": "Jalachara",
    "Scorpio": "Keet",
}

# Vashya compatibility scoring matrix
VASHYA_MATRIX = {
    ("Chatushpada", "Chatushpada"): 2.0,
    ("Manava", "Manava"): 2.0,
    ("Jalachara", "Jalachara"): 2.0,
    ("Vanachara", "Vanachara"): 2.0,
    ("Keet", "Keet"): 2.0,
    ("Chatushpada", "Manava"): 0.5,
    ("Manava", "Chatushpada"): 0.5,
    ("Manava", "Jalachara"): 1.0,
    ("Jalachara", "Manava"): 1.0,
    ("Chatushpada", "Jalachara"): 0.5,
    ("Jalachara", "Chatushpada"): 0.5,
    ("Vanachara", "Chatushpada"): 0.0,  # Wild eats quadruped
    ("Chatushpada", "Vanachara"): 0.0,
    ("Keet", "Chatushpada"): 0.0,
    ("Chatushpada", "Keet"): 0.0,
    ("Vanachara", "Manava"): 0.5,
    ("Manava", "Vanachara"): 0.5,
    ("Keet", "Manava"): 0.5,
    ("Manava", "Keet"): 0.5,
    ("Vanachara", "Jalachara"): 0.5,
    ("Jalachara", "Vanachara"): 0.5,
    ("Keet", "Jalachara"): 1.0,
    ("Jalachara", "Keet"): 1.0,
    ("Vanachara", "Keet"): 1.0,
    ("Keet", "Vanachara"): 1.0,
}

def calc_vashya(m_sign, f_sign):
    if m_sign == f_sign:
        return 2.0
    m_type = VASHYA_TYPE.get(m_sign, "Manava")
    f_type = VASHYA_TYPE.get(f_sign, "Manava")
    return VASHYA_MATRIX.get((m_type, f_type), 1.0)

# 3. Tara (3 points)
def calc_tara(m_nak_idx, f_nak_idx):
    m_to_f = (f_nak_idx - m_nak_idx) % 9
    f_to_m = (m_nak_idx - f_nak_idx) % 9
    pts = 0.0
    if m_to_f not in (2, 4, 6): pts += 1.5
    if f_to_m not in (2, 4, 6): pts += 1.5
    return pts

# 4. Yoni (4 points)
def calc_yoni(m_nak_idx, f_nak_idx):
    m_yoni = YONI_ANIMALS[m_nak_idx]
    f_yoni = YONI_ANIMALS[f_nak_idx]
    if m_yoni == f_yoni:
        return 4.0
    if YONI_ENEMIES.get(m_yoni) == f_yoni:
        return 0.0
    return 2.0 # Neutral

# 5. Graha Maitri (5 points)
def check_friendship(p1, p2):
    if p1 == p2:
        return 1.0 # Same lord
    if p2 in NATURAL_FRIENDS.get(p1, []):
        return 1.0
    if p2 in NATURAL_ENEMIES.get(p1, []):
        return 0.0
    return 0.5 # Neutral

def calc_graha_maitri(m_sign, f_sign):
    m_lord = SIGN_LORDS[m_sign]
    f_lord = SIGN_LORDS[f_sign]
    m_to_f = check_friendship(m_lord, f_lord)
    f_to_m = check_friendship(f_lord, m_lord)
    
    total = m_to_f + f_to_m
    if total == 2.0: return 5.0
    if total == 1.5: return 4.0
    if total == 1.0: return 3.0
    if total == 0.5: return 1.0
    return 0.0

# 6. Gana (6 points)
def calc_gana(m_nak_idx, f_nak_idx):
    m_gana = GANA[m_nak_idx]
    f_gana = GANA[f_nak_idx]
    if m_gana == f_gana: return 6.0
    if m_gana == "Deva" and f_gana == "Manushya": return 6.0
    if m_gana == "Manushya" and f_gana == "Deva": return 5.0
    if m_gana == "Rakshasa" and f_gana == "Manushya": return 0.0
    if f_gana == "Rakshasa" and m_gana == "Manushya": return 0.0
    if m_gana == "Rakshasa" and f_gana == "Deva": return 1.0
    if f_gana == "Rakshasa" and m_gana == "Deva": return 0.0
    return 0.0

# 7. Bhakoot (7 points)
def calc_bhakoot(m_sign, f_sign):
    m_idx = ZODIAC_SIGNS.index(m_sign)
    f_idx = ZODIAC_SIGNS.index(f_sign)
    diff = (f_idx - m_idx) % 12 + 1
    if diff in (1, 7, 3, 11, 4, 10):
        return 7.0
    return 0.0

# 8. Nadi (8 points)
def calc_nadi(m_nak_idx, f_nak_idx):
    m_nadi = NADI[m_nak_idx]
    f_nadi = NADI[f_nak_idx]
    if m_nadi != f_nadi:
        return 8.0
    return 0.0 # Nadi Dosha


# ==========================================
# ADDITIONAL KUTAS (beyond 36-point Ashtakoot)
# ==========================================

# 9. Mahendra Kuta — longevity and well-being
def calc_mahendra(m_nak_idx, f_nak_idx):
    """Male's nakshatra counted from female's. Auspicious if 4,7,10,13,16,19,22,25."""
    count = ((m_nak_idx - f_nak_idx) % 27) + 1
    return "good" if count in (4, 7, 10, 13, 16, 19, 22, 25) else "bad"


# 10. Stree Deergha — husband's longevity
def calc_stree_deergha(m_nak_idx, f_nak_idx):
    """Male's nakshatra must be >= 9 nakshatras from female's (counted f→m)."""
    count = ((m_nak_idx - f_nak_idx) % 27) + 1
    return "good" if count >= 9 else "bad"


# 11. Vedha Kuta — obstruction pairs
VEDHA_PAIRS = [
    (0, 17),   # Ashwini - Jyeshtha
    (1, 16),   # Bharani - Anuradha
    (2, 15),   # Krittika - Vishakha
    (3, 14),   # Rohini - Swati
    (5, 21),   # Ardra - Shravana
    (6, 20),   # Punarvasu - Uttara Ashadha
    (7, 19),   # Pushya - Purva Ashadha
    (8, 18),   # Ashlesha - Mula
    (9, 26),   # Magha - Revati
    (10, 25),  # Purva Phalguni - Uttara Bhadrapada
    (11, 24),  # Uttara Phalguni - Purva Bhadrapada
    (12, 23),  # Hasta - Shatabhisha
    (4, 22),   # Mrigashira - Dhanishta
]

def calc_vedha(m_nak_idx, f_nak_idx):
    """Check if male and female nakshatras form a hostile Vedha pair."""
    for a, b in VEDHA_PAIRS:
        if (m_nak_idx == a and f_nak_idx == b) or (m_nak_idx == b and f_nak_idx == a):
            return "bad"
    return "good"


# 12. Kuja Dosha (Manglik) — Mars affliction analysis
_DOSHA_HOUSES = {2, 4, 7, 8, 12}
_HIGH_SEVERITY_HOUSES = {7, 8}

_MARS_EXCEPTIONS = {
    2: {"Gemini", "Virgo"},
    12: {"Taurus", "Libra"},
    4: {"Aries", "Scorpio"},
    7: {"Capricorn", "Cancer"},
    8: {"Sagittarius", "Pisces"},
}
_MARS_EXEMPT_SIGNS = {"Aquarius", "Leo"}


def _planet_dignity_level(planet_name, sign):
    """Return dignity level for Kuja Dosha scoring."""
    if planet_name in EXALTATION and EXALTATION[planet_name][0] == sign:
        return "exalted"
    if planet_name in OWN_SIGNS and sign in OWN_SIGNS[planet_name]:
        return "own"
    lord = SIGN_LORDS.get(sign)
    if lord and planet_name in NATURAL_FRIENDS.get(lord, []):
        return "friendly"
    if lord and planet_name in NATURAL_ENEMIES.get(lord, []):
        return "enemy"
    if planet_name in DEBILITATION and DEBILITATION[planet_name][0] == sign:
        return "debilitated"
    return "neutral"


_DOSHA_SCORES_HIGH = {
    "Mars": {"debilitated": 100, "enemy": 90, "neutral": 80, "friendly": 70, "own": 60, "exalted": 50},
    "Saturn": {"debilitated": 75, "enemy": 67.5, "neutral": 60, "friendly": 52.5, "own": 45, "exalted": 37.5},
    "Sun": {"debilitated": 50, "enemy": 45, "neutral": 40, "friendly": 35, "own": 30, "exalted": 25},
}
_DOSHA_SCORES_LOW = {
    "Mars": {"debilitated": 50, "enemy": 45, "neutral": 40, "friendly": 35, "own": 30, "exalted": 25},
    "Saturn": {"debilitated": 37.5, "enemy": 33.75, "neutral": 30, "friendly": 26.25, "own": 22.5, "exalted": 18.75},
    "Sun": {"debilitated": 25, "enemy": 22.5, "neutral": 20, "friendly": 17.5, "own": 15, "exalted": 12.5},
}


def _calc_dosha_score(planet_name, house, sign):
    """Calculate Kuja Dosha score for a single planet placement."""
    if house not in _DOSHA_HOUSES:
        return 0.0
    # Mars-specific exceptions
    if planet_name == "Mars":
        if sign in _MARS_EXEMPT_SIGNS:
            return 0.0
        if house in _MARS_EXCEPTIONS and sign in _MARS_EXCEPTIONS[house]:
            return 0.0

    dig = _planet_dignity_level(planet_name, sign)
    score_planet = planet_name if planet_name in _DOSHA_SCORES_HIGH else "Saturn"  # Rahu/Ketu use Saturn table

    if house in _HIGH_SEVERITY_HOUSES:
        return _DOSHA_SCORES_HIGH.get(score_planet, _DOSHA_SCORES_HIGH["Saturn"]).get(dig, 60)
    else:
        return _DOSHA_SCORES_LOW.get(score_planet, _DOSHA_SCORES_LOW["Saturn"]).get(dig, 30)


def calc_kuja_dosha(chart):
    """
    Calculate total Kuja Dosha score for a chart.
    Checks Mars, Saturn, Rahu, Ketu, Sun in houses 2,4,7,8,12.
    chart: output from calculate_vedic_chart (needs planets with house and sign).
    Returns dict with total score and per-planet breakdown.
    """
    planets = chart.get("planets", {})
    total = 0.0
    breakdown = {}
    for p_name in ("Mars", "Saturn", "Rahu", "Ketu", "Sun"):
        pd = planets.get(p_name)
        if not pd:
            continue
        score = _calc_dosha_score(p_name, pd["house"], pd["sign"])
        if score > 0:
            breakdown[p_name] = {"house": pd["house"], "sign": pd["sign"], "score": score}
        total += score
    return {"total_score": round(total, 2), "breakdown": breakdown, "is_manglik": total > 0}


def match_kuja_dosha(male_score, female_score):
    """
    Compare Kuja Dosha between male and female.
    |diff| <= 5: good. Female > male by > 5: bad. Male > female by > 5: check 25% threshold.
    """
    diff = male_score - female_score
    if abs(diff) <= 5:
        return {"result": "good", "description": "Kuja Dosha balanced between partners."}
    if diff < -5:
        return {"result": "bad", "description": "Female has significantly more Kuja Dosha."}
    # male > female by > 5
    if female_score > 0 and diff < female_score * 0.25:
        return {"result": "acceptable", "description": "Male has more Kuja Dosha but within tolerance."}
    return {"result": "bad", "description": "Male has significantly more Kuja Dosha."}


# 13. Rajju Kuta — marital longevity based on nakshatra body-part group
RAJJU_GROUPS = {
    "Pada":  {0, 8, 9, 17, 18, 26},   # Ashwini, Ashlesha, Magha, Jyeshtha, Mula, Revati
    "Kati":  {1, 7, 10, 16, 25, 19},   # Bharani, Pushya, P.Phalguni, Anuradha, U.Bhadra, P.Ashadha
    "Udara": {2, 6, 11, 15, 20, 24},   # Krittika, Punarvasu, U.Phalguni, Vishakha, U.Ashadha, P.Bhadra
    "Kanta": {3, 5, 12, 14, 21, 23},   # Rohini, Ardra, Hasta, Swati, Shravana, Shatabhisha
    "Sira":  {4, 13, 22},              # Mrigashira, Chitra, Dhanishta
}

RAJJU_EFFECTS = {
    "Sira": "head — risk to husband's longevity",
    "Kanta": "neck — risk to wife's longevity",
    "Udara": "stomach — risk to children",
    "Kati": "waist — poverty may ensue",
    "Pada": "foot — couple may be always wandering",
}

def _get_rajju_group(nak_idx):
    for group, indices in RAJJU_GROUPS.items():
        if nak_idx in indices:
            return group
    return None

def calc_rajju(m_nak_idx, f_nak_idx):
    """Same Rajju group = bad; different = good."""
    m_group = _get_rajju_group(m_nak_idx)
    f_group = _get_rajju_group(f_nak_idx)
    if m_group and f_group and m_group == f_group:
        return {"result": "bad", "group": m_group, "effect": RAJJU_EFFECTS.get(m_group, "")}
    return {"result": "good", "group": None, "effect": ""}


# 14. Bad Constellations — specific nakshatra quarters considered destructive
def calc_bad_constellations(m_nak_idx, m_pada, f_nak_idx, f_pada):
    """
    Only first pada of Moola/Ashlesha/Jyeshtha and 4th pada of Vishakha are bad.
    Ashlesha/Jyeshtha/Vishakha destructive only for females.
    """
    issues = []
    if m_nak_idx == 18 and m_pada == 1:
        issues.append("Male born in Moola 1st pada — risk to father-in-law.")
    if f_nak_idx == 18 and f_pada == 1:
        issues.append("Female born in Moola 1st pada — risk to father-in-law.")
    if f_nak_idx == 8 and f_pada == 1:
        issues.append("Female born in Ashlesha 1st pada — risk to husband's mother.")
    if f_nak_idx == 17 and f_pada == 1:
        issues.append("Female born in Jyeshtha 1st pada — risk to husband's elder brother.")
    if f_nak_idx == 15 and f_pada == 4:
        issues.append("Female born in Vishakha 4th pada — risk to husband's younger brother.")
    return {"result": "bad" if issues else "good", "issues": issues}


# 15. Lagna and House 7 — cross-Lagna compatibility
def calc_lagna_house7(chart1, chart2):
    """
    Good if female's Moon sign = male's Lagna OR male's Moon sign = female's Lagna,
    OR if 7th house lords are exchanged.
    """
    m_lagna = chart1.get("lagna", {}).get("sign")
    f_lagna = chart2.get("lagna", {}).get("sign")
    m_moon = chart1.get("planets", {}).get("Moon", {}).get("sign")
    f_moon = chart2.get("planets", {}).get("Moon", {}).get("sign")

    if (f_moon and m_lagna and f_moon == m_lagna) or (m_moon and f_lagna and m_moon == f_lagna):
        return {"result": "good", "description": "Moon-Lagna cross match — mutual understanding and affection."}

    m_lagna_idx = ZODIAC_SIGNS.index(m_lagna) if m_lagna else None
    f_lagna_idx = ZODIAC_SIGNS.index(f_lagna) if f_lagna else None
    if m_lagna_idx is not None and f_lagna_idx is not None:
        m_7th_sign = ZODIAC_SIGNS[(m_lagna_idx + 6) % 12]
        f_7th_sign = ZODIAC_SIGNS[(f_lagna_idx + 6) % 12]
        m_7th_lord = SIGN_LORDS[m_7th_sign]
        f_7th_lord = SIGN_LORDS[f_7th_sign]
        m_7lord_sign = chart1.get("planets", {}).get(m_7th_lord, {}).get("sign")
        f_7lord_sign = chart2.get("planets", {}).get(f_7th_lord, {}).get("sign")
        if m_7lord_sign == f_lagna or f_7lord_sign == m_lagna:
            return {"result": "good", "description": "7th house lord cross-placement — marriage stability."}

    return {"result": "neutral", "description": "No special Lagna-7th house connection found."}


# 16. Sex Energy — based on planets in 7th house
def calc_sex_energy(chart1, chart2):
    """
    Mars/Venus in 7th = strong sex drive. Mercury/Jupiter in 7th = moderate.
    Mismatch between partners = potential incompatibility.
    """
    def _classify(chart):
        planets = chart.get("planets", {})
        strong = any(planets.get(p, {}).get("house") == 7 for p in ("Mars", "Venus"))
        moderate = any(planets.get(p, {}).get("house") == 7 for p in ("Mercury", "Jupiter"))
        if strong and not moderate:
            return "strong"
        if moderate and not strong:
            return "moderate"
        if strong and moderate:
            return "mixed"
        return "unknown"

    m_type = _classify(chart1)
    f_type = _classify(chart2)
    if m_type in ("unknown", "mixed") or f_type in ("unknown", "mixed"):
        return {"result": "neutral", "male": m_type, "female": f_type,
                "description": "Insufficient data for sex energy assessment."}
    if m_type == f_type:
        return {"result": "good", "male": m_type, "female": f_type,
                "description": f"Both partners have {m_type} sex energy — compatible."}
    return {"result": "bad", "male": m_type, "female": f_type,
            "description": f"Male has {m_type} and female has {f_type} sex energy — potential mismatch."}


def calculate_ashtakoot(male_moon_lon: float, female_moon_lon: float,
                        male_chart=None, female_chart=None):
    """
    Calculates the 36-point Ashtakoot compatibility matching
    plus additional kutas (Mahendra, Stree Deergha, Vedha, Rajju, etc.).
    """
    m_nak = get_nakshatra(male_moon_lon)
    f_nak = get_nakshatra(female_moon_lon)
    m_nak_idx = m_nak["index"]
    f_nak_idx = f_nak["index"]
    
    m_sign_idx = int((male_moon_lon % 360) / 30)
    f_sign_idx = int((female_moon_lon % 360) / 30)
    m_sign = ZODIAC_SIGNS[m_sign_idx]
    f_sign = ZODIAC_SIGNS[f_sign_idx]

    scores = {
        "Varna": calc_varna(m_sign, f_sign),
        "Vashya": calc_vashya(m_sign, f_sign),
        "Tara": calc_tara(m_nak_idx, f_nak_idx),
        "Yoni": calc_yoni(m_nak_idx, f_nak_idx),
        "GrahaMaitri": calc_graha_maitri(m_sign, f_sign),
        "Gana": calc_gana(m_nak_idx, f_nak_idx),
        "Bhakoot": calc_bhakoot(m_sign, f_sign),
        "Nadi": calc_nadi(m_nak_idx, f_nak_idx),
    }
    
    total_score = sum(scores.values())

    # Additional kutas
    rajju_result = calc_rajju(m_nak_idx, f_nak_idx)
    additional_kutas = {
        "Mahendra": calc_mahendra(m_nak_idx, f_nak_idx),
        "StreeDeergha": calc_stree_deergha(m_nak_idx, f_nak_idx),
        "Vedha": calc_vedha(m_nak_idx, f_nak_idx),
        "Rajju": rajju_result,
        "BadConstellations": calc_bad_constellations(
            m_nak_idx, m_nak.get("pada", 0), f_nak_idx, f_nak.get("pada", 0)),
    }

    # Chart-dependent kutas (need full chart data)
    if male_chart and female_chart:
        additional_kutas["LagnaHouse7"] = calc_lagna_house7(male_chart, female_chart)
        additional_kutas["SexEnergy"] = calc_sex_energy(male_chart, female_chart)

    # Exception logic (per VedAstro/BPHS):
    exceptions = []

    # 1. Bad Nadi neutralized if Bhakoot + Rajju both good
    if scores["Nadi"] == 0:
        if scores["Bhakoot"] > 0 and rajju_result["result"] == "good":
            exceptions.append("Nadi Dosha mitigated by good Bhakoot and Rajju.")

    # 2. Bad Rajju neutralized if GrahaMaitri + Bhakoot + Tara + Mahendra all good
    if rajju_result["result"] == "bad":
        if (scores["GrahaMaitri"] >= 4.0 and scores["Bhakoot"] > 0 and
                scores["Tara"] >= 1.5 and additional_kutas["Mahendra"] == "good"):
            exceptions.append("Rajju Dosha mitigated by good Graha Maitri, Bhakoot, Tara, and Mahendra.")

    # 3. Bad Stree Deergha neutralized if Bhakoot + GrahaMaitri both good
    if additional_kutas["StreeDeergha"] == "bad":
        if scores["Bhakoot"] > 0 and scores["GrahaMaitri"] >= 4.0:
            exceptions.append("Stree Deergha Dosha mitigated by good Bhakoot and Graha Maitri.")

    return {
        "male_details": {
            "moon_sign": m_sign,
            "nakshatra": m_nak["name"],
            "gana": GANA[m_nak_idx],
            "nadi": NADI[m_nak_idx],
            "yoni": YONI_ANIMALS[m_nak_idx]
        },
        "female_details": {
            "moon_sign": f_sign,
            "nakshatra": f_nak["name"],
            "gana": GANA[f_nak_idx],
            "nadi": NADI[f_nak_idx],
            "yoni": YONI_ANIMALS[f_nak_idx]
        },
        "scores": scores,
        "total_score": total_score,
        "max_score": 36.0,
        "additional_kutas": additional_kutas,
        "exceptions": exceptions,
        "is_match_approved": total_score >= 18.0 and (scores["Nadi"] > 0 or len(exceptions) > 0)
    }
