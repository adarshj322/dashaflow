import math
from .constants import TITHI_NAMES, VARA_NAMES, VARA_LORDS, PANCHANG_YOGA_NAMES, KARANA_NAMES
from .nakshatra import get_nakshatra
import logging

logger = logging.getLogger(__name__)


def calculate_panchang(jd, sun_lon, moon_lon, lat=None, lon=None):
    """
    Calculate the five Panchang elements for a given moment.

    Parameters
    ----------
    jd : float
        Julian Day number
    sun_lon : float
        Sidereal longitude of the Sun (0-360)
    moon_lon : float
        Sidereal longitude of the Moon (0-360)

    Returns
    -------
    dict with tithi, vara, nakshatra, yoga, karana
    """
    # --- Tithi ---
    # Epsilon guards float boundary flicker (e.g. 11.9999999 vs 12.0).
    _EPS = 1e-9
    diff = (moon_lon - sun_lon) % 360.0
    tithi_num = int((diff + _EPS) / 12.0)  # 0-29
    if tithi_num > 29:
        tithi_num = 29
    paksha = "Shukla" if tithi_num < 15 else "Krishna"
    tithi_name = TITHI_NAMES[tithi_num]

    # --- Vara (weekday) ---
    # Verified: JD 2451545.0 (2000-01-01 12:00 UT, a Saturday) gives
    # floor(2451545.0 + 0.5) % 7 = 5 → VARA_NAMES[5] = "Saturday". So 0=Mon..6=Sun.
    day_idx = int(math.floor(jd + 0.5)) % 7

    # Correct for local sunrise if lat/lon provided
    if lat is not None and lon is not None:
        try:
            import swisseph as swe
            swe.set_topo(lon, lat, 0)
            # Find the sunrise for the current civil day UT
            jd_midnight = math.floor(jd - 0.5) + 0.5
            res, tret = swe.rise_trans(jd_midnight, swe.SUN, "", swe.CALC_RISE, (lon, lat, 0.0))
            sunrise_jd = tret[0]
            # If born before today's sunrise, the Vedic day is yesterday
            if jd < sunrise_jd:
                day_idx = (day_idx - 1) % 7
        except Exception as exc:
            # Sunrise correction is best-effort (ephemeris gaps, polar edge
            # cases); fall back to civil-day vara rather than failing the chart.
            logger.debug("sunrise vara correction skipped: %s", exc)
            pass

    # JD 0 = Monday (Julian proleptic). Map: 0=Mon,1=Tue,...6=Sun
    vara = VARA_NAMES[day_idx]
    vara_lord = VARA_LORDS[day_idx]

    # --- Nakshatra (Moon's) ---
    nak = get_nakshatra(moon_lon)

    # --- Yoga (Panchang Yoga) ---
    yoga_val = (sun_lon + moon_lon) % 360.0
    yoga_idx = int((yoga_val + _EPS) / (360.0 / 27.0))
    if yoga_idx >= 27:
        yoga_idx = 26
    yoga_name = PANCHANG_YOGA_NAMES[yoga_idx]

    # --- Karana ---
    # Each tithi has 2 karanas (half-tithi = 6 degrees of Sun-Moon distance)
    karana_num = int((diff + _EPS) / 6.0)  # 0-59
    if karana_num > 59:
        karana_num = 59
    if karana_num == 0:
        karana_name = KARANA_NAMES[10]  # Kimstughna (first half of Shukla Pratipada)
    elif karana_num >= 57:
        # Last 3 are fixed karanas: Shakuni(57), Chatushpada(58), Nagava(59)
        fixed_idx = karana_num - 57 + 7  # maps to indices 7,8,9
        karana_name = KARANA_NAMES[fixed_idx]
    else:
        # Repeating cycle of first 7 karanas (Bava through Vishti)
        karana_name = KARANA_NAMES[(karana_num - 1) % 7]

    return {
        "tithi": {
            "number": tithi_num + 1,
            "name": tithi_name,
            "paksha": paksha,
        },
        "vara": {
            "name": vara,
            "lord": vara_lord,
        },
        "nakshatra": {
            "name": nak["name"],
            "pada": nak["pada"],
            "lord": nak["lord"],
        },
        "yoga": {
            "index": yoga_idx,
            "name": yoga_name,
        },
        "karana": karana_name,
    }
