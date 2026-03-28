from constants import ZODIAC_SIGNS, SIGN_LORDS, EXALTATION, OWN_SIGNS


KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
BENEFICS = {"Jupiter", "Venus", "Mercury"}
MAHAPURUSHA_PLANETS = {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
MAHAPURUSHA_NAMES = {
    "Mars": "Ruchaka Yoga",
    "Mercury": "Bhadra Yoga",
    "Jupiter": "Hamsa Yoga",
    "Venus": "Malavya Yoga",
    "Saturn": "Shasha Yoga",
}

# Gandanta junctions: last nakshatra of water sign → first nakshatra of fire sign
# Water signs: Cancer(3), Scorpio(7), Pisces(11)  Fire signs: Leo(4), Sagittarius(8), Aries(0)
# Gandanta zones: last 3°20' of water sign + first 3°20' of fire sign
GANDANTA_JUNCTIONS = [
    (3, 4),   # Cancer → Leo
    (7, 8),   # Scorpio → Sagittarius
    (11, 0),  # Pisces → Aries
]
GANDANTA_ORB = 3.3333  # 3°20' = one pada


def _house_from(base_sign_idx, planet_sign_idx):
    return ((planet_sign_idx - base_sign_idx) % 12) + 1


def _sign_idx(sign_name):
    return ZODIAC_SIGNS.index(sign_name)


def _lord_of_house(lagna_sign_idx, house_num):
    sign_idx = (lagna_sign_idx + house_num - 1) % 12
    return SIGN_LORDS[ZODIAC_SIGNS[sign_idx]]


def _is_exalted_or_own(planet_name, sign):
    if planet_name in EXALTATION and EXALTATION[planet_name][0] == sign:
        return True
    if planet_name in OWN_SIGNS and sign in OWN_SIGNS[planet_name]:
        return True
    return False


def detect_yogas(planets, lagna_sign):
    """
    Detect key Vedic yogas from chart data.

    Parameters
    ----------
    planets : dict
        {planet_name: {"sign": str, "sign_idx": int, "house": int, "dignity": str, ...}}
    lagna_sign : str

    Returns
    -------
    list of dict: [{"name": str, "formed_by": list, "description": str}, ...]
    """
    yogas = []
    lagna_idx = _sign_idx(lagna_sign)

    moon_data = planets.get("Moon", {})
    moon_idx = moon_data.get("sign_idx", 0)

    # --- Pancha Mahapurusha Yogas ---
    for p in MAHAPURUSHA_PLANETS:
        pd = planets.get(p)
        if not pd:
            continue
        if pd.get("house") in KENDRA_HOUSES and _is_exalted_or_own(p, pd["sign"]):
            yogas.append({
                "name": MAHAPURUSHA_NAMES[p],
                "formed_by": [p],
                "description": f"{p} in own/exalted sign in house {pd['house']} from Lagna.",
            })

    # --- Gajakesari Yoga: Jupiter in kendra from Moon ---
    jup = planets.get("Jupiter")
    if jup and moon_data:
        house_from_moon = _house_from(moon_idx, jup["sign_idx"])
        if house_from_moon in KENDRA_HOUSES:
            yogas.append({
                "name": "Gajakesari Yoga",
                "formed_by": ["Jupiter", "Moon"],
                "description": f"Jupiter in house {house_from_moon} from Moon (kendra).",
            })

    # --- Budhaditya Yoga: Sun + Mercury in same sign ---
    sun_d = planets.get("Sun")
    mer_d = planets.get("Mercury")
    if sun_d and mer_d and sun_d["sign"] == mer_d["sign"]:
        if mer_d.get("dignity") != "debilitated" and not mer_d.get("is_combust"):
            yogas.append({
                "name": "Budhaditya Yoga",
                "formed_by": ["Sun", "Mercury"],
                "description": f"Sun and Mercury conjoined in {sun_d['sign']}.",
            })

    # --- Chandra-Mangal Yoga: Moon + Mars in same sign ---
    mars_d = planets.get("Mars")
    if moon_data and mars_d and moon_data["sign"] == mars_d["sign"]:
        yogas.append({
            "name": "Chandra-Mangal Yoga",
            "formed_by": ["Moon", "Mars"],
            "description": f"Moon and Mars conjoined in {moon_data['sign']}.",
        })

    # --- Kemadruma Yoga: No planet in 2nd or 12th from Moon ---
    if moon_data:
        sign_2nd = (moon_idx + 1) % 12
        sign_12th = (moon_idx - 1) % 12
        has_support = False
        for p_name, pd in planets.items():
            if p_name in ("Sun", "Moon", "Rahu", "Ketu"):
                continue
            if pd["sign_idx"] in (sign_2nd, sign_12th):
                has_support = True
                break
        if not has_support:
            yogas.append({
                "name": "Kemadruma Yoga",
                "formed_by": ["Moon"],
                "description": "No planet (except Sun/nodes) in 2nd or 12th from Moon.",
            })

    # --- Adhi Yoga: Benefics in 6th, 7th, 8th from Moon ---
    if moon_data:
        target_houses = {6, 7, 8}
        adhi_planets = []
        for p_name in ("Mercury", "Jupiter", "Venus"):
            pd = planets.get(p_name)
            if pd:
                h = _house_from(moon_idx, pd["sign_idx"])
                if h in target_houses:
                    adhi_planets.append(p_name)
        if len(adhi_planets) >= 2:
            yogas.append({
                "name": "Adhi Yoga",
                "formed_by": adhi_planets,
                "description": f"Benefics ({', '.join(adhi_planets)}) in 6/7/8 from Moon.",
            })

    # --- Raj Yoga: Lord of kendra + Lord of trikona conjoined ---
    kendra_lords = set()
    trikona_lords = set()
    for h in KENDRA_HOUSES:
        kendra_lords.add(_lord_of_house(lagna_idx, h))
    for h in TRIKONA_HOUSES:
        trikona_lords.add(_lord_of_house(lagna_idx, h))

    dual_lords = kendra_lords & trikona_lords
    for lord_name in dual_lords:
        pd = planets.get(lord_name)
        if pd and pd.get("house") in KENDRA_HOUSES | TRIKONA_HOUSES:
            yogas.append({
                "name": "Raj Yoga",
                "formed_by": [lord_name],
                "description": f"{lord_name} is lord of both kendra and trikona, placed in house {pd['house']}.",
            })

    pure_kendra = kendra_lords - dual_lords
    pure_trikona = trikona_lords - dual_lords
    for kl in pure_kendra:
        for tl in pure_trikona:
            kl_data = planets.get(kl)
            tl_data = planets.get(tl)
            if kl_data and tl_data and kl_data["sign"] == tl_data["sign"]:
                yogas.append({
                    "name": "Raj Yoga",
                    "formed_by": [kl, tl],
                    "description": f"Kendra lord {kl} conjoined with trikona lord {tl} in {kl_data['sign']}.",
                })

    # --- Viparita Raj Yoga: Lord of 6/8/12 in another dusthana ---
    dusthana_lords = {}
    for h in DUSTHANA_HOUSES:
        lord = _lord_of_house(lagna_idx, h)
        dusthana_lords[h] = lord

    for h, lord in dusthana_lords.items():
        pd = planets.get(lord)
        if pd and pd.get("house") in DUSTHANA_HOUSES and pd["house"] != h:
            yogas.append({
                "name": "Viparita Raj Yoga",
                "formed_by": [lord],
                "description": f"Lord of house {h} ({lord}) placed in house {pd['house']} (dusthana in dusthana).",
            })

    # --- Neecha Bhanga Raja Yoga ---
    for p_name, pd in planets.items():
        if pd.get("dignity") != "debilitated":
            continue
        sign = pd["sign"]
        cancellation = False
        cancel_reason = ""

        dispositor = SIGN_LORDS.get(sign)
        if dispositor:
            disp_data = planets.get(dispositor)
            if disp_data:
                if disp_data.get("house") in KENDRA_HOUSES:
                    cancellation = True
                    cancel_reason = f"Dispositor {dispositor} in kendra from Lagna."
                elif moon_data and _house_from(moon_idx, disp_data["sign_idx"]) in KENDRA_HOUSES:
                    cancellation = True
                    cancel_reason = f"Dispositor {dispositor} in kendra from Moon."

        if not cancellation and p_name in EXALTATION:
            exalt_sign = EXALTATION[p_name][0]
            exalt_lord = SIGN_LORDS.get(exalt_sign)
            if exalt_lord:
                el_data = planets.get(exalt_lord)
                if el_data:
                    if el_data.get("house") in KENDRA_HOUSES:
                        cancellation = True
                        cancel_reason = f"Lord of exaltation sign ({exalt_lord}) in kendra from Lagna."
                    elif moon_data and _house_from(moon_idx, el_data["sign_idx"]) in KENDRA_HOUSES:
                        cancellation = True
                        cancel_reason = f"Lord of exaltation sign ({exalt_lord}) in kendra from Moon."

        if cancellation:
            yogas.append({
                "name": "Neecha Bhanga Raja Yoga",
                "formed_by": [p_name],
                "description": f"Debilitated {p_name} in {sign} with cancellation: {cancel_reason}",
            })

    # --- Parivartana Yoga: Mutual exchange of signs ---
    checked_pairs = set()
    for p1, d1 in planets.items():
        if p1 in ("Rahu", "Ketu"):
            continue
        lord_of_p1_sign = SIGN_LORDS.get(d1["sign"])
        if lord_of_p1_sign and lord_of_p1_sign != p1:
            d2 = planets.get(lord_of_p1_sign)
            if d2:
                lord_of_p2_sign = SIGN_LORDS.get(d2["sign"])
                if lord_of_p2_sign == p1:
                    pair = tuple(sorted([p1, lord_of_p1_sign]))
                    if pair not in checked_pairs:
                        checked_pairs.add(pair)
                        h1, h2 = d1["house"], d2["house"]
                        # Classify exchange type
                        if {h1, h2} <= DUSTHANA_HOUSES:
                            ptype = "Dainya"
                        elif {h1, h2} & DUSTHANA_HOUSES:
                            ptype = "Khala"
                        else:
                            ptype = "Maha"
                        yogas.append({
                            "name": f"Parivartana Yoga ({ptype})",
                            "formed_by": list(pair),
                            "description": f"{pair[0]} in {d1['sign'] if pair[0] == p1 else d2['sign']} and "
                                           f"{pair[1]} in {d2['sign'] if pair[1] == lord_of_p1_sign else d1['sign']} — mutual sign exchange.",
                        })

    # --- Dhana Yogas: Wealth combinations ---
    lord_2 = _lord_of_house(lagna_idx, 2)
    lord_5 = _lord_of_house(lagna_idx, 5)
    lord_9 = _lord_of_house(lagna_idx, 9)
    lord_11 = _lord_of_house(lagna_idx, 11)

    good_houses = KENDRA_HOUSES | TRIKONA_HOUSES
    # Lord of 2nd and 11th both in kendra/trikona
    l2d = planets.get(lord_2)
    l11d = planets.get(lord_11)
    if l2d and l11d and l2d.get("house") in good_houses and l11d.get("house") in good_houses:
        yogas.append({
            "name": "Dhana Yoga",
            "formed_by": [lord_2, lord_11],
            "description": f"Lord of 2nd ({lord_2}) in house {l2d['house']} and lord of 11th ({lord_11}) in house {l11d['house']}.",
        })
    # Lord of 5th and 9th conjoined or in mutual kendra
    l5d = planets.get(lord_5)
    l9d = planets.get(lord_9)
    if l5d and l9d:
        if l5d["sign"] == l9d["sign"]:
            yogas.append({
                "name": "Dhana Yoga",
                "formed_by": [lord_5, lord_9],
                "description": f"Lord of 5th ({lord_5}) and lord of 9th ({lord_9}) conjoined in {l5d['sign']}.",
            })
        elif _house_from(l5d["sign_idx"], l9d["sign_idx"]) in KENDRA_HOUSES:
            yogas.append({
                "name": "Dhana Yoga",
                "formed_by": [lord_5, lord_9],
                "description": f"Lord of 5th ({lord_5}) and lord of 9th ({lord_9}) in mutual kendra.",
            })

    # --- Sunapha / Anapha / Durudhura Yogas (Moon-based) ---
    if moon_data:
        sign_2nd_m = (moon_idx + 1) % 12
        sign_12th_m = (moon_idx - 1) % 12
        sunapha_planets = []
        anapha_planets = []
        for p_name, pd in planets.items():
            if p_name in ("Sun", "Moon", "Rahu", "Ketu"):
                continue
            if pd["sign_idx"] == sign_2nd_m:
                sunapha_planets.append(p_name)
            if pd["sign_idx"] == sign_12th_m:
                anapha_planets.append(p_name)

        if sunapha_planets and anapha_planets:
            yogas.append({
                "name": "Durudhura Yoga",
                "formed_by": sunapha_planets + anapha_planets,
                "description": f"Planets in 2nd ({', '.join(sunapha_planets)}) and 12th ({', '.join(anapha_planets)}) from Moon — wealth and fame.",
            })
        elif sunapha_planets:
            yogas.append({
                "name": "Sunapha Yoga",
                "formed_by": sunapha_planets,
                "description": f"{', '.join(sunapha_planets)} in 2nd from Moon — self-made wealth.",
            })
        elif anapha_planets:
            yogas.append({
                "name": "Anapha Yoga",
                "formed_by": anapha_planets,
                "description": f"{', '.join(anapha_planets)} in 12th from Moon — good character and comfort.",
            })

    # --- Amala Yoga: Natural benefic in 10th from Lagna or Moon ---
    for base_name, base_idx in [("Lagna", lagna_idx), ("Moon", moon_idx)]:
        for b_name in BENEFICS:
            bd = planets.get(b_name)
            if bd and _house_from(base_idx, bd["sign_idx"]) == 10:
                yogas.append({
                    "name": "Amala Yoga",
                    "formed_by": [b_name],
                    "description": f"{b_name} in 10th from {base_name} — virtuous deeds and lasting fame.",
                })
                break  # one benefic is enough per base

    # --- Saraswati Yoga: Jupiter, Venus, Mercury in kendra/trikona/2nd ---
    saraswati_houses = KENDRA_HOUSES | TRIKONA_HOUSES | {2}
    sara_ok = []
    for p_name in ("Jupiter", "Venus", "Mercury"):
        pd = planets.get(p_name)
        if pd and pd.get("house") in saraswati_houses:
            sara_ok.append(p_name)
    if len(sara_ok) == 3:
        jup_d = planets.get("Jupiter")
        if jup_d and (jup_d.get("dignity") in ("own_sign", "exalted", "mooltrikona") or jup_d.get("house") in KENDRA_HOUSES):
            yogas.append({
                "name": "Saraswati Yoga",
                "formed_by": sara_ok,
                "description": "Jupiter, Venus, Mercury in kendra/trikona/2nd with strong Jupiter — learning and wisdom.",
            })

    # --- Lakshmi Yoga: Lord of 9th in own/exalted + Venus in own/exalted kendra ---
    ven_d = planets.get("Venus")
    if l9d and ven_d:
        lord9_strong = l9d.get("dignity") in ("own_sign", "exalted", "mooltrikona")
        venus_strong = (ven_d.get("house") in KENDRA_HOUSES and
                        _is_exalted_or_own("Venus", ven_d["sign"]))
        if lord9_strong and venus_strong:
            yogas.append({
                "name": "Lakshmi Yoga",
                "formed_by": [lord_9, "Venus"],
                "description": f"Lord of 9th ({lord_9}) in dignity and Venus in own/exalted kendra — great wealth.",
            })

    # --- Voshi Yoga / Veshi Yoga: Planet in 2nd/12th from Sun ---
    if sun_d:
        sun_idx = sun_d["sign_idx"]
        sign_2nd_s = (sun_idx + 1) % 12
        sign_12th_s = (sun_idx - 1) % 12
        voshi_planets = []  # 12th from Sun
        veshi_planets = []  # 2nd from Sun
        for p_name, pd in planets.items():
            if p_name in ("Sun", "Moon", "Rahu", "Ketu"):
                continue
            if pd["sign_idx"] == sign_2nd_s:
                veshi_planets.append(p_name)
            if pd["sign_idx"] == sign_12th_s:
                voshi_planets.append(p_name)

        if veshi_planets and voshi_planets:
            yogas.append({
                "name": "Ubhayachari Yoga",
                "formed_by": veshi_planets + voshi_planets,
                "description": f"Planets in 2nd ({', '.join(veshi_planets)}) and 12th ({', '.join(voshi_planets)}) from Sun — balanced fame.",
            })
        elif veshi_planets:
            yogas.append({
                "name": "Veshi Yoga",
                "formed_by": veshi_planets,
                "description": f"{', '.join(veshi_planets)} in 2nd from Sun — industrious nature.",
            })
        elif voshi_planets:
            yogas.append({
                "name": "Voshi Yoga",
                "formed_by": voshi_planets,
                "description": f"{', '.join(voshi_planets)} in 12th from Sun — charitable nature.",
            })

    return yogas


def detect_kaal_sarpa(raw_planets):
    """
    Detect Kaal Sarpa Dosha: all 7 planets hemmed between Rahu-Ketu axis.
    
    Parameters
    ----------
    raw_planets : dict — raw planet data with 'sign_idx' for each planet
    
    Returns
    -------
    dict or None — dosha details if present, None otherwise
    """
    rahu_idx = raw_planets["Rahu"]["sign_idx"]
    ketu_idx = raw_planets["Ketu"]["sign_idx"]
    
    # The 7 planets (Sun through Saturn) must all be on one side of the Rahu-Ketu axis
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    
    # Check if all planets fall in the arc from Rahu to Ketu (going forward)
    def _in_arc(planet_idx, start_idx, end_idx):
        """Check if planet_idx is in the arc from start_idx to end_idx (exclusive of nodes)."""
        if start_idx == end_idx:
            return False
        if start_idx < end_idx:
            return start_idx < planet_idx < end_idx
        else:  # wraps around
            return planet_idx > start_idx or planet_idx < end_idx
    
    # Arc from Rahu to Ketu
    all_rahu_to_ketu = all(_in_arc(raw_planets[p]["sign_idx"], rahu_idx, ketu_idx) for p in seven)
    # Arc from Ketu to Rahu
    all_ketu_to_rahu = all(_in_arc(raw_planets[p]["sign_idx"], ketu_idx, rahu_idx) for p in seven)
    
    if all_rahu_to_ketu or all_ketu_to_rahu:
        # Determine type: Ascending (Rahu leads) or Descending (Ketu leads)
        if all_rahu_to_ketu:
            kaal_type = "Ascending (planets move toward Ketu)"
        else:
            kaal_type = "Descending (planets move toward Rahu)"
        
        return {
            "present": True,
            "type": kaal_type,
            "rahu_sign": ZODIAC_SIGNS[rahu_idx],
            "ketu_sign": ZODIAC_SIGNS[ketu_idx],
            "description": "All 7 planets hemmed between Rahu-Ketu axis — karmic restriction pattern affecting life direction.",
        }
    
    # Check partial Kaal Sarpa (one planet outside — still significant)
    for direction, checker in [("Rahu→Ketu", lambda p: _in_arc(raw_planets[p]["sign_idx"], rahu_idx, ketu_idx)),
                                ("Ketu→Rahu", lambda p: _in_arc(raw_planets[p]["sign_idx"], ketu_idx, rahu_idx))]:
        outside = [p for p in seven if not checker(p)]
        if len(outside) == 1:
            return {
                "present": True,
                "type": f"Partial ({outside[0]} outside)",
                "rahu_sign": ZODIAC_SIGNS[rahu_idx],
                "ketu_sign": ZODIAC_SIGNS[ketu_idx],
                "description": f"Near-complete Kaal Sarpa — only {outside[0]} escapes the nodal axis. Karmic themes still dominant.",
            }
    
    return None


def detect_graha_yuddha(raw_planets):
    """
    Detect Planetary War (Graha Yuddha): two planets within 1° of each other.
    Only applies to Mars, Mercury, Jupiter, Venus, Saturn (not Sun, Moon, Rahu, Ketu).
    The planet with higher longitude wins; the loser is weakened.
    
    Returns
    -------
    list of dict — each war detected
    """
    war_planets = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    wars = []
    
    for i in range(len(war_planets)):
        for j in range(i + 1, len(war_planets)):
            p1, p2 = war_planets[i], war_planets[j]
            lon1 = raw_planets[p1]["lon"]
            lon2 = raw_planets[p2]["lon"]
            
            # Angular separation (handle wrap-around at 360°)
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff
            
            if diff <= 1.0:
                # Planet with higher latitude wins (simplified: brighter/larger planet wins)
                # Traditional: planet with higher longitude in the same sign wins
                # Simplified: we report both and let interpretation handle it
                winner = p1 if lon1 > lon2 else p2
                loser = p2 if winner == p1 else p1
                wars.append({
                    "planet1": p1,
                    "planet2": p2,
                    "separation_degrees": round(diff, 4),
                    "winner": winner,
                    "loser": loser,
                    "description": f"{p1} and {p2} in planetary war ({diff:.2f}° apart) — {loser} is weakened, {winner} gains strength.",
                })
    
    return wars


def detect_gandanta(raw_planets, asc_lon=None):
    """
    Detect Gandanta: planets or Lagna at water-fire sign junctions (last/first 3°20').
    These are inauspicious knot points where nakshatra and sign boundaries overlap.
    
    Returns
    -------
    list of dict — each gandanta point detected
    """
    gandanta_points = []
    
    def _check_gandanta(name, longitude):
        sign_idx = int(longitude / 30) % 12
        degree = longitude % 30
        
        for water_idx, fire_idx in GANDANTA_JUNCTIONS:
            # Last 3°20' of water sign
            if sign_idx == water_idx and degree >= (30 - GANDANTA_ORB):
                return {
                    "planet": name,
                    "sign": ZODIAC_SIGNS[sign_idx],
                    "degree": round(degree, 2),
                    "junction": f"{ZODIAC_SIGNS[water_idx]}-{ZODIAC_SIGNS[fire_idx]}",
                    "position": "end_of_water_sign",
                    "description": f"{name} at {degree:.1f}° {ZODIAC_SIGNS[sign_idx]} — Gandanta zone (karmic knot, spiritual transformation).",
                }
            # First 3°20' of fire sign
            if sign_idx == fire_idx and degree <= GANDANTA_ORB:
                return {
                    "planet": name,
                    "sign": ZODIAC_SIGNS[sign_idx],
                    "degree": round(degree, 2),
                    "junction": f"{ZODIAC_SIGNS[water_idx]}-{ZODIAC_SIGNS[fire_idx]}",
                    "position": "start_of_fire_sign",
                    "description": f"{name} at {degree:.1f}° {ZODIAC_SIGNS[sign_idx]} — Gandanta zone (karmic knot, spiritual transformation).",
                }
        return None
    
    for name, rp in raw_planets.items():
        result = _check_gandanta(name, rp["lon"])
        if result:
            gandanta_points.append(result)
    
    if asc_lon is not None:
        result = _check_gandanta("Lagna", asc_lon)
        if result:
            gandanta_points.append(result)
    
    return gandanta_points
