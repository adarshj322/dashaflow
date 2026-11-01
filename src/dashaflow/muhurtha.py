"""
Muhurtha — Electional Astrology (BPHS)
Evaluates auspiciousness of a given date/time for specific activities.
Uses Panchang elements, planetary positions, and classical rules.
"""

from .constants import ZODIAC_SIGNS
from .errors import InvalidInputError

# ==========================================
# UNIVERSAL AVOIDANCE RULES
# ==========================================

# Inauspicious Panchang Yoga indices (0-indexed)
BAD_YOGAS = {0, 5, 8, 9, 12, 14, 16, 18, 26}

# Universally avoided lunar days (tithis)
BAD_TITHIS = {4, 6, 8, 12, 14, 30}

# Universally avoided nakshatras
BAD_NAKSHATRAS = {"Bharani", "Krittika"}


# ==========================================
# ACTIVITY-SPECIFIC RULES
# ==========================================

MARRIAGE_RULES = {
    "good_nakshatras": {"Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta",
                        "Swati", "Anuradha", "Moola", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_lagnas": {"Taurus", "Gemini", "Cancer", "Virgo", "Libra", "Sagittarius"},
}

TRAVEL_RULES = {
    "good_nakshatras": {"Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta",
                        "Anuradha", "Shravana", "Dhanishta", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_lagnas": {"Aries", "Taurus", "Cancer", "Leo", "Libra", "Sagittarius"},
}

BUSINESS_RULES = {
    "good_nakshatras": {"Ashwini", "Rohini", "Punarvasu", "Pushya", "Uttara Phalguni",
                        "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_weekdays": {"Monday", "Wednesday", "Thursday", "Friday"},
    "moon_signs": {"Taurus", "Cancer", "Virgo", "Libra", "Sagittarius", "Pisces"},
}

EDUCATION_RULES = {
    "good_nakshatras": {"Ashwini", "Punarvasu", "Pushya", "Hasta", "Chitra",
                        "Swati", "Shravana", "Dhanishta", "Shatabhisha", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_lagnas": {"Gemini", "Virgo", "Sagittarius", "Pisces"},
}

HOUSE_ENTRY_RULES = {
    "good_nakshatras": {"Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada",
                        "Shravana", "Dhanishta", "Revati", "Ashwini", "Mrigashira"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_weekdays": {"Monday", "Wednesday", "Thursday", "Friday"},
}

MEDICAL_RULES = {
    "good_nakshatras": {"Ashwini", "Rohini", "Mrigashira", "Pushya", "Hasta",
                        "Chitra", "Swati", "Anuradha", "Shravana", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_weekdays": {"Saturday", "Monday"},
}

ACTIVITY_RULES = {
    "marriage": MARRIAGE_RULES,
    "travel": TRAVEL_RULES,
    "business": BUSINESS_RULES,
    "education": EDUCATION_RULES,
    "house_entry": HOUSE_ENTRY_RULES,
    "medical": MEDICAL_RULES,
}


def _section(panchang, key):
    """Nested panchang section as a dict; mistyped values become {} (ignored)."""
    section = panchang.get(key, {})
    return section if isinstance(section, dict) else {}


def _contains(container, value):
    """Set membership that tolerates unhashable/mistyped values (→ False)."""
    try:
        return value in container
    except TypeError:
        return False


def _check_panchanga_suddhi(panchang):
    """Check universal Panchang purity (5-fold). Returns list of issues."""
    issues = []

    tithi = _section(panchang, "tithi")
    tithi_num = tithi.get("number", 0)
    if _contains(BAD_TITHIS, tithi_num):
        issues.append(f"Inauspicious tithi: {tithi.get('name', tithi_num)}")

    nak_name = _section(panchang, "nakshatra").get("name", "")
    if _contains(BAD_NAKSHATRAS, nak_name):
        issues.append(f"Inauspicious nakshatra: {nak_name}")

    yoga = _section(panchang, "yoga")
    yoga_idx = yoga.get("index", -1)
    if _contains(BAD_YOGAS, yoga_idx):
        issues.append(f"Inauspicious yoga: {yoga.get('name', yoga_idx)}")

    return issues


def _planet_entry(planets, name):
    """Planet entry as a dict; mistyped values become {} (ignored)."""
    entry = planets.get(name, {})
    return entry if isinstance(entry, dict) else {}


def _check_marriage_doshas(planets):
    """Check marriage-specific rejection doshas (per BPHS)."""
    doshas = []

    # Sagraha Dosha: Moon conjunct any planet (needs a Moon position;
    # otherwise an empty sign could false-match another empty sign).
    moon = _planet_entry(planets, "Moon")
    moon_sign = moon.get("sign", "")
    if moon_sign:
        for p_name, pd in planets.items():
            if not isinstance(pd, dict):
                continue
            if p_name != "Moon" and pd.get("sign") == moon_sign:
                doshas.append(f"Sagraha Dosha: Moon conjunct {p_name} in {moon_sign}")
                break

    # Moon in 6th, 8th, or 12th
    moon_house = moon.get("house", 0)
    if moon_house in (6, 8, 12):
        doshas.append(f"Shashtashta Dosha: Moon in house {moon_house}")

    # Venus in 6th
    venus = _planet_entry(planets, "Venus")
    if venus.get("house") == 6:
        doshas.append("Bhrigupta Shatka: Venus in 6th house")

    # Mars in 8th
    mars = _planet_entry(planets, "Mars")
    if mars.get("house") == 8:
        doshas.append("Kujaasthama: Mars in 8th house")

    return doshas


def evaluate_muhurtha(activity: str, panchang: dict, planets=None, lagna_sign=None) -> dict:
    """
    Evaluate auspiciousness of a moment for a given activity.

    Parameters
    ----------
    activity : str
        One of: 'marriage', 'travel', 'business', 'education', 'house_entry', 'medical'
    panchang : dict
        Panchang data from calculate_panchang()
    planets : dict, optional
        Planet positions (for marriage dosha checks)
    lagna_sign : str, optional
        Rising sign at the moment

    Returns
    -------
    dict with verdict, reasons, and score
    """
    if not isinstance(activity, str):
        return {"verdict": "error", "reason": f"Unknown activity: {activity!r} (must be a string)",
                "supported_activities": list(ACTIVITY_RULES.keys())}
    if not isinstance(panchang, dict):
        raise InvalidInputError("Invalid panchang: must be a panchang dict.")
    if planets is not None and not isinstance(planets, dict):
        raise InvalidInputError("Invalid planets: must be a planets dict or None.")
    if lagna_sign is not None:
        if lagna_sign not in ZODIAC_SIGNS:
            raise InvalidInputError(f"Invalid lagna_sign: {lagna_sign!r} (must be a zodiac sign or None).")
    rules = ACTIVITY_RULES.get(activity)
    if not rules:
        return {"verdict": "error", "reason": f"Unknown activity: {activity}",
                "supported_activities": list(ACTIVITY_RULES.keys())}

    positive = []
    negative = []

    # 1. Universal Panchanga Suddhi
    panchang_issues = _check_panchanga_suddhi(panchang)
    negative.extend(panchang_issues)

    # 2. Activity-specific nakshatra
    nak_name = _section(panchang, "nakshatra").get("name", "")
    good_naks = rules.get("good_nakshatras", set())
    if _contains(good_naks, nak_name):
        positive.append(f"Auspicious nakshatra for {activity}: {nak_name}")
    elif nak_name and not _contains(BAD_NAKSHATRAS, nak_name):
        negative.append(f"Nakshatra {nak_name} is not ideal for {activity}")

    # 3. Activity-specific tithi
    tithi = _section(panchang, "tithi")
    tithi_num = tithi.get("number", 0)
    good_tithis = rules.get("good_tithis", set())
    if _contains(good_tithis, tithi_num):
        positive.append(f"Auspicious tithi: {tithi.get('name', tithi_num)}")

    # 4. Weekday check
    good_weekdays = rules.get("good_weekdays")
    if good_weekdays:
        vara = _section(panchang, "vara").get("name", "")
        if _contains(good_weekdays, vara):
            positive.append(f"Auspicious weekday: {vara}")
        elif vara:
            # Missing vara carries no signal (like missing lagna/nakshatra).
            negative.append(f"Weekday {vara} is not ideal for {activity}")

    # 5. Lagna check
    good_lagnas = rules.get("good_lagnas")
    if good_lagnas and lagna_sign:
        if _contains(good_lagnas, lagna_sign):
            positive.append(f"Auspicious Lagna: {lagna_sign}")
        else:
            negative.append(f"Lagna {lagna_sign} is not ideal for {activity}")

    # 6. Moon sign check (for business)
    moon_signs = rules.get("moon_signs")
    if moon_signs and planets:
        moon_sign = _planet_entry(planets, "Moon").get("sign", "")
        if _contains(moon_signs, moon_sign):
            positive.append(f"Moon in auspicious sign for {activity}: {moon_sign}")
        elif moon_sign:
            negative.append(f"Moon in {moon_sign} is not ideal for {activity}")

    # 7. Marriage-specific dosha checks
    if activity == "marriage" and planets:
        doshas = _check_marriage_doshas(planets)
        for d in doshas:
            negative.append(f"DOSHA: {d}")

    # 8th house check (should be empty for marriage, medical, house_entry)
    if activity in ("marriage", "medical", "house_entry") and planets:
        for p_name, pd in planets.items():
            if not isinstance(pd, dict):
                continue
            if p_name not in ("Rahu", "Ketu") and pd.get("house") == 8:
                negative.append(f"Planet in 8th house: {p_name}")
                break

    # Scoring
    score = len(positive) * 10 - len(negative) * 15
    has_hard_reject = any("DOSHA:" in n for n in negative)

    if has_hard_reject:
        verdict = "inauspicious"
    elif len(negative) == 0 and len(positive) >= 2:
        verdict = "auspicious"
    elif len(positive) > len(negative):
        verdict = "mixed_favorable"
    elif len(negative) > len(positive):
        verdict = "inauspicious"
    else:
        verdict = "mixed"

    return {
        "activity": activity,
        "verdict": verdict,
        "score": max(0, score),
        "positive_factors": positive,
        "negative_factors": negative,
        "total_positive": len(positive),
        "total_negative": len(negative),
    }
