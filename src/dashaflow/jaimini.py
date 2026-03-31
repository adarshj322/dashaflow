"""
Jaimini Karakas — Chara Karaka System
Based on BPHS Jaimini Sutras: The planet with the highest degree 
in its sign (excluding Rahu/Ketu) becomes the Atmakaraka (soul significator).
The 8-karaka scheme is used (includes Rahu as the 8th).
"""

from .constants import ZODIAC_SIGNS, SIGN_LORDS

KARAKA_NAMES = [
    "Atmakaraka",       # Soul, self (highest degree) — most important planet in chart
    "Amatyakaraka",     # Career/profession, minister
    "Bhratrikaraka",    # Siblings, courage
    "Matrikaraka",      # Mother, education, property
    "Putrakaraka",      # Children, creativity, intelligence
    "Gnatikaraka",      # Enemies, diseases, obstacles
    "Darakaraka",       # Spouse (lowest degree among 7 planets)
]

KARAKA_DESCRIPTIONS = {
    "Atmakaraka": "The King of the chart. Represents the soul's deepest desire and the primary life lesson. The house it sits in (Karakamsha in D9) reveals the soul's ultimate direction.",
    "Amatyakaraka": "The Minister. Represents career, profession, and the means through which one earns and contributes to society. Check its D10 position for career specifics.",
    "Bhratrikaraka": "Significator of siblings, courage, and personal initiative. Its strength shows the native's ability to take bold action.",
    "Matrikaraka": "Significator of mother, formal education, property, and emotional comfort.",
    "Putrakaraka": "Significator of children, intelligence, creativity, and past-life merit (Purva Punya). Check D7 for progeny details.",
    "Gnatikaraka": "Significator of enemies, diseases, and obstacles. Its Dasha can bring confrontations but also the strength to overcome them.",
    "Darakaraka": "Significator of spouse and marriage partner. The planet with the LOWEST degree becomes the Darakaraka. Its sign, dignity, and D9 position describe the spouse's nature.",
}

# Arudha Pada names for all 12 houses
ARUDHA_NAMES = {
    1: "Arudha Lagna (AL)",
    2: "Dhana Pada (A2)",
    3: "Vikrama Pada (A3)",
    4: "Sukha Pada (A4)",
    5: "Mantra Pada (A5)",
    6: "Roga Pada (A6)",
    7: "Dara Pada (A7)",
    8: "Mrithyu Pada (A8)",
    9: "Dharma Pada (A9)",
    10: "Karma Pada (A10)",
    11: "Labha Pada (A11)",
    12: "Upapada (UL)",
}


def calculate_jaimini_karakas(planets_data: dict):
    """
    Calculates the 7 Chara Karakas from the natal chart planet data.
    
    Parameters
    ----------
    planets_data : dict
        The 'planets' dict from calculate_vedic_chart output.
        Each planet entry must have 'degree' (0-30 within sign).
    
    Returns
    -------
    dict with karaka assignments and descriptions.
    """
    # Only the 7 visible planets participate (Rahu/Ketu excluded from standard 7-karaka scheme)
    eligible = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    
    # Build list of (planet_name, degree_in_sign)
    planet_degrees = []
    for name in eligible:
        if name in planets_data:
            deg = planets_data[name]["degree"]
            planet_degrees.append((name, deg))
    
    # Sort by degree DESCENDING — highest degree = Atmakaraka
    planet_degrees.sort(key=lambda x: x[1], reverse=True)
    
    karakas = {}
    for i, (planet_name, degree) in enumerate(planet_degrees):
        if i < len(KARAKA_NAMES):
            karaka_name = KARAKA_NAMES[i]
            karakas[karaka_name] = {
                "planet": planet_name,
                "degree": degree,
                "description": KARAKA_DESCRIPTIONS[karaka_name],
                "sign": planets_data[planet_name]["sign"],
                "house": planets_data[planet_name]["house"],
                "d9_sign": planets_data[planet_name].get("d9_sign", ""),
            }
    
    return karakas


def _sign_idx(sign_name):
    """Get index of a sign (0-11)."""
    return ZODIAC_SIGNS.index(sign_name)


def _house_count(from_idx, to_idx):
    """Count houses from one sign index to another (1-based)."""
    return ((to_idx - from_idx) % 12) + 1


def calculate_arudha_padas(lagna_sign, planets_data):
    """
    Calculate Arudha Padas for all 12 houses per Jaimini system.
    
    Arudha Pada of a house = count from house sign to its lord's placement,
    then count the same distance from the lord's sign.
    
    Exception: If the Arudha falls in the same sign as the house or the 7th from it,
    move it to the 10th sign from the house instead.
    
    Parameters
    ----------
    lagna_sign : str — Ascendant sign name
    planets_data : dict — planet data from calculate_vedic_chart
    
    Returns
    -------
    dict: {house_num: {"sign": str, "name": str, "sign_index": int}}
    """
    lagna_idx = _sign_idx(lagna_sign)
    
    # Build planet sign lookup
    planet_signs = {}
    for name, pd in planets_data.items():
        planet_signs[name] = _sign_idx(pd["sign"])
    
    arudha_padas = {}
    
    for house_num in range(1, 13):
        house_sign_idx = (lagna_idx + house_num - 1) % 12
        house_sign = ZODIAC_SIGNS[house_sign_idx]
        
        # Lord of this house
        lord = SIGN_LORDS[house_sign]
        
        if lord not in planet_signs:
            continue
        
        lord_sign_idx = planet_signs[lord]
        
        # Count from house sign to lord's sign
        distance = _house_count(house_sign_idx, lord_sign_idx)
        
        # Arudha = same distance counted from lord's sign
        arudha_idx = (lord_sign_idx + distance - 1) % 12
        
        # Exception rule: if arudha falls in the house itself or 7th from it
        seventh_from_house = (house_sign_idx + 6) % 12
        if arudha_idx == house_sign_idx or arudha_idx == seventh_from_house:
            # Move to 10th from the house
            arudha_idx = (house_sign_idx + 9) % 12
        
        arudha_padas[house_num] = {
            "sign": ZODIAC_SIGNS[arudha_idx],
            "sign_index": arudha_idx,
            "name": ARUDHA_NAMES.get(house_num, f"A{house_num}"),
        }
    
    return arudha_padas


def calculate_upapada(lagna_sign, planets_data):
    """
    Calculate Upapada Lagna (UL) — the Arudha of the 12th house.
    Critical for spouse analysis in Jaimini.
    
    The sign of the Upapada and planets in/aspecting it describe the spouse.
    The 2nd from Upapada shows longevity of marriage.
    
    Returns
    -------
    dict: {"sign": str, "sign_index": int, "lord": str, "second_from_ul": str}
    """
    arudha_padas = calculate_arudha_padas(lagna_sign, planets_data)
    
    ul = arudha_padas.get(12)
    if not ul:
        return None
    
    ul_idx = ul["sign_index"]
    second_idx = (ul_idx + 1) % 12
    
    return {
        "sign": ul["sign"],
        "sign_index": ul_idx,
        "lord": SIGN_LORDS[ul["sign"]],
        "second_from_ul": ZODIAC_SIGNS[second_idx],
        "description": f"Upapada in {ul['sign']} — spouse characteristics shaped by {SIGN_LORDS[ul['sign']]}. 2nd from UL ({ZODIAC_SIGNS[second_idx]}) indicates marriage longevity.",
    }


def calculate_karakamsha(karakas, planets_data, lagna_sign):
    """
    Calculate Karakamsha — Atmakaraka's sign in D9 (Navamsha).
    The Karakamsha sign becomes a reference lagna for soul-level analysis.
    
    Also computes the 12th from Karakamsha → Ishta Devata (personal deity).
    
    Parameters
    ----------
    karakas : dict — output from calculate_jaimini_karakas
    planets_data : dict — planets output with d9_sign
    lagna_sign : str — D1 ascendant sign
    
    Returns
    -------
    dict: Karakamsha analysis
    """
    ak = karakas.get("Atmakaraka")
    if not ak:
        return None
    
    ak_planet = ak["planet"]
    ak_d9_sign = ak.get("d9_sign", "")
    
    if not ak_d9_sign:
        return None
    
    ak_d9_idx = _sign_idx(ak_d9_sign)
    lagna_idx = _sign_idx(lagna_sign)
    
    # Karakamsha house from Lagna
    karakamsha_house = _house_count(lagna_idx, ak_d9_idx)
    
    # 12th from Karakamsha → Ishta Devata sign
    ishta_devata_sign_idx = (ak_d9_idx - 1) % 12
    ishta_devata_sign = ZODIAC_SIGNS[ishta_devata_sign_idx]
    ishta_devata_lord = SIGN_LORDS[ishta_devata_sign]
    
    # Check which planets occupy the Karakamsha sign in D9
    planets_in_karakamsha = []
    for name, pd in planets_data.items():
        if pd.get("d9_sign") == ak_d9_sign:
            planets_in_karakamsha.append(name)
    
    return {
        "atmakaraka": ak_planet,
        "karakamsha_sign": ak_d9_sign,
        "karakamsha_house_from_lagna": karakamsha_house,
        "planets_in_karakamsha": planets_in_karakamsha,
        "ishta_devata_sign": ishta_devata_sign,
        "ishta_devata_lord": ishta_devata_lord,
        "description": f"Atmakaraka {ak_planet} in D9 {ak_d9_sign} (house {karakamsha_house} from Lagna) — soul's deepest direction. Ishta Devata indicated by {ishta_devata_lord} ({ishta_devata_sign}).",
    }
