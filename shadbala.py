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

from constants import (
    ZODIAC_SIGNS, EXALTATION, DEBILITATION, OWN_SIGNS,
    MOOLTRIKONA, NATURAL_FRIENDS, NATURAL_ENEMIES, DIGBALA_HOUSES
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


def _saptavargaja_bala(planet_name, dignity):
    """
    Strength based on dignity status in the rasi chart.
    Exalted=30, Mooltrikona=22.5, Own=20, Friend=15, Neutral=10, Enemy=5, Debilitated=2
    (Simplified: using D1 only instead of full 7 vargas)
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
    return dignity_scores.get(dignity, 10.0)


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


def _sthana_bala(planet_name, planet_lon, dignity, sign_idx, house, degree):
    uchcha = _uchcha_bala(planet_name, planet_lon)
    saptavarga = _saptavargaja_bala(planet_name, dignity)
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

def _kala_bala(planet_name, is_day_birth=True):
    """
    Simplified Kala Bala.
    Day-born: Sun, Jupiter, Venus gain strength.
    Night-born: Moon, Mars, Saturn gain strength.
    Mercury always gets moderate strength (day or night).
    """
    day_planets = ["Sun", "Jupiter", "Venus"]
    night_planets = ["Moon", "Mars", "Saturn"]

    if planet_name == "Mercury":
        return 30.0  # Mercury is always moderate
    if is_day_birth and planet_name in day_planets:
        return 60.0
    if not is_day_birth and planet_name in night_planets:
        return 60.0
    return 0.0


# ============================================================
# 4. CHESTA BALA (Motional Strength)
# ============================================================

def _chesta_bala(planet_name, speed, is_retrograde):
    """
    Retrograde planets get high Chesta Bala (60).
    Direct fast planets get moderate (30).
    Sun and Moon always get 30 (they don't retrograde).
    """
    if planet_name in ("Sun", "Moon"):
        return 30.0
    if planet_name in ("Rahu", "Ketu"):
        return 0.0
    if is_retrograde:
        return 60.0
    # Direct: use speed as a rough proxy (faster = more Chesta)
    return 30.0


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

def _drik_bala(planet_name, house, planets_data):
    """
    Simplified: benefics (Jupiter, Venus, Mercury, Moon) aspecting
    add strength; malefics (Saturn, Mars, Sun, Rahu, Ketu) aspecting reduce.
    """
    benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
    malefics = ["Saturn", "Mars", "Sun", "Rahu", "Ketu"]

    score = 0.0
    for name, data in planets_data.items():
        if name == planet_name:
            continue
        # Check if this planet aspects the target planet's sign
        if "aspects" in data:
            target_sign = planets_data[planet_name]["sign"]
            if target_sign in data["aspects"]:
                if name in benefics:
                    score += 10.0
                elif name in malefics:
                    score -= 10.0

    # Clamp to [0, 60]
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

    for planet_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        if planet_name not in planets_data or planet_name not in raw_planets:
            continue

        pd = planets_data[planet_name]
        rp = raw_planets[planet_name]

        sthana = _sthana_bala(planet_name, rp["lon"], pd["dignity"], rp["sign_idx"], pd["house"], pd["degree"])
        dig = _dig_bala(planet_name, pd["house"])
        kala = _kala_bala(planet_name, is_day_birth)
        chesta = _chesta_bala(planet_name, rp["speed"], pd["is_retrograde"])
        naisargika = NAISARGIKA_BALA.get(planet_name, 0.0)
        drik = _drik_bala(planet_name, pd["house"], planets_data)

        total_shashtiamshas = sthana["total"] + dig + kala + chesta + naisargika + drik
        total_rupas = round(total_shashtiamshas / 60.0, 2)
        required = REQUIRED_SHADBALA.get(planet_name, 5.0)
        is_strong = total_rupas >= required

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
        }

    return result
