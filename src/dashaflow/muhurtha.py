"""
Muhurtha — Electional Astrology (BPHS)
Evaluates auspiciousness of a given date/time for specific activities.
Uses Panchang elements, planetary positions, and classical rules.
"""

from .constants import ZODIAC_SIGNS, SIGN_LORDS

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


def _check_panchanga_suddhi(panchang):
    """Check universal Panchang purity (5-fold). Returns list of issues."""
    issues = []

    tithi_num = panchang.get("tithi", {}).get("number", 0)
    if tithi_num in BAD_TITHIS:
        issues.append(f"Inauspicious tithi: {panchang['tithi'].get('name', tithi_num)}")

    nak_name = panchang.get("nakshatra", {}).get("name", "")
    if nak_name in BAD_NAKSHATRAS:
        issues.append(f"Inauspicious nakshatra: {nak_name}")

    yoga_idx = panchang.get("yoga", {}).get("index", -1)
    if yoga_idx in BAD_YOGAS:
        issues.append(f"Inauspicious yoga: {panchang['yoga'].get('name', yoga_idx)}")

    return issues


def _check_marriage_doshas(planets):
    """Check marriage-specific rejection doshas (per BPHS)."""
    doshas = []

    # Sagraha Dosha: Moon conjunct any planet
    moon = planets.get("Moon", {})
    moon_sign = moon.get("sign", "")
    for p_name, pd in planets.items():
        if p_name != "Moon" and pd.get("sign") == moon_sign:
            doshas.append(f"Sagraha Dosha: Moon conjunct {p_name} in {moon_sign}")
            break

    # Moon in 6th, 8th, or 12th
    moon_house = moon.get("house", 0)
    if moon_house in (6, 8, 12):
        doshas.append(f"Shashtashta Dosha: Moon in house {moon_house}")

    # Venus in 6th
    venus = planets.get("Venus", {})
    if venus.get("house") == 6:
        doshas.append("Bhrigupta Shatka: Venus in 6th house")

    # Mars in 8th
    mars = planets.get("Mars", {})
    if mars.get("house") == 8:
        doshas.append("Kujaasthama: Mars in 8th house")

    return doshas


def evaluate_muhurtha(activity, panchang, planets=None, lagna_sign=None):
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
    nak_name = panchang.get("nakshatra", {}).get("name", "")
    good_naks = rules.get("good_nakshatras", set())
    if nak_name in good_naks:
        positive.append(f"Auspicious nakshatra for {activity}: {nak_name}")
    elif nak_name and nak_name not in BAD_NAKSHATRAS:
        negative.append(f"Nakshatra {nak_name} is not ideal for {activity}")

    # 3. Activity-specific tithi
    tithi_num = panchang.get("tithi", {}).get("number", 0)
    good_tithis = rules.get("good_tithis", set())
    if tithi_num in good_tithis:
        positive.append(f"Auspicious tithi: {panchang['tithi'].get('name', tithi_num)}")

    # 4. Weekday check
    good_weekdays = rules.get("good_weekdays")
    if good_weekdays:
        vara = panchang.get("vara", {}).get("name", "")
        if vara in good_weekdays:
            positive.append(f"Auspicious weekday: {vara}")
        else:
            negative.append(f"Weekday {vara} is not ideal for {activity}")

    # 5. Lagna check
    good_lagnas = rules.get("good_lagnas")
    if good_lagnas and lagna_sign:
        if lagna_sign in good_lagnas:
            positive.append(f"Auspicious Lagna: {lagna_sign}")
        else:
            negative.append(f"Lagna {lagna_sign} is not ideal for {activity}")

    # 6. Moon sign check (for business)
    moon_signs = rules.get("moon_signs")
    if moon_signs and planets:
        moon_sign = planets.get("Moon", {}).get("sign", "")
        if moon_sign in moon_signs:
            positive.append(f"Moon in auspicious sign for {activity}: {moon_sign}")
        else:
            negative.append(f"Moon in {moon_sign} is not ideal for {activity}")

    # 7. Marriage-specific dosha checks
    if activity == "marriage" and planets:
        doshas = _check_marriage_doshas(planets)
        for d in doshas:
            negative.append(f"DOSHA: {d}")

    # 8th house check (should be empty for marriage, medical, house_entry)
    if activity in ("marriage", "medical", "house_entry") and planets:
        for p_name, pd in planets.items():
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
