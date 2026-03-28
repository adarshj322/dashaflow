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

    return yogas
