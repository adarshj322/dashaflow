from constants import ZODIAC_SIGNS

# 1-indexed houses from the placement of the planet
ASHTAKAVARGA_TABLES = {
    "Sun": {
        "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon": [3, 6, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus": [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Ascendant": [3, 4, 6, 10, 11, 12]
    },
    "Moon": {
        "Sun": [3, 6, 7, 8, 10, 11],
        "Moon": [1, 3, 6, 7, 10, 11],
        "Mars": [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus": [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Ascendant": [3, 6, 10, 11]
    },
    "Mars": {
        "Sun": [3, 5, 6, 10, 11],
        "Moon": [3, 6, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus": [6, 8, 11, 12],
        "Saturn": [1, 4, 7, 8, 9, 10, 11],
        "Ascendant": [1, 3, 6, 10, 11]
    },
    "Mercury": {
        "Sun": [5, 6, 9, 11, 12],
        "Moon": [2, 4, 6, 8, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Ascendant": [1, 2, 4, 6, 8, 10, 11]
    },
    "Jupiter": {
        "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon": [2, 5, 7, 9, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus": [2, 5, 6, 9, 10, 11],
        "Saturn": [3, 5, 6, 12],
        "Ascendant": [1, 2, 4, 5, 6, 7, 9, 10, 11]
    },
    "Venus": {
        "Sun": [8, 11, 12],
        "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars": [3, 5, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn": [3, 4, 5, 8, 9, 10, 11],
        "Ascendant": [1, 2, 3, 4, 5, 8, 9, 11]
    },
    "Saturn": {
        "Sun": [1, 2, 4, 7, 8, 10, 11],
        "Moon": [3, 6, 11],
        "Mars": [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus": [6, 11, 12],
        "Saturn": [3, 5, 6, 11],
        "Ascendant": [1, 3, 4, 6, 10, 11]
    }
}

def calculate_ashtakavarga(planets_in_signs: dict, ascendant_sign_idx: int):
    """
    Calculates Sarvashtakavarga (SAV) and Bhinnashtakavarga (BAV).
    planets_in_signs dict maps "Sun", "Moon", etc. to their 0-11 sign index.
    
    Returns a dict with 'sarvashtakavarga' (list of 12 ints mapping to ZODIAC_SIGNS)
    and 'bhinnashtakavarga' mapping each planet to their 12-sign array.
    """
    # Initialize all BAV arrays with 0
    bav = {p: [0]*12 for p in ASHTAKAVARGA_TABLES.keys()}
    sav = [0]*12
    
    # Extend planets dict with Ascendant for calculation
    positions = planets_in_signs.copy()
    positions["Ascendant"] = ascendant_sign_idx
    
    for target_planet, contributions in ASHTAKAVARGA_TABLES.items():
        for source_point, houses_list in contributions.items():
            source_idx = positions[source_point]
            for h in houses_list:
                # h is 1-indexed house from the source planet.
                # So if source is at idx 0 (Aries) and h=1, target sign is 0 (Aries)
                target_sign_idx = (source_idx + (h - 1)) % 12
                bav[target_planet][target_sign_idx] += 1
                sav[target_sign_idx] += 1
                
    # Return as a dict mapped to Zodiac Sign names for easier LLM reading
    sav_dict = {ZODIAC_SIGNS[i]: sav[i] for i in range(12)}
    
    bav_dict = {}
    for p, arr in bav.items():
        bav_dict[p] = {ZODIAC_SIGNS[i]: arr[i] for i in range(12)}
        
    return {
        "sarvashtakavarga": sav_dict,
        "bhinnashtakavarga": bav_dict,
        "total_bindus": sum(sav) # Should be 337
    }
