from .constants import DUAL_LORD_PAIRS, RASHI_GUNAKAR, TRIKONA_GROUPS, ZODIAC_SIGNS

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

def calculate_ashtakavarga(planets_in_signs: dict, ascendant_sign_idx: int) -> dict:
    """
    Calculates Sarvashtakavarga (SAV) and Bhinnashtakavarga (BAV).
    planets_in_signs dict maps "Sun", "Moon", etc. to their 0-11 sign index.

    Bindus only (no Shodhana/reduction applied).

    Returns a dict with 'sarvashtakavarga' (list of 12 ints mapping to ZODIAC_SIGNS)
    and 'bhinnashtakavarga' mapping each planet to their 12-sign array.
    """
    if not isinstance(ascendant_sign_idx, int) or not 0 <= ascendant_sign_idx <= 11:
        raise ValueError(f"Invalid ascendant_sign_idx '{ascendant_sign_idx}'. Expected 0-11.")
    for _p, _idx in planets_in_signs.items():
        if not isinstance(_idx, int) or not 0 <= _idx <= 11:
            raise ValueError(f"Invalid sign index for '{_p}': '{_idx}'. Expected 0-11.")
    # Initialize all BAV arrays with 0
    bav = {p: [0]*12 for p in ASHTAKAVARGA_TABLES.keys()}
    sav = [0]*12

    # Extend planets dict with Ascendant for calculation
    positions = dict(planets_in_signs)
    positions["Ascendant"] = ascendant_sign_idx

    for target_planet, contributions in ASHTAKAVARGA_TABLES.items():
        for source_point, houses_list in contributions.items():
            try:
                source_idx = positions[source_point]
            except KeyError:
                raise ValueError(f"Missing '{source_point}' position for Ashtakavarga.") from None
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

    # Prashtarashtakavarga (expanded scatter chart)
    # For each target planet, shows which source contributed bindus to which sign
    prashtara = {}
    for target_planet, contributions in ASHTAKAVARGA_TABLES.items():
        prashtara[target_planet] = {}
        for source_point, houses_list in contributions.items():
            try:
                source_idx = positions[source_point]
            except KeyError:
                raise ValueError(f"Missing '{source_point}' position for Ashtakavarga.") from None
            row = [0] * 12
            for h in houses_list:
                target_sign_idx = (source_idx + (h - 1)) % 12
                row[target_sign_idx] = 1
            prashtara[target_planet][source_point] = {ZODIAC_SIGNS[i]: row[i] for i in range(12)}

    return {
        "sarvashtakavarga": sav_dict,
        "bhinnashtakavarga": bav_dict,
        "prashtarashtakavarga": prashtara,
        "total_bindus": sum(sav) # Should be 337
    }


def trikona_shodhana(bav_12: list) -> list:
    """
    Trikona Shodhana (I Reduction) on one 12-sign BAV array.

    Per elemental trikona: all-different → subtract the minimum from all
    three; one zero → no reduction; two zeros → all zero; all equal → all zero.
    """
    out = list(bav_12)
    for a, b, c in TRIKONA_GROUPS:
        vals = (out[a], out[b], out[c])
        zeros = sum(1 for v in vals if v == 0)
        if zeros == 1:
            continue  # Rule (b): no reduction
        if zeros == 2:
            out[a] = out[b] = out[c] = 0  # Rule (c)
        elif vals[0] == vals[1] == vals[2]:
            out[a] = out[b] = out[c] = 0  # Rule (d)
        else:
            m = min(vals)  # Rule (a)
            out[a] -= m
            out[b] -= m
            out[c] -= m
    return out


def ekadhipatya_shodhana(bav_12: list, occupied: set) -> list:
    """
    Ekadhipatya Shodhana (II Reduction) on a Trikona-reduced BAV array.

    Applies to dual-owned sign pairs only (Sun/Moon exempt). Occupancy =
    physical presence of a planet in the birth chart.
    I(a) both occupied → none; I(b) either zero → none;
    II(a) occupied > unoccupied → unoccupied eliminated;
    II(b) occupied < unoccupied → unoccupied set to occupied value;
    II(c) equal → unoccupied eliminated;
    III(a) both empty + equal → both zero;
    III(b) both empty + unequal → both set to the smaller.
    """
    out = list(bav_12)
    for (s1, s2), _lord in DUAL_LORD_PAIRS:
        v1, v2 = out[s1], out[s2]
        if v1 == 0 or v2 == 0:
            continue  # I(b): no reduction
        o1, o2 = (s1 in occupied), (s2 in occupied)
        if o1 and o2:
            continue  # I(a): no reduction
        if o1 and not o2:
            occ, unocc = s1, s2
        elif o2 and not o1:
            occ, unocc = s2, s1
        else:
            # III: both empty — equal → both zero, else both = smaller.
            if v1 == v2:
                out[s1] = out[s2] = 0  # III(a)
            else:
                m = min(v1, v2)
                out[s1] = out[s2] = m  # III(b)
            continue
        # II: one occupied — compare with the unoccupied sign.
        if out[occ] > out[unocc]:
            out[unocc] = 0  # II(a)
        elif out[occ] < out[unocc]:
            out[unocc] = out[occ]  # II(b)
        else:
            out[unocc] = 0  # II(c)
    return out


def calculate_sodhita_ashtakavarga(planets_in_signs: dict, ascendant_sign_idx: int,
                                   occupied_signs: set = None) -> dict:
    """
    Sodhita (reduced) Ashtakavarga: Trikona then Ekadhipatya Shodhana
    per BAV, plus Sodhya Pinda per planet.

    Parameters
    ----------
    planets_in_signs : dict — {planet: 0-11 sign_idx} (7 grahas).
    ascendant_sign_idx : int — Lagna sign 0-11.
    occupied_signs : set, optional — birth-chart occupied sign indices
        (defaults to the 7 planets' own signs; Rahu/Ketu excluded).

    Returns
    -------
    dict with sodhita BAVs, sodhita SAV (sign→bindus), reduced total,
    and Sodhya Pinda per planet (Σ shodhita bindus × Rashi Gunakar).
    """
    base = calculate_ashtakavarga(planets_in_signs, ascendant_sign_idx)
    if occupied_signs is None:
        occupied_signs = {planets_in_signs[p] for p in
                          ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                          if p in planets_in_signs}

    sodhita_bav = {}
    for planet, sign_map in base["bhinnashtakavarga"].items():
        arr = [sign_map[ZODIAC_SIGNS[i]] for i in range(12)]
        arr = ekadhipatya_shodhana(trikona_shodhana(arr), occupied_signs)
        sodhita_bav[planet] = {ZODIAC_SIGNS[i]: arr[i] for i in range(12)}

    sodhita_sav = {sign: sum(sodhita_bav[p][sign] for p in sodhita_bav) for sign in ZODIAC_SIGNS}
    sodhya_pinda = {}
    for planet, sign_map in sodhita_bav.items():
        sodhya_pinda[planet] = sum(sign_map[sign] * RASHI_GUNAKAR[sign] for sign in ZODIAC_SIGNS)

    return {
        "sodhita_bhinnashtakavarga": sodhita_bav,
        "sodhita_sarvashtakavarga": sodhita_sav,
        "sodhita_total": sum(sodhita_sav.values()),
        "sodhya_pinda": sodhya_pinda,
    }
