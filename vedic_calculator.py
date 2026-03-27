import swisseph as swe
import datetime
import pytz
import json

from constants import PLANETS, ZODIAC_SIGNS, SIGN_LORDS
from nakshatra import get_nakshatra
from dasha import calculate_dashas
from dignity import get_dignity, check_combustion, get_digbala
from yoga import detect_yogas
from panchang import calculate_panchang
from ashtakavarga import calculate_ashtakavarga
from jaimini import calculate_jaimini_karakas
from shadbala import calculate_shadbala

swe.set_ephe_path('')


def get_sign_and_degree(longitude):
    """Converts 360-degree longitude to Zodiac Sign and degree within that sign."""
    longitude = longitude % 360.0
    sign_idx = int(longitude / 30)
    if sign_idx >= 12:
        sign_idx = 11
    degree = longitude % 30
    return ZODIAC_SIGNS[sign_idx], round(degree, 2), sign_idx


def calculate_navamsha(longitude):
    """Calculates D9 (Navamsha) sign based on absolute longitude."""
    navamsha_absolute = (longitude * 9) % 360
    sign_idx = int(navamsha_absolute / 30)
    return ZODIAC_SIGNS[sign_idx]


def calculate_dashamsha(longitude):
    """Calculates D10 (Dashamsha) sign per BPHS Parashari method."""
    sign_idx = int(longitude / 30)
    degree_in_sign = longitude % 30
    part = int(degree_in_sign / 3.0)

    if (sign_idx + 1) % 2 != 0:  # odd sign (1-indexed)
        d10_idx = (sign_idx + part) % 12
    else:
        d10_idx = (sign_idx + 8 + part) % 12

    return ZODIAC_SIGNS[d10_idx]

def calculate_d3_drekkana(longitude):
    """Calculates D3 (Drekkana) sign."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / 10.0)
    if part == 0:
        d3_idx = sign_idx
    elif part == 1:
        d3_idx = (sign_idx + 4) % 12
    else:
        d3_idx = (sign_idx + 8) % 12
    return ZODIAC_SIGNS[d3_idx]

def calculate_d4_chaturthamsha(longitude):
    """Calculates D4 (Chaturthamsha) sign."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / 7.5)
    d4_idx = (sign_idx + (part * 3)) % 12
    return ZODIAC_SIGNS[d4_idx]

def calculate_d7_saptamsha(longitude):
    """Calculates D7 (Saptamsha) sign."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / (30.0 / 7.0))
    if (sign_idx + 1) % 2 != 0:  # Odd sign
        d7_idx = (sign_idx + part) % 12
    else:  # Even sign
        d7_idx = (sign_idx + 6 + part) % 12
    return ZODIAC_SIGNS[d7_idx]

def calculate_d12_dwadashamsha(longitude):
    """Calculates D12 (Dwadashamsha) sign."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / 2.5)
    d12_idx = (sign_idx + part) % 12
    return ZODIAC_SIGNS[d12_idx]

def calculate_d24_chaturvimshamsha(longitude):
    """Calculates D24 (Chaturvimshamsha / Siddhamsha) sign — Education & Learning.
    Odd signs: count from Leo. Even signs: count from Cancer."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / (30.0 / 24.0))
    if (sign_idx + 1) % 2 != 0:  # Odd sign
        d24_idx = (4 + part) % 12  # Leo = index 4
    else:
        d24_idx = (3 + part) % 12  # Cancer = index 3
    return ZODIAC_SIGNS[d24_idx]

def calculate_d30_trimshamsha(longitude):
    """Calculates D30 (Trimshamsha) sign — Misfortunes & Diseases.
    Uses the BPHS unequal division: 5°, 5°, 8°, 7°, 5° for odd signs
    and reversed for even signs."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    is_odd = (sign_idx + 1) % 2 != 0

    if is_odd:
        # Odd: Mars(5), Saturn(5), Jupiter(8), Mercury(7), Venus(5)
        if degree < 5: lord = "Mars"
        elif degree < 10: lord = "Saturn"
        elif degree < 18: lord = "Jupiter"
        elif degree < 25: lord = "Mercury"
        else: lord = "Venus"
    else:
        # Even: Venus(5), Mercury(7), Jupiter(8), Saturn(5), Mars(5)
        if degree < 5: lord = "Venus"
        elif degree < 12: lord = "Mercury"
        elif degree < 20: lord = "Jupiter"
        elif degree < 25: lord = "Saturn"
        else: lord = "Mars"

    # D30 sign = the sign owned by the lord
    from constants import OWN_SIGNS
    return OWN_SIGNS[lord][0]  # Return the first own sign

def calculate_d60_shashtiamsha(longitude):
    """Calculates D60 (Shashtiamsha) sign.
    BPHS: Odd signs count from self, Even signs count from opposite (7th)."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / 0.5)
    if (sign_idx + 1) % 2 != 0:  # Odd sign
        d60_idx = (sign_idx + part) % 12
    else:  # Even sign
        d60_idx = (sign_idx + 6 + part) % 12
    return ZODIAC_SIGNS[d60_idx]

def get_vedic_aspects(planet_name, sign_idx):
    """
    Calculates the signs aspected by a planet based on BPHS rules.
    Standard Parashari: only Mars, Jupiter, Saturn have special aspects.
    Rahu/Ketu get only the universal 7th aspect.
    """
    aspected_indices = [(sign_idx + 6) % 12]

    if planet_name == "Mars":
        aspected_indices.extend([(sign_idx + 3) % 12, (sign_idx + 7) % 12])
    elif planet_name == "Jupiter":
        aspected_indices.extend([(sign_idx + 4) % 12, (sign_idx + 8) % 12])
    elif planet_name == "Saturn":
        aspected_indices.extend([(sign_idx + 2) % 12, (sign_idx + 9) % 12])

    return [ZODIAC_SIGNS[idx] for idx in sorted(set(aspected_indices))]


def _house_from_lagna(planet_sign_idx, lagna_sign_idx):
    """Whole-sign house number (1-12) from the Ascendant sign."""
    return ((planet_sign_idx - lagna_sign_idx) % 12) + 1


def _to_jd(dob_str, time_str, timezone_str):
    """Convert local date/time to Julian Day and return (jd, birth_dt_local)."""
    local_tz = pytz.timezone(timezone_str)
    naive_dt = datetime.datetime.strptime(f"{dob_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    year, month, day = utc_dt.year, utc_dt.month, utc_dt.day
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = swe.julday(year, month, day, hour)
    return jd, local_dt


def calculate_vedic_chart(dob_str: str, time_str: str, lat: float, lon: float, timezone_str: str,
                          query_date_str: str = None):
    """
    Calculates a comprehensive Vedic Astrological Chart (Sidereal Lahiri).

    Parameters
    ----------
    dob_str : str  "YYYY-MM-DD"
    time_str : str "HH:MM" (24-hour format)
    lat : float    Latitude (e.g., 28.6139 for Delhi)
    lon : float    Longitude (e.g., 77.2090 for Delhi)
    timezone_str : str  (e.g., "Asia/Kolkata")
    query_date_str : str, optional  "YYYY-MM-DD" for Dasha lookup. Defaults to today.

    Returns
    -------
    dict: Full chart data including planets, nakshatra, dasha, yogas, panchang.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd, local_dt = _to_jd(dob_str, time_str, timezone_str)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    ayanamsha_val = swe.get_ayanamsa_ut(jd)

    # --- Ascendant (Lagna) ---
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)
    asc_lon = ascmc[0]
    asc_sign, asc_deg, asc_sign_idx = get_sign_and_degree(asc_lon)
    asc_nak = get_nakshatra(asc_lon)

    # --- Planetary positions ---
    raw_planets = {}
    sun_lon = None

    for name, planet_id in PLANETS.items():
        res, _ = swe.calc_ut(jd, planet_id, flags)
        planet_lon = res[0]
        speed = res[3]

        sign, deg, sign_idx = get_sign_and_degree(planet_lon)

        if name in ("Rahu", "Ketu"):
            is_retrograde = True
        elif name in ("Sun", "Moon"):
            is_retrograde = False
        else:
            is_retrograde = speed < 0

        if name == "Sun":
            sun_lon = planet_lon

        raw_planets[name] = {
            "lon": planet_lon,
            "sign": sign,
            "degree": deg,
            "sign_idx": sign_idx,
            "speed": speed,
            "is_retrograde": is_retrograde,
        }

    # Ketu = Rahu + 180
    rahu_data = raw_planets["Rahu"]
    ketu_lon = (rahu_data["lon"] + 180) % 360
    k_sign, k_deg, k_sign_idx = get_sign_and_degree(ketu_lon)
    raw_planets["Ketu"] = {
        "lon": ketu_lon,
        "sign": k_sign,
        "degree": k_deg,
        "sign_idx": k_sign_idx,
        "speed": -abs(rahu_data["speed"]),
        "is_retrograde": True,
    }

    # --- Build enriched planet data ---
    planets_output = {}
    planets_for_yoga = {}
    planets_in_signs = {name: rp["sign_idx"] for name, rp in raw_planets.items()}

    for name, rp in raw_planets.items():
        house = _house_from_lagna(rp["sign_idx"], asc_sign_idx)
        nak = get_nakshatra(rp["lon"])
        dignity = get_dignity(name, rp["sign"], rp["degree"], planets_in_signs)
        is_combust = check_combustion(name, rp["lon"], sun_lon, rp["is_retrograde"]) if sun_lon is not None else False
        has_digbala = get_digbala(name, house)

        planet_entry = {
            "sign": rp["sign"],
            "degree": rp["degree"],
            "house": house,
            "nakshatra": nak["name"],
            "pada": nak["pada"],
            "nakshatra_lord": nak["lord"],
            "is_retrograde": rp["is_retrograde"],
            "is_combust": is_combust,
            "dignity": dignity,
            "has_digbala": has_digbala,
            "d3_sign": calculate_d3_drekkana(rp["lon"]),
            "d4_sign": calculate_d4_chaturthamsha(rp["lon"]),
            "d7_sign": calculate_d7_saptamsha(rp["lon"]),
            "d9_sign": calculate_navamsha(rp["lon"]),
            "d10_sign": calculate_dashamsha(rp["lon"]),
            "d12_sign": calculate_d12_dwadashamsha(rp["lon"]),
            "d24_sign": calculate_d24_chaturvimshamsha(rp["lon"]),
            "d30_sign": calculate_d30_trimshamsha(rp["lon"]),
            "d60_sign": calculate_d60_shashtiamsha(rp["lon"]),
            "aspects": get_vedic_aspects(name, rp["sign_idx"]),
        }
        planets_output[name] = planet_entry
        planets_for_yoga[name] = {
            "sign": rp["sign"],
            "sign_idx": rp["sign_idx"],
            "house": house,
            "dignity": dignity,
            "is_combust": is_combust,
        }

    # --- Dasha ---
    moon_lon = raw_planets["Moon"]["lon"]
    birth_dt_naive = local_dt.replace(tzinfo=None)

    query_dt = None
    if query_date_str:
        query_dt = datetime.datetime.strptime(query_date_str, "%Y-%m-%d")
    else:
        query_dt = datetime.datetime.now()

    dasha_data = calculate_dashas(moon_lon, birth_dt_naive, query_dt)

    # --- Yogas ---
    yogas = detect_yogas(planets_for_yoga, asc_sign)

    # --- Panchang ---
    panchang_data = calculate_panchang(jd, sun_lon, moon_lon, lat, lon)

    # --- Ashtakavarga ---
    sav_planets = {name: rp["sign_idx"] for name, rp in raw_planets.items() if name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]}
    ashtakavarga_data = calculate_ashtakavarga(sav_planets, asc_sign_idx)

    # --- Assemble output ---
    chart_data = {
        "metadata": {
            "dob": dob_str,
            "time": time_str,
            "coordinates": {"lat": lat, "lon": lon},
            "timezone": timezone_str,
            "ayanamsha": "Lahiri",
            "ayanamsha_degrees": round(ayanamsha_val, 4),
            "query_date": query_dt.strftime("%Y-%m-%d"),
        },
        "panchang": panchang_data,
        "lagna": {
            "sign": asc_sign,
            "degree": asc_deg,
            "nakshatra": asc_nak["name"],
            "pada": asc_nak["pada"],
            "d3_sign": calculate_d3_drekkana(asc_lon),
            "d4_sign": calculate_d4_chaturthamsha(asc_lon),
            "d7_sign": calculate_d7_saptamsha(asc_lon),
            "d9_sign": calculate_navamsha(asc_lon),
            "d10_sign": calculate_dashamsha(asc_lon),
            "d12_sign": calculate_d12_dwadashamsha(asc_lon),
            "d24_sign": calculate_d24_chaturvimshamsha(asc_lon),
            "d30_sign": calculate_d30_trimshamsha(asc_lon),
            "d60_sign": calculate_d60_shashtiamsha(asc_lon),
        },
        "planets": planets_output,
        "dashas": dasha_data,
        "yogas": yogas,
        "ashtakavarga": ashtakavarga_data,
        "jaimini_karakas": calculate_jaimini_karakas(planets_output),
        "shadbala": calculate_shadbala(planets_output, raw_planets),
    }

    return chart_data


def calculate_transit(transit_date_str: str, natal_chart: dict, timezone_str: str = "Asia/Kolkata"):
    """
    Calculate current planetary transit positions and overlay on natal chart.

    Parameters
    ----------
    transit_date_str : str  "YYYY-MM-DD"
    natal_chart : dict  Output from calculate_vedic_chart()
    timezone_str : str

    Returns
    -------
    dict with transit planets, house placements from natal Lagna/Moon, and Sade Sati status.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    # Transit at noon on the given date
    dt = datetime.datetime.strptime(transit_date_str, "%Y-%m-%d")
    local_tz = pytz.timezone(timezone_str)
    local_noon = local_tz.localize(dt.replace(hour=12))
    utc_noon = local_noon.astimezone(pytz.utc)
    jd = swe.julday(utc_noon.year, utc_noon.month, utc_noon.day,
                     utc_noon.hour + utc_noon.minute / 60.0)

    natal_lagna_sign = natal_chart["lagna"]["sign"]
    natal_lagna_idx = ZODIAC_SIGNS.index(natal_lagna_sign)

    natal_moon_sign = natal_chart["planets"]["Moon"]["sign"]
    natal_moon_idx = ZODIAC_SIGNS.index(natal_moon_sign)

    transit_planets = {}
    transit_sun_lon = None

    for name, planet_id in PLANETS.items():
        res, _ = swe.calc_ut(jd, planet_id, flags)
        planet_lon = res[0]
        speed = res[3]
        sign, deg, sign_idx = get_sign_and_degree(planet_lon)

        if name in ("Rahu", "Ketu"):
            is_retro = True
        elif name in ("Sun", "Moon"):
            is_retro = False
        else:
            is_retro = speed < 0

        if name == "Sun":
            transit_sun_lon = planet_lon

        house_from_lagna = _house_from_lagna(sign_idx, natal_lagna_idx)
        house_from_moon = _house_from_lagna(sign_idx, natal_moon_idx)

        transit_planets[name] = {
            "sign": sign,
            "degree": deg,
            "is_retrograde": is_retro,
            "nakshatra": get_nakshatra(planet_lon)["name"],
            "house_from_lagna": house_from_lagna,
            "house_from_moon": house_from_moon,
            "sav_points": natal_chart.get("ashtakavarga", {}).get("sarvashtakavarga", {}).get(sign, 0)
        }

    # Ketu
    rahu_lon = transit_planets["Rahu"]
    rahu_raw_lon = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0]
    ketu_lon = (rahu_raw_lon + 180) % 360
    k_sign, k_deg, k_sign_idx = get_sign_and_degree(ketu_lon)
    transit_planets["Ketu"] = {
        "sign": k_sign,
        "degree": k_deg,
        "is_retrograde": True,
        "nakshatra": get_nakshatra(ketu_lon)["name"],
        "house_from_lagna": _house_from_lagna(k_sign_idx, natal_lagna_idx),
        "house_from_moon": _house_from_lagna(k_sign_idx, natal_moon_idx),
        "sav_points": natal_chart.get("ashtakavarga", {}).get("sarvashtakavarga", {}).get(k_sign, 0)
    }

    # --- Sade Sati detection ---
    saturn_sign_idx = ZODIAC_SIGNS.index(transit_planets["Saturn"]["sign"])
    sade_sati_active = False
    sade_sati_phase = None
    dist = (saturn_sign_idx - natal_moon_idx) % 12
    if dist == 11:
        sade_sati_active = True
        sade_sati_phase = "rising (12th from Moon)"
    elif dist == 0:
        sade_sati_active = True
        sade_sati_phase = "peak (over Moon)"
    elif dist == 1:
        sade_sati_active = True
        sade_sati_phase = "setting (2nd from Moon)"

    # --- Rahu-Ketu transit axis ---
    rahu_house_lagna = transit_planets["Rahu"]["house_from_lagna"]
    ketu_house_lagna = transit_planets["Ketu"]["house_from_lagna"]

    return {
        "transit_date": transit_date_str,
        "planets": transit_planets,
        "sade_sati": {
            "active": sade_sati_active,
            "phase": sade_sati_phase,
            "saturn_transit_sign": transit_planets["Saturn"]["sign"],
            "natal_moon_sign": natal_moon_sign,
        },
        "rahu_ketu_axis": {
            "rahu_house_from_lagna": rahu_house_lagna,
            "ketu_house_from_lagna": ketu_house_lagna,
            "rahu_sign": transit_planets["Rahu"]["sign"],
            "ketu_sign": transit_planets["Ketu"]["sign"],
        },
    }


if __name__ == "__main__":
    data = calculate_vedic_chart(
        dob_str="1990-04-15",
        time_str="14:30",
        lat=28.6139,
        lon=77.2090,
        timezone_str="Asia/Kolkata"
    )
    print("=== NATAL CHART ===")
    print(json.dumps(data, indent=2))

    print("\n=== TRANSIT ===")
    transit = calculate_transit("2026-02-28", data)
    print(json.dumps(transit, indent=2))
