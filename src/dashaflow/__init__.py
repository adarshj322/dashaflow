"""
DashaFlow — Vedic Astrology Calculation Engine
===============================================

Swiss Ephemeris with Sidereal Lahiri ayanamsha.
Rooted in Brihat Parashara Hora Shastra (BPHS) and B.V. Raman's Hindu Predictive Astrology.

Quick start::

    import dashaflow

    chart = dashaflow.cast_chart("1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")
    print(chart["lagna"]["sign"])       # e.g. "Leo"
    print(chart["planets"]["Moon"])      # full Moon data
    print(chart["yogas"])               # detected yogas
"""

from ._version import __version__
from ._validation import validate_birth_input
from .vedic_calculator import calculate_vedic_chart, calculate_transit
from .matchmaking import calculate_ashtakoot, calc_kuja_dosha, match_kuja_dosha
from .muhurtha import evaluate_muhurtha, ACTIVITY_RULES
from .career import analyze_career as _analyze_career_internal
from .constants import ZODIAC_SIGNS

__all__ = [
    "__version__",
    "cast_chart",
    "cast_transit",
    "calculate_compatibility",
    "check_muhurtha",
    "analyze_career",
]


def cast_chart(
    dob: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
    query_date: str = None,
    ephe_path: str = '',
) -> dict:
    """
    Cast a complete Vedic natal chart (Sidereal Lahiri ayanamsha).

    Returns a dict with: metadata, panchang, lagna, planets (with dignity,
    combustion, aspects, 14 varga signs), dashas (5 levels), yogas (24 types),
    ashtakavarga, jaimini_karakas, shadbala, bhava_chalit, avasthas,
    kaal_sarpa, graha_yuddha, gandanta, arudha_padas, upapada, karakamsha.

    Parameters
    ----------
    dob : str
        Date of birth as "YYYY-MM-DD"
    time : str
        Time of birth as "HH:MM" (24-hour)
    lat : float
        Birth latitude (-90 to 90)
    lon : float
        Birth longitude (-180 to 180)
    timezone : str
        IANA timezone (e.g. "Asia/Kolkata")
    query_date : str, optional
        Date for Dasha lookup as "YYYY-MM-DD". Defaults to today.
    ephe_path : str, optional
        Path to Swiss Ephemeris data files. Defaults to '' (bundled).

    Returns
    -------
    dict
        Complete chart data.

    Raises
    ------
    ValueError
        If any input parameter is invalid.
    """
    validate_birth_input(dob, time, lat, lon, timezone)
    return calculate_vedic_chart(
        dob_str=dob,
        time_str=time,
        lat=lat,
        lon=lon,
        timezone_str=timezone,
        query_date_str=query_date,
        ephe_path=ephe_path,
    )


def cast_transit(
    transit_date: str,
    natal_chart: dict,
    timezone: str = "Asia/Kolkata",
) -> dict:
    """
    Calculate planetary transits overlaid on a natal chart.

    Parameters
    ----------
    transit_date : str
        Date to compute transits as "YYYY-MM-DD"
    natal_chart : dict
        Full dict output from cast_chart()
    timezone : str, optional
        IANA timezone. Defaults to "Asia/Kolkata".

    Returns
    -------
    dict
        Transit planets with house positions, SAV points, Sade Sati, Rahu-Ketu axis.
    """
    return calculate_transit(
        transit_date_str=transit_date,
        natal_chart=natal_chart,
        timezone_str=timezone,
    )


def calculate_compatibility(
    dob1: str, time1: str, lat1: float, lon1: float, tz1: str,
    dob2: str, time2: str, lat2: float, lon2: float, tz2: str,
) -> dict:
    """
    Calculate 36-point Ashtakoot compatibility + Kuja Dosha.

    Person 1 = Male, Person 2 = Female (by tradition for accurate scoring).

    Parameters
    ----------
    dob1, time1, lat1, lon1, tz1 : Birth details for Person 1 (Male)
    dob2, time2, lat2, lon2, tz2 : Birth details for Person 2 (Female)

    Returns
    -------
    dict
        8 Ashtakoot kutas (36 pts), extended kutas (Mahendra, Stree Deergha,
        Vedha, Rajju, etc.), Kuja Dosha analysis with compatibility verdict.
    """
    validate_birth_input(dob1, time1, lat1, lon1, tz1)
    validate_birth_input(dob2, time2, lat2, lon2, tz2)

    chart1 = calculate_vedic_chart(dob1, time1, lat1, lon1, tz1)
    chart2 = calculate_vedic_chart(dob2, time2, lat2, lon2, tz2)

    m_moon = chart1["planets"]["Moon"]
    f_moon = chart2["planets"]["Moon"]

    m_lon = ZODIAC_SIGNS.index(m_moon["sign"]) * 30 + m_moon["degree"]
    f_lon = ZODIAC_SIGNS.index(f_moon["sign"]) * 30 + f_moon["degree"]

    score = calculate_ashtakoot(m_lon, f_lon, male_chart=chart1, female_chart=chart2)

    male_dosha = calc_kuja_dosha(chart1)
    female_dosha = calc_kuja_dosha(chart2)
    kuja_match = match_kuja_dosha(male_dosha["total_score"], female_dosha["total_score"])
    score["kuja_dosha"] = {
        "male": male_dosha,
        "female": female_dosha,
        "compatibility": kuja_match,
    }

    return score


def check_muhurtha(
    activity: str,
    date: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
) -> dict:
    """
    Check if a date/time is auspicious for a specific activity.

    Parameters
    ----------
    activity : str
        One of: 'marriage', 'travel', 'business', 'education', 'house_entry', 'medical'
    date : str
        Date as "YYYY-MM-DD"
    time : str
        Time as "HH:MM" (24-hour)
    lat : float
        Location latitude
    lon : float
        Location longitude
    timezone : str
        IANA timezone string

    Returns
    -------
    dict
        Verdict (auspicious/mixed/inauspicious), score, factors, panchang_suddhi.
    """
    validate_birth_input(date, time, lat, lon, timezone)
    if activity not in ACTIVITY_RULES:
        raise ValueError(f"Unknown activity '{activity}'. Supported: {list(ACTIVITY_RULES.keys())}")

    chart = calculate_vedic_chart(date, time, lat, lon, timezone)
    panchang = chart.get("panchang", {})
    planets = chart.get("planets", {})
    lagna_sign = chart.get("lagna", {}).get("sign")
    return evaluate_muhurtha(activity, panchang, planets, lagna_sign)


def analyze_career(
    dob: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
) -> dict:
    """
    Analyze career potential using the 10th house, D10 Dashamsha, and planetary significations.

    Parameters
    ----------
    dob : str
        Date of birth as "YYYY-MM-DD"
    time : str
        Time of birth as "HH:MM" (24-hour)
    lat : float
        Birth latitude
    lon : float
        Birth longitude
    timezone : str
        IANA timezone string

    Returns
    -------
    dict
        10th house analysis, D10 indicators, career themes, strength factors.
    """
    validate_birth_input(dob, time, lat, lon, timezone)
    chart = calculate_vedic_chart(dob, time, lat, lon, timezone)
    planets = chart.get("planets", {})
    lagna_sign = chart.get("lagna", {}).get("sign")
    return _analyze_career_internal(planets, lagna_sign)
