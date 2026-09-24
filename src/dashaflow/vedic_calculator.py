import swisseph as swe
import datetime
import logging
import threading
import time
import pytz

from ._version import __version__
from .constants import PLANETS, ZODIAC_SIGNS, OWN_SIGNS
from .errors import CalculationError, EphemerisError, InvalidInputError
from .nakshatra import get_nakshatra
from .dasha import calculate_dashas
from .dignity import get_dignity, check_combustion, get_digbala
from .yoga import detect_yogas, detect_kaal_sarpa, detect_graha_yuddha, detect_gandanta
from .panchang import calculate_panchang
from .ashtakavarga import calculate_ashtakavarga
from .jaimini import calculate_jaimini_karakas, calculate_arudha_padas, calculate_upapada, calculate_karakamsha
from .shadbala import calculate_shadbala

logger = logging.getLogger(__name__)

# Swiss Ephemeris uses process-global state (ephe path + sidereal mode) and
# its calc entry points are affected by it. A single re-entrant lock guards
# the whole configure→compute section so concurrent chart calculations (or
# host-app swe users) cannot interleave configuration with computation.
# Throughput note: the locked section is ~10 swe calls (milliseconds); pure
# Python enrichment runs outside the lock.
_SWE_LOCK = threading.RLock()

# Years outside this range fall back to the Moshier analytic ephemeris when
# no extended .se1 files are provided (reduced accuracy vs full integration).
_FULL_ACCURACY_RANGE = (1800, 2400)


def _ephemeris_accuracy(birth_year: int, ephe_path: str) -> str:
    """'full' inside the integrated range (or with custom files), else Moshier fallback."""
    if ephe_path:
        return "full (custom ephemeris path)"
    lo, hi = _FULL_ACCURACY_RANGE
    if lo <= birth_year <= hi:
        return "full"
    return "reduced (Moshier fallback — provide .se1 files via ephe_path for full accuracy)"


def _configure_swiss_ephemeris(ephe_path: str = '') -> None:
    """Set ephemeris path + Lahiri sidereal mode. Callers must hold _SWE_LOCK."""
    swe.set_ephe_path(ephe_path or '')
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def get_sign_and_degree(longitude: float) -> tuple:
    """Converts 360-degree longitude to Zodiac Sign and degree within that sign."""
    longitude = longitude % 360.0
    sign_idx = int(longitude / 30) % 12
    degree = longitude % 30
    return ZODIAC_SIGNS[sign_idx], round(degree, 2), sign_idx


def calculate_navamsha(longitude):
    """Calculates D9 (Navamsha) sign based on absolute longitude."""
    navamsha_absolute = (longitude * 9) % 360
    sign_idx = int(navamsha_absolute / 30)
    return ZODIAC_SIGNS[sign_idx]


def calculate_d2_hora(longitude):
    """Calculates D2 (Hora) sign — Wealth.
    Odd signs: 0-15° → Leo, 15-30° → Cancer.
    Even signs: 0-15° → Cancer, 15-30° → Leo.
    Validated against VedAstro Vargas.cs HoraTable."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    is_odd = (sign_idx + 1) % 2 != 0
    if is_odd:
        return "Leo" if degree < 15 else "Cancer"
    else:
        return "Cancer" if degree < 15 else "Leo"


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


def calculate_d16_shodashamsha(longitude):
    """Calculates D16 (Shodashamsha) sign — Vehicles, Comforts, Happiness.
    16 equal parts of 1.875° each.
    Start sign = (sign_idx * 4) % 12 counted from Aries.
    Validated against VedAstro Vargas.cs ShodashamshaTable."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / 1.875)
    if part >= 16:
        part = 15
    start_idx = (sign_idx * 4) % 12
    d16_idx = (start_idx + part) % 12
    return ZODIAC_SIGNS[d16_idx]


def calculate_d20_vimshamsha(longitude):
    """Calculates D20 (Vimshamsha) sign — Spiritual Progress, Worship.
    20 equal parts of 1.5° each.
    Start sign = (sign_idx * 8) % 12 counted from Aries.
    Validated against VedAstro Vargas.cs VimshamshaTable."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / 1.5)
    if part >= 20:
        part = 19
    start_idx = (sign_idx * 8) % 12
    d20_idx = (start_idx + part) % 12
    return ZODIAC_SIGNS[d20_idx]


def calculate_d27_bhamsha(longitude):
    """Calculates D27 (Bhamsha / Saptavimshamsha) sign — Strength, Courage.
    27 equal parts of ~1.1111° each.
    Fire signs (Aries,Leo,Sag) start from Aries.
    Earth signs (Taurus,Virgo,Cap) start from Cancer.
    Air signs (Gemini,Libra,Aqua) start from Libra.
    Water signs (Cancer,Scorpio,Pisces) start from Capricorn.
    Validated against VedAstro Vargas.cs BhamshaTable."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / (30.0 / 27.0))
    if part >= 27:
        part = 26
    # Determine element of the sign (0=Fire, 1=Earth, 2=Air, 3=Water)
    element = sign_idx % 4
    if element == 0:    # Fire signs: Aries(0), Leo(4), Sagittarius(8)
        start_idx = 0   # Aries
    elif element == 1:  # Earth signs: Taurus(1), Virgo(5), Capricorn(9)
        start_idx = 3   # Cancer
    elif element == 2:  # Air signs: Gemini(2), Libra(6), Aquarius(10)
        start_idx = 6   # Libra
    else:               # Water signs: Cancer(3), Scorpio(7), Pisces(11)
        start_idx = 9   # Capricorn
    d27_idx = (start_idx + part) % 12
    return ZODIAC_SIGNS[d27_idx]

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


def calculate_d40_khavedamsha(longitude):
    """Calculates D40 (Khavedamsha / Akshavedamsha) sign — Auspicious/Inauspicious effects.
    40 equal parts of 0.75° each.
    Odd signs start from Aries, Even signs start from Libra.
    Per K.S. Charak / VedAstro Vargas.cs AkshavedamshaTable."""
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    part = int(degree / 0.75)
    if part >= 40:
        part = 39
    if (sign_idx + 1) % 2 != 0:  # Odd sign
        start_idx = 0   # Aries
    else:                         # Even sign
        start_idx = 6   # Libra
    d40_idx = (start_idx + part) % 12
    return ZODIAC_SIGNS[d40_idx]


# Table-driven varga dispatch: output key -> calculator function.
# Eliminates 15x14 lines of repeated dX_sign calls for Lagna + each planet.
VARGA_CALCS = {
    "d2_sign": calculate_d2_hora,
    "d3_sign": calculate_d3_drekkana,
    "d4_sign": calculate_d4_chaturthamsha,
    "d7_sign": calculate_d7_saptamsha,
    "d9_sign": calculate_navamsha,
    "d10_sign": calculate_dashamsha,
    "d12_sign": calculate_d12_dwadashamsha,
    "d16_sign": calculate_d16_shodashamsha,
    "d20_sign": calculate_d20_vimshamsha,
    "d24_sign": calculate_d24_chaturvimshamsha,
    "d27_sign": calculate_d27_bhamsha,
    "d30_sign": calculate_d30_trimshamsha,
    "d40_sign": calculate_d40_khavedamsha,
    "d60_sign": calculate_d60_shashtiamsha,
}


def calculate_all_vargas(longitude: float) -> dict:
    """Return all 14 varga signs for an absolute longitude."""
    lon = longitude % 360.0
    return {key: fn(lon) for key, fn in VARGA_CALCS.items()}


def _synthesize_ketu(rahu_data: dict) -> dict:
    """Ketu is always exactly opposite Rahu (mean node + 180°). Single source of truth."""
    ketu_lon = (rahu_data["lon"] + 180) % 360
    k_sign, k_deg, k_sign_idx = get_sign_and_degree(ketu_lon)
    return {
        "lon": ketu_lon,
        "lat": -rahu_data.get("lat", 0.0),
        "sign": k_sign,
        "degree": k_deg,
        "sign_idx": k_sign_idx,
        "speed": -abs(rahu_data["speed"]),
        "is_retrograde": True,
    }


def _compute_raw_planets(jd: float, flags: int) -> tuple:
    """Compute sidereal longitudes for all grahas. Returns (raw_planets, sun_lon)."""
    raw_planets = {}
    sun_lon = None
    for name, planet_id in PLANETS.items():
        res, _ = swe.calc_ut(jd, planet_id, flags)
        planet_lon = res[0]
        planet_lat = res[1]
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
            "lat": planet_lat,
            "sign": sign,
            "degree": deg,
            "sign_idx": sign_idx,
            "speed": speed,
            "is_retrograde": is_retrograde,
        }
    raw_planets["Ketu"] = _synthesize_ketu(raw_planets["Rahu"])
    return raw_planets, sun_lon


def _enrich_planets(raw_planets: dict, asc_sign_idx: int, sun_lon: float) -> tuple:
    """Build enriched planet output + minimal yoga input from raw positions."""
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
            "aspects": get_vedic_aspects(name, rp["sign_idx"]),
        }
        planet_entry.update(calculate_all_vargas(rp["lon"]))
        planets_output[name] = planet_entry
        planets_for_yoga[name] = {
            "sign": rp["sign"],
            "sign_idx": rp["sign_idx"],
            "house": house,
            "dignity": dignity,
            "is_combust": is_combust,
            "is_retrograde": rp["is_retrograde"],
        }
    return planets_output, planets_for_yoga


def get_vedic_aspects(planet_name: str, sign_idx: int) -> list:
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


def _house_from_lagna(planet_sign_idx: int, lagna_sign_idx: int) -> int:
    """Whole-sign house number (1-12) from the Ascendant sign."""
    return ((planet_sign_idx - lagna_sign_idx) % 12) + 1


def _to_jd(dob_str: str, time_str: str, timezone_str: str) -> tuple:
    """Convert local date/time to Julian Day and return (jd, birth_dt_local)."""
    try:
        local_tz = pytz.timezone(timezone_str)
    except Exception:
        raise InvalidInputError(f"Unknown timezone '{timezone_str}'. Use IANA format.") from None
    try:
        naive_dt = datetime.datetime.strptime(f"{dob_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise InvalidInputError(f"Invalid date/time '{dob_str} {time_str}'. Expected YYYY-MM-DD HH:MM.") from None
    try:
        # is_dst=None forces pytz to raise (rather than silently resolve)
        # ambiguous fall-back hours and spring-forward gaps — a birth time
        # must map to exactly one instant for a correct chart.
        local_dt = local_tz.localize(naive_dt, is_dst=None)
    except Exception as exc:
        # pytz raises AmbiguousTimeError/NonExistentTimeError (not ValueError
        # subclasses) for DST transitions — map into the error taxonomy.
        raise InvalidInputError(
            f"Non-existent or ambiguous local time '{dob_str} {time_str}' in '{timezone_str}': {exc}"
        ) from exc
    utc_dt = local_dt.astimezone(pytz.utc)

    year, month, day = utc_dt.year, utc_dt.month, utc_dt.day
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = swe.julday(year, month, day, hour)
    return jd, local_dt


def calculate_bhava_chalit(asc_lon: float, raw_planets: dict) -> dict:
    """
    Calculate Bhava Chalit (Equal House from Lagna midpoint).
    
    In Bhava Chalit, house cusps are at 15° before and after the Lagna degree.
    Bhava 1 midpoint = Lagna. Cusp 1 starts at (Lagna - 15°).
    Each house spans exactly 30°.
    
    A planet's Bhava house may differ from its Rashi (whole-sign) house
    when it's near a sign boundary.
    
    Returns
    -------
    dict: {planet_name: {"bhava_house": int, "rashi_house": int, "shifted": bool}}
    """
    # Bhava 1 midpoint is at the Lagna degree
    # Cusp of house 1 starts at asc_lon - 15°
    cusp_start = (asc_lon - 15.0) % 360.0
    
    asc_sign_idx = int(asc_lon / 30) % 12
    
    result = {}
    for name, rp in raw_planets.items():
        planet_lon = rp["lon"]
        
        # Rashi house (whole-sign)
        rashi_house = ((rp["sign_idx"] - asc_sign_idx) % 12) + 1
        
        # Bhava house (equal house from lagna midpoint)
        diff = (planet_lon - cusp_start) % 360.0
        bhava_house = int(diff / 30.0) + 1
        if bhava_house > 12:
            bhava_house = 12
        
        result[name] = {
            "bhava_house": bhava_house,
            "rashi_house": rashi_house,
            "shifted": bhava_house != rashi_house,
        }
    
    return result


def calculate_avasthas(planets_data: dict, raw_planets: dict) -> dict:
    """
    Calculate Planetary Avasthas (age states) per BPHS.
    
    Five states based on degree in sign:
    - Bala (Infant): 0-6° — weak, dependent, immature results
    - Kumara (Adolescent): 6-12° — growing, partially effective  
    - Yuva (Youth): 12-18° — full strength, best results
    - Vriddha (Old): 18-24° — declining, delayed results
    - Mrita (Dead): 24-30° — very weak, negligible results
    
    Returns
    -------
    dict: {planet_name: {"avastha": str, "degree": float, "strength_factor": float, "description": str}}
    """
    AVASTHA_TABLE = [
        ("Bala", 0, 6, 0.25, "Infant state — immature, dependent, weak delivery of results."),
        ("Kumara", 6, 12, 0.50, "Adolescent state — growing potential, partially effective."),
        ("Yuva", 12, 18, 1.00, "Youth state — full vigor, maximum capacity to deliver results."),
        ("Vriddha", 18, 24, 0.50, "Old state — declining energy, delayed or reduced results."),
        ("Mrita", 24, 30, 0.125, "Dead state — exhausted, negligible capacity to deliver results."),
    ]
    
    # For odd signs: Bala→Kumara→Yuva→Vriddha→Mrita (normal order)
    # For even signs: Mrita→Vriddha→Yuva→Kumara→Bala (reverse order)
    
    result = {}
    for name, rp in raw_planets.items():
        if name in ("Rahu", "Ketu"):
            continue
        
        degree = rp["degree"]
        sign_idx = rp["sign_idx"]
        is_odd_sign = (sign_idx % 2) == 0  # Aries=0 (odd), Taurus=1 (even), etc.
        
        if is_odd_sign:
            table = AVASTHA_TABLE
        else:
            table = list(reversed(AVASTHA_TABLE))
        
        avastha_name = "Yuva"
        strength_factor = 1.0
        description = ""
        
        for avastha, start, end, factor, desc in table:
            if start <= degree < end:
                avastha_name = avastha
                strength_factor = factor
                description = desc
                break
        
        result[name] = {
            "avastha": avastha_name,
            "degree": round(degree, 2),
            "strength_factor": strength_factor,
            "description": description,
        }
    
    return result


_REQUIRED_TOP_KEYS = frozenset({
    "metadata", "panchang", "lagna", "planets", "dashas", "yogas",
    "ashtakavarga", "jaimini_karakas", "shadbala", "bhava_chalit",
    "avasthas", "kaal_sarpa", "graha_yuddha", "gandanta",
    "arudha_padas", "upapada", "karakamsha",
})
_REQUIRED_PLANETS = frozenset({
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
})
_REQUIRED_PLANET_FIELDS = frozenset({
    "sign", "degree", "house", "nakshatra", "pada", "dignity",
    "is_retrograde", "is_combust", "aspects",
})


def _validate_chart_contract(chart_data: dict) -> None:
    """Output-contract gate: every chart leaving this module must satisfy it.

    Raises CalculationError (never returns False) so silent corruption can
    never reach API consumers.
    """
    missing = _REQUIRED_TOP_KEYS - set(chart_data)
    if missing:
        raise CalculationError(f"Chart missing top-level keys: {sorted(missing)}")
    planets = chart_data["planets"]
    missing_p = _REQUIRED_PLANETS - set(planets)
    if missing_p:
        raise CalculationError(f"Chart missing planets: {sorted(missing_p)}")
    for name, pd in planets.items():
        missing_f = _REQUIRED_PLANET_FIELDS - set(pd)
        if missing_f:
            raise CalculationError(f"Planet '{name}' missing fields: {sorted(missing_f)}")
        if pd["sign"] not in ZODIAC_SIGNS:
            raise CalculationError(f"Planet '{name}' has invalid sign: {pd['sign']!r}")
        if not 1 <= pd["house"] <= 12:
            raise CalculationError(f"Planet '{name}' has invalid house: {pd['house']!r}")
    if chart_data["lagna"]["sign"] not in ZODIAC_SIGNS:
        raise CalculationError(f"Lagna has invalid sign: {chart_data['lagna']['sign']!r}")
    if not chart_data["dashas"].get("timeline"):
        raise CalculationError("Dasha timeline is empty.")
    sav_total = chart_data["ashtakavarga"].get("total_bindus")
    if sav_total != 337:
        raise CalculationError(f"SAV bindu invariant violated: total={sav_total} (expected 337).")


def calculate_vedic_chart(dob_str: str, time_str: str, lat: float, lon: float, timezone_str: str,
                          query_date_str: str = None, ephe_path: str = ''):
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
    ephe_path : str, optional  Path to Swiss Ephemeris data files. Defaults to '' (bundled).

    Returns
    -------
    dict: Full chart data including planets, nakshatra, dasha, yogas, panchang.

    Notes
    -----
    Thread-safe: the Swiss Ephemeris section runs under a process-wide lock.
    Direct callers bypassing dashaflow.cast_chart should still pass valid
    inputs — invalid dates/timezones raise InvalidInputError (a ValueError).
    Swiss backend failures raise EphemerisError; implausible outputs raise
    CalculationError via the output-contract gate.
    """
    started = time.perf_counter()
    logger.debug("cast chart start dob=%s tz=%s", dob_str, timezone_str)
    with _SWE_LOCK:
        _configure_swiss_ephemeris(ephe_path)
        jd, local_dt = _to_jd(dob_str, time_str, timezone_str)
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

        try:
            ayanamsha_val = swe.get_ayanamsa_ut(jd)
        except Exception as exc:
            raise EphemerisError(f"Ephemeris backend failed (ayanamsha): {exc}") from exc

        # --- Ascendant (Lagna) ---
        try:
            cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)
        except Exception as exc:
            raise EphemerisError(f"Could not compute houses for lat={lat}, lon={lon}: {exc}") from exc
        asc_lon = ascmc[0]
        asc_sign, asc_deg, asc_sign_idx = get_sign_and_degree(asc_lon)
        asc_nak = get_nakshatra(asc_lon)

        # --- Planetary positions (shared helper; Ketu synthesized inside) ---
        try:
            raw_planets, sun_lon = _compute_raw_planets(jd, flags)
        except Exception as exc:
            raise EphemerisError(f"Ephemeris backend failed (planets): {exc}") from exc

    # --- Build enriched planet data (shared helper; vargas table-driven) ---
    planets_output, planets_for_yoga = _enrich_planets(raw_planets, asc_sign_idx, sun_lon)

    # --- Dasha ---
    moon_lon = raw_planets["Moon"]["lon"]
    birth_dt_naive = local_dt.replace(tzinfo=None)

    if query_date_str:
        try:
            query_dt = datetime.datetime.strptime(query_date_str, "%Y-%m-%d")
        except ValueError:
            raise InvalidInputError(f"Invalid query_date '{query_date_str}'. Expected YYYY-MM-DD.") from None
    else:
        logger.debug("query_date omitted; defaulting to today (non-deterministic across days)")
        query_dt = datetime.datetime.now()

    dasha_data = calculate_dashas(moon_lon, birth_dt_naive, query_dt)

    # --- Yogas ---
    yogas = detect_yogas(planets_for_yoga, asc_sign)

    # --- Panchang ---
    # calculate_panchang touches Swiss global state (set_topo/rise_trans), so
    # it runs under the same lock as the rest of the ephemeris section.
    with _SWE_LOCK:
        panchang_data = calculate_panchang(jd, sun_lon, moon_lon, lat, lon)

    # --- Ashtakavarga ---
    sav_planets = {name: rp["sign_idx"] for name, rp in raw_planets.items() if name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]}
    ashtakavarga_data = calculate_ashtakavarga(sav_planets, asc_sign_idx)

    # --- Assemble output ---
    jaimini_karakas = calculate_jaimini_karakas(planets_output)

    birth_year = int(dob_str[:4])
    accuracy = _ephemeris_accuracy(birth_year, ephe_path)
    if accuracy.startswith("reduced"):
        logger.warning("dob year %d outside %s with bundled ephemeris: %s",
                       birth_year, list(_FULL_ACCURACY_RANGE), accuracy)

    chart_data = {
        "metadata": {
            "dob": dob_str,
            "time": time_str,
            "coordinates": {"lat": lat, "lon": lon},
            "timezone": timezone_str,
            "ayanamsha": "Lahiri",
            "ayanamsha_degrees": round(ayanamsha_val, 4),
            "query_date": query_dt.strftime("%Y-%m-%d"),
            "dashaflow_version": __version__,
            "swe_version": swe.version,
            "ephemeris": ephe_path or "bundled",
            "ephemeris_accuracy": accuracy,
            "computed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "panchang": panchang_data,
        "lagna": {
            "sign": asc_sign,
            "degree": asc_deg,
            "nakshatra": asc_nak["name"],
            "pada": asc_nak["pada"],
            **calculate_all_vargas(asc_lon),
        },
        "planets": planets_output,
        "dashas": dasha_data,
        "yogas": yogas,
        "ashtakavarga": ashtakavarga_data,
        "jaimini_karakas": jaimini_karakas,
        "shadbala": calculate_shadbala(planets_output, raw_planets, is_day_birth=((asc_lon - sun_lon + 360) % 360) < 180),
        "bhava_chalit": calculate_bhava_chalit(asc_lon, raw_planets),
        "avasthas": calculate_avasthas(planets_output, raw_planets),
        "kaal_sarpa": detect_kaal_sarpa(raw_planets),
        "graha_yuddha": detect_graha_yuddha(raw_planets),
        "gandanta": detect_gandanta(raw_planets, asc_lon),
        "arudha_padas": calculate_arudha_padas(asc_sign, planets_output),
        "upapada": calculate_upapada(asc_sign, planets_output),
        "karakamsha": calculate_karakamsha(jaimini_karakas, planets_output, asc_sign),
    }

    _validate_chart_contract(chart_data)
    logger.debug("cast chart done lagna=%s maha=%s elapsed=%.3fs",
                 asc_sign,
                 (dasha_data.get("maha") or {}).get("planet"),
                 time.perf_counter() - started)
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

    Thread-safe: runs under the same process-wide Swiss Ephemeris lock as
    chart calculation. Invalid inputs raise InvalidInputError (a ValueError).
    """
    started = time.perf_counter()
    logger.debug("transit start date=%s", transit_date_str)
    # Transit at noon on the given date
    try:
        dt = datetime.datetime.strptime(transit_date_str, "%Y-%m-%d")
    except ValueError:
        raise InvalidInputError(f"Invalid transit_date '{transit_date_str}'. Expected YYYY-MM-DD.") from None
    try:
        local_tz = pytz.timezone(timezone_str)
    except Exception:
        raise InvalidInputError(f"Unknown timezone '{timezone_str}'. Use IANA format.") from None
    try:
        # Noon is DST-safe in almost all zones, but date-line skips (e.g.
        # Samoa 2011-12-30) can remove any local time — stay in the taxonomy.
        # is_dst=None: raise on gaps rather than silently shifting the instant.
        local_noon = local_tz.localize(dt.replace(hour=12), is_dst=None)
    except Exception as exc:
        raise InvalidInputError(f"Unrepresentable local noon '{transit_date_str}' in '{timezone_str}': {exc}") from exc
    utc_noon = local_noon.astimezone(pytz.utc)

    try:
        natal_lagna_sign = natal_chart["lagna"]["sign"]
        natal_lagna_idx = ZODIAC_SIGNS.index(natal_lagna_sign)
        natal_moon_sign = natal_chart["planets"]["Moon"]["sign"]
        natal_moon_idx = ZODIAC_SIGNS.index(natal_moon_sign)
    except (KeyError, ValueError, AttributeError, TypeError) as exc:
        raise InvalidInputError(f"Invalid natal_chart structure: {exc}") from exc

    with _SWE_LOCK:
        _configure_swiss_ephemeris('')
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        jd = swe.julday(utc_noon.year, utc_noon.month, utc_noon.day,
                         utc_noon.hour + utc_noon.minute / 60.0)

        transit_planets = {}
        rahu_lon = rahu_speed = None

        for name, planet_id in PLANETS.items():
            try:
                res, _ = swe.calc_ut(jd, planet_id, flags)
            except Exception as exc:
                raise EphemerisError(f"Ephemeris backend failed (transit {name}): {exc}") from exc
            planet_lon = res[0]
            speed = res[3]
            sign, deg, sign_idx = get_sign_and_degree(planet_lon)

            if name in ("Rahu", "Ketu"):
                is_retro = True
            elif name in ("Sun", "Moon"):
                is_retro = False
            else:
                is_retro = speed < 0

            if name == "Rahu":
                rahu_lon, rahu_speed = planet_lon, speed

            house_from_lagna = _house_from_lagna(sign_idx, natal_lagna_idx)
            house_from_moon = _house_from_lagna(sign_idx, natal_moon_idx)

            transit_planets[name] = {
                "sign": sign,
                "degree": deg,
                "is_retrograde": is_retro,
                "nakshatra": get_nakshatra(planet_lon)["name"],
                "house_from_lagna": house_from_lagna,
                "house_from_moon": house_from_moon,
                "sav_points": natal_chart.get("ashtakavarga", {}).get("sarvashtakavarga", {}).get(sign, 0),
            }

        # Ketu is always opposite Rahu — reuse the same synthesis as natal charts.
        ketu_raw = _synthesize_ketu({"lon": rahu_lon, "speed": rahu_speed})
        k_sign, k_deg, k_sign_idx = ketu_raw["sign"], ketu_raw["degree"], ketu_raw["sign_idx"]
        ketu_lon = ketu_raw["lon"]
        transit_planets["Ketu"] = {
            "sign": k_sign,
            "degree": k_deg,
            "is_retrograde": True,
            "nakshatra": get_nakshatra(ketu_lon)["name"],
            "house_from_lagna": _house_from_lagna(k_sign_idx, natal_lagna_idx),
            "house_from_moon": _house_from_lagna(k_sign_idx, natal_moon_idx),
            "sav_points": natal_chart.get("ashtakavarga", {}).get("sarvashtakavarga", {}).get(k_sign, 0)
        }

    logger.debug("transit done elapsed=%.3fs", time.perf_counter() - started)

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


if __name__ == "__main__":  # pragma: no cover - manual demo only
    demo = calculate_vedic_chart(
        dob_str="1990-04-15",
        time_str="14:30",
        lat=28.6139,
        lon=77.2090,
        timezone_str="Asia/Kolkata",
    )
    print(f"Lagna: {demo['lagna']['sign']} | Moon: {demo['planets']['Moon']['nakshatra']} | "
          f"Maha: {demo['dashas']['maha']['planet'] if demo['dashas']['maha'] else None}")
