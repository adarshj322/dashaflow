"""
Shadbala — Six-fold Planetary Strength System (BPHS)
Calculates a numerical strength score for each planet based on:
1. Sthana Bala (Positional Strength) — Uchcha, Saptavargaja, Ojayugmarasyamsha, Kendra, Drekkana
2. Dig Bala (Directional Strength) — Based on house position
3. Kala Bala (Temporal Strength) — Day/night birth, hora lord, etc. (simplified)
4. Chesta Bala (Motional Strength) — Based on speed/retrograde
5. Naisargika Bala (Natural Strength) — Fixed hierarchy Sun > Moon > Venus > Jupiter > Mercury > Mars > Saturn
6. Drik Bala (Aspectual Strength) — Based on aspects received (simplified)

All values are in Shashtiamshas (60ths of a Rupa). 1 Rupa = 60 Shashtiamshas.
"""

from .constants import (
    ZODIAC_SIGNS, EXALTATION, DEBILITATION, OWN_SIGNS,
    MOOLTRIKONA, NATURAL_FRIENDS, NATURAL_ENEMIES, NATURAL_NEUTRALS,
    DIGBALA_HOUSES, SIGN_LORDS
)
import math


# ============================================================
# 1. STHANA BALA (Positional Strength)
# ============================================================

def _uchcha_bala(planet_name, planet_lon):
    """
    Exaltation strength. Max 60 Shashtiamshas at exact exaltation degree,
    0 at exact debilitation degree. Linear interpolation.
    """
    if planet_name not in EXALTATION:
        return 0.0

    exalt_sign, exalt_deg = EXALTATION[planet_name]
    exalt_sign_idx = ZODIAC_SIGNS.index(exalt_sign)
    exalt_lon = exalt_sign_idx * 30 + exalt_deg

    # Angular distance from exaltation point
    diff = abs(planet_lon - exalt_lon)
    if diff > 180:
        diff = 360 - diff

    # Max strength at 0 diff (exalted), min at 180 (debilitated)
    bala = (180 - diff) / 180.0 * 60.0
    return round(bala, 2)


def _varga_dignity(planet_name, varga_sign):
    """
    Determine a planet's dignity in a given varga chart sign.
    Returns a score: exalted=30, mooltrikona=22.5, own=20, friend=15, neutral=10, enemy=5, debilitated=2.
    """
    if not varga_sign or planet_name in ("Rahu", "Ketu"):
        return 10.0
    # Exaltation check
    if planet_name in EXALTATION and EXALTATION[planet_name][0] == varga_sign:
        return 30.0
    # Debilitation check
    if planet_name in DEBILITATION and DEBILITATION[planet_name][0] == varga_sign:
        return 2.0
    # Mooltrikona check
    if planet_name in MOOLTRIKONA and MOOLTRIKONA[planet_name][0] == varga_sign:
        return 22.5
    # Own sign check
    if planet_name in OWN_SIGNS and varga_sign in OWN_SIGNS[planet_name]:
        return 20.0
    # Relationship with sign lord
    sign_lord = SIGN_LORDS.get(varga_sign)
    if sign_lord and sign_lord != planet_name:
        if planet_name in NATURAL_FRIENDS and sign_lord in NATURAL_FRIENDS[planet_name]:
            return 15.0
        if planet_name in NATURAL_ENEMIES and sign_lord in NATURAL_ENEMIES[planet_name]:
            return 5.0
    return 10.0


def _saptavargaja_bala(planet_name, dignity, planet_data=None):
    """
    Strength based on dignity in the Saptavarga (7 divisional charts):
    D1 (Rasi), D2 (Hora), D3 (Drekkana), D7 (Saptamsha),
    D9 (Navamsha), D12 (Dwadashamsha), D30 (Trimshamsha).
    Each varga contributes up to 30 points; total is averaged.
    """
    dignity_scores = {
        "exalted": 30.0,
        "mooltrikona": 22.5,
        "own_sign": 20.0,
        "friend": 15.0,
        "neutral": 10.0,
        "enemy": 5.0,
        "debilitated": 2.0,
    }
    d1_score = dignity_scores.get(dignity, 10.0)

    if not planet_data:
        return d1_score

    varga_keys = ["d2_sign", "d3_sign", "d7_sign", "d9_sign", "d12_sign", "d30_sign"]
    scores = [d1_score]
    for key in varga_keys:
        varga_sign = planet_data.get(key)
        scores.append(_varga_dignity(planet_name, varga_sign))

    return round(sum(scores) / len(scores), 2)


def _ojayugmarasyamsha_bala(planet_name, sign_idx):
    """
    Strength from odd/even sign placement.
    Sun, Mars, Jupiter, Saturn gain strength in odd signs.
    Moon, Venus, Mercury (and Rahu/Ketu) gain in even signs.
    """
    is_odd_sign = (sign_idx % 2 == 0)  # Aries=0 is odd (index 0)
    odd_planets = ["Sun", "Mars", "Jupiter", "Saturn"]
    if planet_name in odd_planets:
        return 15.0 if is_odd_sign else 0.0
    else:
        return 15.0 if not is_odd_sign else 0.0


def _kendra_bala(house):
    """
    Planets in Kendras (1,4,7,10) get 60, Panapara (2,5,8,11) get 30,
    Apoklima (3,6,9,12) get 15.
    """
    if house in [1, 4, 7, 10]:
        return 60.0
    elif house in [2, 5, 8, 11]:
        return 30.0
    else:
        return 15.0


def _drekkana_bala(planet_name, degree_in_sign):
    """
    Male planets (Sun, Mars, Jupiter) strong in 1st drekkana (0-10°),
    Neutral planets (Mercury, Saturn) in 2nd drekkana (10-20°),
    Female planets (Moon, Venus) in 3rd drekkana (20-30°).
    """
    if degree_in_sign < 10:
        drekkana = 1
    elif degree_in_sign < 20:
        drekkana = 2
    else:
        drekkana = 3

    male = ["Sun", "Mars", "Jupiter"]
    female = ["Moon", "Venus"]

    if planet_name in male and drekkana == 1:
        return 15.0
    elif planet_name in female and drekkana == 3:
        return 15.0
    elif planet_name not in male and planet_name not in female and drekkana == 2:
        return 15.0
    return 0.0


def _sthana_bala(planet_name, planet_lon, dignity, sign_idx, house, degree, planet_data=None):
    uchcha = _uchcha_bala(planet_name, planet_lon)
    saptavarga = _saptavargaja_bala(planet_name, dignity, planet_data)
    ojayugma = _ojayugmarasyamsha_bala(planet_name, sign_idx)
    kendra = _kendra_bala(house)
    drekkana = _drekkana_bala(planet_name, degree)
    total = uchcha + saptavarga + ojayugma + kendra + drekkana
    return {
        "uchcha": uchcha,
        "saptavargaja": saptavarga,
        "ojayugmarasyamsha": ojayugma,
        "kendra": kendra,
        "drekkana": drekkana,
        "total": round(total, 2)
    }


# ============================================================
# 2. DIG BALA (Directional Strength)
# ============================================================

def _dig_bala(planet_name, house):
    """
    Max 60 when planet is in its Digbala house, 0 when opposite.
    Linear interpolation based on house distance.
    """
    if planet_name not in DIGBALA_HOUSES:
        return 0.0

    ideal_house = DIGBALA_HOUSES[planet_name]
    # House distance (1-indexed, circular)
    dist = abs(house - ideal_house)
    if dist > 6:
        dist = 12 - dist
    # Max at 0 distance, 0 at 6 houses away
    bala = (6 - dist) / 6.0 * 60.0
    return round(bala, 2)


# ============================================================
# 3. KALA BALA (Temporal Strength) — Simplified
# ============================================================

def _kala_bala(planet_name, is_day_birth=True, moon_lon=None, sun_lon=None):
    """
    Kala Bala with three sub-components:
    1. Natonnata Bala (day/night strength)
    2. Paksha Bala (lunar phase strength)
    3. Ayana Bala (Sun's declination / seasonal strength)
    """
    # 1. Natonnata Bala (day/night)
    day_planets = ["Sun", "Jupiter", "Venus"]
    night_planets = ["Moon", "Mars", "Saturn"]
    if planet_name == "Mercury":
        natonnata = 30.0
    elif is_day_birth and planet_name in day_planets:
        natonnata = 60.0
    elif not is_day_birth and planet_name in night_planets:
        natonnata = 60.0
    else:
        natonnata = 0.0

    # 2. Paksha Bala (Moon phase — benefics strong in Shukla Paksha, malefics in Krishna)
    paksha = 0.0
    if moon_lon is not None and sun_lon is not None:
        tithi_angle = (moon_lon - sun_lon) % 360
        is_shukla = tithi_angle < 180
        # Strength proportional to how close to Full/New Moon
        if is_shukla:
            phase_ratio = tithi_angle / 180.0
        else:
            phase_ratio = (360 - tithi_angle) / 180.0
        benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
        if planet_name in benefics:
            paksha = phase_ratio * 60.0  # benefics strong near Full Moon
        else:
            paksha = (1 - phase_ratio) * 60.0  # malefics strong near New Moon

    # 3. Ayana Bala (seasonal — based on Sun's longitude)
    ayana = 0.0
    if sun_lon is not None:
        # Sun 0-180° = Uttarayana (northern), 180-360° = Dakshinayana (southern)
        # Benefics strong in Uttarayana, malefics in Dakshinayana
        sun_norm = sun_lon % 360
        benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
        if sun_norm < 180:
            ratio = (180 - abs(sun_norm - 90)) / 180.0
        else:
            ratio = (180 - abs(sun_norm - 270)) / 180.0
        if planet_name in benefics:
            ayana = ratio * 30.0 if sun_norm < 180 else (1 - ratio) * 30.0
        else:
            ayana = (1 - ratio) * 30.0 if sun_norm < 180 else ratio * 30.0

    return round(natonnata + paksha + ayana, 2)


# ============================================================
# 4. CHESTA BALA (Motional Strength)
# ============================================================

# Average daily speeds in degrees (approximate)
_AVG_SPEEDS = {
    "Mars": 0.524,
    "Mercury": 1.383,
    "Jupiter": 0.083,
    "Venus": 1.200,
    "Saturn": 0.034,
}


def _chesta_bala(planet_name, speed, is_retrograde):
    """
    Motional strength based on actual speed.
    Retrograde=60, Stationary(very slow)=45, Direct uses speed ratio.
    Sun=Chesta from longitude, Moon=Paksha-based (set in Kala Bala).
    """
    if planet_name in ("Sun", "Moon"):
        return 30.0
    if planet_name in ("Rahu", "Ketu"):
        return 0.0
    if is_retrograde:
        return 60.0
    avg = _AVG_SPEEDS.get(planet_name, 1.0)
    abs_speed = abs(speed)
    if abs_speed < avg * 0.1:
        return 45.0  # near-stationary
    # Scale linearly: 0 speed → 45, avg speed → 30, 2x avg → 15
    ratio = min(abs_speed / avg, 2.0)
    return round(60.0 - ratio * 15.0, 2)


# ============================================================
# 5. NAISARGIKA BALA (Natural Strength) — Fixed
# ============================================================

NAISARGIKA_BALA = {
    "Sun": 60.0,
    "Moon": 51.43,
    "Venus": 42.86,
    "Jupiter": 34.29,
    "Mercury": 25.71,
    "Mars": 17.14,
    "Saturn": 8.57,
}


# ============================================================
# 6. DRIK BALA (Aspectual Strength) — Simplified
# ============================================================

# BPHS partial aspect strengths (house distance → fraction)
_ASPECT_STRENGTH = {
    3: 0.25, 4: 0.75, 5: 0.50, 7: 1.00, 8: 0.75, 9: 0.50, 10: 0.25,
}
# Special full aspects override
_SPECIAL_ASPECTS = {
    "Mars": {4: 1.00, 8: 1.00},
    "Jupiter": {5: 1.00, 9: 1.00},
    "Saturn": {3: 1.00, 10: 1.00},
}


def _drik_bala(planet_name, house, planets_data):
    """
    Aspectual strength using BPHS weighted partial aspects.
    Benefics aspecting add strength; malefics reduce it.
    Aspect weight varies by house distance and special aspects.
    """
    benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
    malefics = ["Saturn", "Mars", "Sun", "Rahu", "Ketu"]

    target_sign_idx = ZODIAC_SIGNS.index(planets_data[planet_name]["sign"])
    score = 0.0

    for name, data in planets_data.items():
        if name == planet_name or name in ("Rahu", "Ketu"):
            continue
        aspector_sign_idx = ZODIAC_SIGNS.index(data["sign"])
        house_dist = ((target_sign_idx - aspector_sign_idx) % 12) + 1
        if house_dist == 1:
            continue  # conjunction, not aspect

        # Check if this planet aspects at this distance
        special = _SPECIAL_ASPECTS.get(name, {})
        strength = special.get(house_dist, _ASPECT_STRENGTH.get(house_dist, 0.0))
        if strength <= 0:
            continue

        if name in benefics:
            score += strength * 15.0
        elif name in malefics:
            score -= strength * 15.0

    # Normalize to [0, 60] range with 30 as midpoint
    return round(max(0.0, min(60.0, score + 30.0)), 2)


# ============================================================
# MAIN CALCULATOR
# ============================================================

# Minimum required Shadbala (in Rupas) per BPHS
REQUIRED_SHADBALA = {
    "Sun": 6.5,
    "Moon": 6.0,
    "Mars": 5.0,
    "Mercury": 7.0,
    "Jupiter": 6.5,
    "Venus": 5.5,
    "Saturn": 5.0,
}


def calculate_shadbala(planets_data: dict, raw_planets: dict, is_day_birth: bool = True):
    """
    Calculates the six-fold strength for all 7 planets.
    
    Parameters
    ----------
    planets_data : dict — The enriched 'planets' output from calculate_vedic_chart
    raw_planets : dict — The raw planet data with 'lon', 'sign_idx', 'speed'
    is_day_birth : bool — Whether birth occurred during daytime
    
    Returns
    -------
    dict: Shadbala breakdown for each planet with total in Shashtiamshas and Rupas.
    """
    result = {}

    # Extract Sun and Moon longitudes for Kala Bala sub-components
    sun_lon = raw_planets.get("Sun", {}).get("lon")
    moon_lon = raw_planets.get("Moon", {}).get("lon")

    for planet_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        if planet_name not in planets_data or planet_name not in raw_planets:
            continue

        pd = planets_data[planet_name]
        rp = raw_planets[planet_name]

        sthana = _sthana_bala(planet_name, rp["lon"], pd["dignity"], rp["sign_idx"], pd["house"], pd["degree"], pd)
        dig = _dig_bala(planet_name, pd["house"])
        kala = _kala_bala(planet_name, is_day_birth, moon_lon, sun_lon)
        chesta = _chesta_bala(planet_name, rp["speed"], pd["is_retrograde"])
        naisargika = NAISARGIKA_BALA.get(planet_name, 0.0)
        drik = _drik_bala(planet_name, pd["house"], planets_data)

        total_shashtiamshas = sthana["total"] + dig + kala + chesta + naisargika + drik
        total_rupas = round(total_shashtiamshas / 60.0, 2)
        required = REQUIRED_SHADBALA.get(planet_name, 5.0)
        is_strong = total_rupas >= required

        # Ishta Phala and Kashta Phala (BPHS)
        # Ishta = sqrt(Uchcha Bala * Chesta Bala)
        # Kashta = sqrt((60 - Uchcha Bala) * (60 - Chesta Bala))
        uchcha = sthana["uchcha"]
        ishta_phala = round(math.sqrt(max(0, uchcha * chesta)), 2)
        kashta_phala = round(math.sqrt(max(0, (60.0 - uchcha) * (60.0 - chesta))), 2)

        result[planet_name] = {
            "sthana_bala": sthana,
            "dig_bala": dig,
            "kala_bala": kala,
            "chesta_bala": chesta,
            "naisargika_bala": naisargika,
            "drik_bala": drik,
            "total_shashtiamshas": round(total_shashtiamshas, 2),
            "total_rupas": total_rupas,
            "required_rupas": required,
            "is_strong": is_strong,
            "strength_ratio": round(total_rupas / required, 2),
            "ishta_phala": ishta_phala,
            "kashta_phala": kashta_phala,
        }

    return result
