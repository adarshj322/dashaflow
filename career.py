"""
Career Analysis Framework — D10 Dashamsha interpretation
Uses D10 chart, 10th house analysis, and planetary significations.
"""

from constants import ZODIAC_SIGNS, SIGN_LORDS, EXALTATION, OWN_SIGNS

# Planet -> career significations (Jyotish standard)
CAREER_SIGNIFICATIONS = {
    "Sun": ["government", "politics", "administration", "medicine", "leadership", "authority"],
    "Moon": ["nursing", "hospitality", "public_relations", "agriculture", "shipping", "dairy"],
    "Mars": ["military", "engineering", "surgery", "sports", "police", "real_estate", "fire_services"],
    "Mercury": ["writing", "accounting", "commerce", "communication", "IT", "teaching", "astrology"],
    "Jupiter": ["law", "education", "finance", "banking", "religion", "philosophy", "consulting"],
    "Venus": ["arts", "entertainment", "fashion", "luxury_goods", "hotel", "cosmetics", "music"],
    "Saturn": ["mining", "agriculture", "labor", "construction", "oil", "manufacturing", "judiciary"],
    "Rahu": ["technology", "foreign_trade", "aviation", "research", "pharmaceuticals", "diplomacy"],
    "Ketu": ["spirituality", "occult", "research", "computing", "alternative_medicine", "languages"],
}

# Sign -> professional domains
SIGN_CAREERS = {
    "Aries": ["military", "sports", "engineering", "entrepreneurship"],
    "Taurus": ["banking", "agriculture", "luxury_goods", "arts", "food_industry"],
    "Gemini": ["communication", "writing", "media", "IT", "trading"],
    "Cancer": ["nursing", "hospitality", "real_estate", "food_industry"],
    "Leo": ["government", "entertainment", "leadership", "politics"],
    "Virgo": ["healthcare", "accounting", "analysis", "service", "editing"],
    "Libra": ["law", "diplomacy", "arts", "fashion", "counseling"],
    "Scorpio": ["research", "surgery", "occult", "insurance", "investigation"],
    "Sagittarius": ["education", "law", "religion", "publishing", "travel"],
    "Capricorn": ["administration", "mining", "construction", "management"],
    "Aquarius": ["technology", "social_work", "aviation", "research", "NGO"],
    "Pisces": ["spirituality", "arts", "healthcare", "shipping", "charity"],
}

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}


def _is_strong(planet_name, sign):
    """Check if planet is exalted or in own sign."""
    if planet_name in EXALTATION and EXALTATION[planet_name][0] == sign:
        return True
    if planet_name in OWN_SIGNS and sign in OWN_SIGNS[planet_name]:
        return True
    return False


def analyze_career(planets, lagna_sign):
    """
    Comprehensive career analysis using 10th house, D10, and planetary influences.

    Parameters
    ----------
    planets : dict — Planet data from calculate_vedic_chart (needs house, sign, d10_sign, dignity)
    lagna_sign : str — Ascendant sign

    Returns
    -------
    dict with career indicators, D10 analysis, and recommendations
    """
    lagna_idx = ZODIAC_SIGNS.index(lagna_sign)
    tenth_sign = ZODIAC_SIGNS[(lagna_idx + 9) % 12]
    tenth_lord = SIGN_LORDS[tenth_sign]

    # D10 analysis
    d10_indicators = {}
    for p_name, pd in planets.items():
        d10_sign = pd.get("d10_sign")
        if d10_sign:
            d10_lord = SIGN_LORDS.get(d10_sign)
            d10_indicators[p_name] = {
                "d10_sign": d10_sign,
                "d10_lord": d10_lord,
                "d10_strong": _is_strong(p_name, d10_sign),
            }

    # Planets in 10th house
    tenth_house_planets = []
    for p_name, pd in planets.items():
        if pd.get("house") == 10:
            tenth_house_planets.append(p_name)

    # 10th lord analysis
    tenth_lord_data = planets.get(tenth_lord, {})
    tenth_lord_house = tenth_lord_data.get("house")
    tenth_lord_sign = tenth_lord_data.get("sign", "")
    tenth_lord_d10 = tenth_lord_data.get("d10_sign", "")
    tenth_lord_dignity = tenth_lord_data.get("dignity", "neutral")

    # Career themes from 10th house planets
    career_themes = set()
    primary_planets = []

    # From 10th house occupants
    for p_name in tenth_house_planets:
        for theme in CAREER_SIGNIFICATIONS.get(p_name, []):
            career_themes.add(theme)
        primary_planets.append(p_name)

    # From 10th lord's significations
    for theme in CAREER_SIGNIFICATIONS.get(tenth_lord, []):
        career_themes.add(theme)
    if tenth_lord not in primary_planets:
        primary_planets.append(tenth_lord)

    # From 10th sign's domains
    for theme in SIGN_CAREERS.get(tenth_sign, []):
        career_themes.add(theme)

    # From D10 10th lord placement
    if tenth_lord in d10_indicators:
        d10_info = d10_indicators[tenth_lord]
        for theme in SIGN_CAREERS.get(d10_info["d10_sign"], []):
            career_themes.add(theme)

    # Strength assessment
    strength_factors = []
    if tenth_lord_dignity in ("exalted", "own_sign", "mooltrikona"):
        strength_factors.append(f"10th lord {tenth_lord} in {tenth_lord_dignity} — strong career foundation")
    if tenth_lord_house in KENDRA_HOUSES:
        strength_factors.append(f"10th lord {tenth_lord} in kendra (house {tenth_lord_house}) — career prominence")
    if tenth_lord_house in TRIKONA_HOUSES:
        strength_factors.append(f"10th lord {tenth_lord} in trikona (house {tenth_lord_house}) — fortune in career")
    if tenth_lord_house in DUSTHANA_HOUSES:
        strength_factors.append(f"10th lord {tenth_lord} in dusthana (house {tenth_lord_house}) — career challenges")

    for p_name in tenth_house_planets:
        pd = planets.get(p_name, {})
        if pd.get("dignity") in ("exalted", "own_sign"):
            strength_factors.append(f"{p_name} strong in 10th house — powerful career planet")
        if pd.get("is_retrograde"):
            strength_factors.append(f"{p_name} retrograde in 10th — unconventional career path")

    # D10 strength check
    d10_strong_planets = [p for p, info in d10_indicators.items() if info.get("d10_strong")]
    if d10_strong_planets:
        strength_factors.append(f"Strong in D10: {', '.join(d10_strong_planets)} — career success in their domains")

    # 6th lord analysis (competition/service)
    sixth_sign = ZODIAC_SIGNS[(lagna_idx + 5) % 12]
    sixth_lord = SIGN_LORDS[sixth_sign]
    sixth_lord_data = planets.get(sixth_lord, {})
    if sixth_lord_data.get("house") == 10:
        strength_factors.append(f"6th lord {sixth_lord} in 10th — career in service, healthcare, or competition")

    # 7th lord analysis (business/partnerships)
    seventh_sign = ZODIAC_SIGNS[(lagna_idx + 6) % 12]
    seventh_lord = SIGN_LORDS[seventh_sign]
    seventh_lord_data = planets.get(seventh_lord, {})
    if seventh_lord_data.get("house") == 10 or tenth_lord_house == 7:
        strength_factors.append("10th-7th lord connection — career through partnerships or business")

    return {
        "tenth_house": {
            "sign": tenth_sign,
            "lord": tenth_lord,
            "lord_house": tenth_lord_house,
            "lord_sign": tenth_lord_sign,
            "lord_d10": tenth_lord_d10,
            "lord_dignity": tenth_lord_dignity,
            "occupants": tenth_house_planets,
        },
        "d10_indicators": d10_indicators,
        "career_themes": sorted(career_themes),
        "primary_planets": primary_planets,
        "strength_factors": strength_factors,
        "d10_strong_planets": d10_strong_planets,
    }
