import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from vedic_calculator import calculate_vedic_chart, calculate_transit

mcp = FastMCP("vedic-astrology", instructions="Vedic Astrology chart calculator using Swiss Ephemeris (Sidereal Lahiri)")


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
    
    Returns the score breakdown (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi)
    and the total score out of 36.
    
    Parameters:
        dob1, time1, lat1, lon1, tz1: Birth details for Person 1 (e.g. "1990-04-15", "14:30")
        dob2, time2, lat2, lon2, tz2: Birth details for Person 2
    """
    try:
        from vedic_calculator import calculate_vedic_chart
        from matchmaking import calculate_ashtakoot
        from constants import ZODIAC_SIGNS
        
        chart1 = calculate_vedic_chart(dob1, time1, lat1, lon1, tz1)
        chart2 = calculate_vedic_chart(dob2, time2, lat2, lon2, tz2)
        
        m_moon = chart1["planets"]["Moon"]
        f_moon = chart2["planets"]["Moon"]
        
        m_lon = ZODIAC_SIGNS.index(m_moon["sign"]) * 30 + m_moon["degree"]
        f_lon = ZODIAC_SIGNS.index(f_moon["sign"]) * 30 + f_moon["degree"]
        
        score = calculate_ashtakoot(m_lon, f_lon)
        return json.dumps(score, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
