import sys
import os
import json
import re
import pytz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from vedic_calculator import calculate_vedic_chart, calculate_transit

mcp = FastMCP("vedic-astrology", instructions="Vedic Astrology chart calculator using Swiss Ephemeris (Sidereal Lahiri)")

_DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _validate_birth_input(dob, time, lat, lon, timezone):
    """Validate common birth chart inputs. Raises ValueError on bad data."""
    if not _DATE_RE.match(dob):
        raise ValueError(f"Invalid date format '{dob}'. Expected YYYY-MM-DD.")
    if not _TIME_RE.match(time):
        raise ValueError(f"Invalid time format '{time}'. Expected HH:MM (24h).")
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} out of range [-90, 90].")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude {lon} out of range [-180, 180].")
    if timezone not in pytz.all_timezones:
        raise ValueError(f"Unknown timezone '{timezone}'. Use IANA format (e.g. 'Asia/Kolkata').")


@mcp.tool()
def cast_vedic_chart(
    dob: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
    query_date: str = "",
) -> str:
    """
    Calculate a complete Vedic birth chart (Sidereal Lahiri ayanamsha).

    Returns planetary positions with sign, house, nakshatra, pada, dignity,
    combustion, retrograde status, Navamsha (D9), Dashamsha (D10), aspects,
    Vimshottari Dasha periods, detected yogas, and Panchang elements.

    Parameters:
        dob: Date of birth as "YYYY-MM-DD" (e.g. "1990-04-15")
        time: Time of birth as "HH:MM" in 24-hour format (e.g. "14:30")
        lat: Birth latitude as decimal degrees (e.g. 28.6139 for New Delhi)
        lon: Birth longitude as decimal degrees (e.g. 77.2090 for New Delhi)
        timezone: IANA timezone string (e.g. "Asia/Kolkata", "America/New_York")
        query_date: Optional date for Dasha lookup as "YYYY-MM-DD". Defaults to today.
    """
    try:
        _validate_birth_input(dob, time, lat, lon, timezone)
        if query_date and not _DATE_RE.match(query_date):
            raise ValueError(f"Invalid query_date format '{query_date}'. Expected YYYY-MM-DD.")
        result = calculate_vedic_chart(
            dob_str=dob,
            time_str=time,
            lat=lat,
            lon=lon,
            timezone_str=timezone,
            query_date_str=query_date if query_date else None,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def cast_transit_chart(
    transit_date: str,
    natal_chart_json: str,
    timezone: str = "Asia/Kolkata",
) -> str:
    """
    Calculate planetary transits for a given date overlaid on a natal chart.

    Returns each transit planet's current sign, nakshatra, house from natal Lagna,
    house from natal Moon, Sade Sati status, and Rahu-Ketu transit axis.

    IMPORTANT: You must call cast_vedic_chart first and pass its FULL JSON output
    as the natal_chart_json parameter.

    Parameters:
        transit_date: The date to compute transits for as "YYYY-MM-DD" (e.g. "2026-02-28")
        natal_chart_json: The FULL JSON string output from a previous cast_vedic_chart call
        timezone: IANA timezone string (defaults to "Asia/Kolkata")
    """
    try:
        if not _DATE_RE.match(transit_date):
            raise ValueError(f"Invalid transit_date format '{transit_date}'. Expected YYYY-MM-DD.")
        if timezone not in pytz.all_timezones:
            raise ValueError(f"Unknown timezone '{timezone}'. Use IANA format (e.g. 'Asia/Kolkata').")
        natal_chart = json.loads(natal_chart_json)
        result = calculate_transit(
            transit_date_str=transit_date,
            natal_chart=natal_chart,
            timezone_str=timezone,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def calculate_compatibility(
    dob1: str, time1: str, lat1: float, lon1: float, tz1: str,
    dob2: str, time2: str, lat2: float, lon2: float, tz2: str
) -> str:
    """
    Calculates traditional 36-point Ashtakoot relationship compatibility between two people.
    By tradition, Person 1 (dob1) should be Male and Person 2 (dob2) should be Female for accurate points.
    
    Returns the score breakdown (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi),
    additional kutas (Mahendra, Stree Deergha, Vedha), Kuja Dosha analysis,
    and the total score out of 36.
    
    Parameters:
        dob1, time1, lat1, lon1, tz1: Birth details for Person 1 (e.g. "1990-04-15", "14:30")
        dob2, time2, lat2, lon2, tz2: Birth details for Person 2
    """
    try:
        from vedic_calculator import calculate_vedic_chart
        from matchmaking import calculate_ashtakoot, calc_kuja_dosha, match_kuja_dosha
        from constants import ZODIAC_SIGNS

        _validate_birth_input(dob1, time1, lat1, lon1, tz1)
        _validate_birth_input(dob2, time2, lat2, lon2, tz2)

        chart1 = calculate_vedic_chart(dob1, time1, lat1, lon1, tz1)
        chart2 = calculate_vedic_chart(dob2, time2, lat2, lon2, tz2)
        
        m_moon = chart1["planets"]["Moon"]
        f_moon = chart2["planets"]["Moon"]
        
        m_lon = ZODIAC_SIGNS.index(m_moon["sign"]) * 30 + m_moon["degree"]
        f_lon = ZODIAC_SIGNS.index(f_moon["sign"]) * 30 + f_moon["degree"]
        
        score = calculate_ashtakoot(m_lon, f_lon, male_chart=chart1, female_chart=chart2)

        # Kuja Dosha (Manglik) analysis
        male_dosha = calc_kuja_dosha(chart1)
        female_dosha = calc_kuja_dosha(chart2)
        kuja_match = match_kuja_dosha(male_dosha["total_score"], female_dosha["total_score"])
        score["kuja_dosha"] = {
            "male": male_dosha,
            "female": female_dosha,
            "compatibility": kuja_match,
        }

        return json.dumps(score, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def check_muhurtha(
    activity: str,
    date: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
) -> str:
    """
    Check if a date/time is auspicious for a specific activity (electional astrology).

    Evaluates Panchang purity, nakshatra suitability, tithi, weekday, Lagna, and
    activity-specific doshas to determine muhurtha quality.

    Parameters:
        activity: Type of activity — one of 'marriage', 'travel', 'business', 'education', 'house_entry', 'medical'
        date: Date to evaluate as "YYYY-MM-DD"
        time: Time to evaluate as "HH:MM" (24h format)
        lat: Location latitude
        lon: Location longitude
        timezone: IANA timezone string
    """
    try:
        _validate_birth_input(date, time, lat, lon, timezone)
        from muhurtha import evaluate_muhurtha, ACTIVITY_RULES
        if activity not in ACTIVITY_RULES:
            raise ValueError(f"Unknown activity '{activity}'. Supported: {list(ACTIVITY_RULES.keys())}")
        chart = calculate_vedic_chart(date, time, lat, lon, timezone)
        panchang = chart.get("panchang", {})
        planets = chart.get("planets", {})
        lagna_sign = chart.get("lagna", {}).get("sign")
        result = evaluate_muhurtha(activity, panchang, planets, lagna_sign)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def analyze_career_chart(
    dob: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
) -> str:
    """
    Analyze career potential using the 10th house, D10 Dashamsha, and planetary significations.

    Returns career themes, strength factors, D10 planet analysis, and domain recommendations
    based on the 10th house lord, occupants, dignity, and D10 divisional chart.

    Parameters:
        dob: Date of birth as "YYYY-MM-DD"
        time: Time of birth as "HH:MM" (24h)
        lat: Birth latitude
        lon: Birth longitude
        timezone: IANA timezone string
    """
    try:
        _validate_birth_input(dob, time, lat, lon, timezone)
        from career import analyze_career
        chart = calculate_vedic_chart(dob, time, lat, lon, timezone)
        planets = chart.get("planets", {})
        lagna_sign = chart.get("lagna", {}).get("sign")
        result = analyze_career(planets, lagna_sign)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
