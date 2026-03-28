"""
Jaimini Karakas — Chara Karaka System
Based on BPHS Jaimini Sutras: The planet with the highest degree 
in its sign (excluding Rahu/Ketu) becomes the Atmakaraka (soul significator).
The 8-karaka scheme is used (includes Rahu as the 8th).
"""

from constants import ZODIAC_SIGNS

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
