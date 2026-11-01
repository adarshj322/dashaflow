"""
Vimshopaka Bala — 20-point divisional strength (BPHS Shad-Varga scheme).

Each planet scores up to 20 points from dignity across six vargas with
fixed weights: D1 Rasi 6, D2 Hora 2, D3 Drekkana 4, D9 Navamsa 5,
D12 Dwadashamsa 2, D30 Trimshamsha 1.

Per-varga contribution = weight × (Varga Viswa / 20), where Varga Viswa
grades the planet's relationship with the varga sign lord:
own/exalted/mooltrikona 20, great friend 18, friend 15, neutral 10,
enemy 7, great enemy/debilitated 5 (floor convention).

Interpretation bands: <5 nil (incapable of auspicious results),
5-10 weak, 10-15 medium, 15-18 full, 18-20 extra.

Relationship grades come from Panchadha-Maitri via get_dignity() against
natal (D1) placements, so great_friend/great_enemy occur naturally.
Rahu/Ketu resolve through the same dignity path (documented school).
"""

from .dignity import get_dignity

# Shad-Varga scheme weights (sum to 20). D1 uses the "sign" key.
VIMSHOPAKA_WEIGHTS = {
    "sign": 6.0,      # D1 Rasi
    "d2_sign": 2.0,   # D2 Hora
    "d3_sign": 4.0,   # D3 Drekkana
    "d9_sign": 5.0,   # D9 Navamsa
    "d12_sign": 2.0,  # D12 Dwadashamsha
    "d30_sign": 1.0,  # D30 Trimshamsha
}

# Dignity → Varga Viswa (out of 20).
VISWA = {
    "exalted": 20.0,
    "mooltrikona": 20.0,
    "own_sign": 20.0,
    "great_friend": 18.0,
    "friend": 15.0,
    "neutral": 10.0,
    "enemy": 7.0,
    "great_enemy": 5.0,
    "debilitated": 5.0,
}

VIMSHOPAKA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def _band(total: float) -> str:
    """Strength band for a 0-20 Vimshopaka total."""
    if total < 5:
        return "nil"
    if total < 10:
        return "weak"
    if total < 15:
        return "medium"
    if total < 18:
        return "full"
    return "extra"


def calculate_vimshopaka(planets_data: dict, planets_in_signs: dict) -> dict:
    """
    Calculate Shad-Varga Vimshopaka Bala for the seven grahas.

    Parameters
    ----------
    planets_data : dict
        Enriched 'planets' output (needs 'sign' + d2/d3/d9/d12/d30 signs).
    planets_in_signs : dict
        {planet_name: D1 sign_idx} for Panchadha-Maitri grading.

    Returns
    -------
    dict per planet: {total_20, band, breakdown per varga}.
    """
    result = {}
    for name in VIMSHOPAKA_PLANETS:
        if name not in planets_data:
            continue
        pd = planets_data[name]
        breakdown = {}
        total = 0.0
        for key, weight in VIMSHOPAKA_WEIGHTS.items():
            varga_sign = pd.get(key, "") if key != "sign" else pd.get("sign", "")
            dignity = get_dignity(name, varga_sign, 15.0, planets_in_signs)
            viswa = VISWA.get(dignity, 10.0)
            contribution = round(weight * viswa / 20.0, 2)
            breakdown[key] = {
                "sign": varga_sign,
                "dignity": dignity,
                "viswa": viswa,
                "contribution": contribution,
            }
            total += contribution
        total = round(total, 2)
        result[name] = {
            "total_20": total,
            "band": _band(total),
            "breakdown": breakdown,
        }
    return result
