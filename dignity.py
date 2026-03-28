from constants import (
    EXALTATION, DEBILITATION, OWN_SIGNS, MOOLTRIKONA,
    SIGN_LORDS, NATURAL_FRIENDS, NATURAL_ENEMIES, NATURAL_NEUTRALS,
    COMBUSTION_ORBS, ZODIAC_SIGNS,
)


def get_dignity(planet_name, sign, degree_in_sign, planets_in_signs=None):
    """
    Determine a planet's dignity in a given sign per BPHS.
    Returns one of: exalted, mooltrikona, own_sign, friend, neutral, enemy, debilitated.
    Rahu/Ketu get a simplified check (exalt/debilit/own or neutral).
    """
    if planet_name in EXALTATION and EXALTATION[planet_name][0] == sign:
        if planet_name in MOOLTRIKONA:
            mt_sign, mt_start, mt_end = MOOLTRIKONA[planet_name]
            if mt_sign == sign and mt_start <= degree_in_sign <= mt_end:
                return "mooltrikona"
        return "exalted"

    if planet_name in DEBILITATION and DEBILITATION[planet_name][0] == sign:
        return "debilitated"

    if planet_name in OWN_SIGNS and sign in OWN_SIGNS[planet_name]:
        if planet_name in MOOLTRIKONA:
            mt_sign, mt_start, mt_end = MOOLTRIKONA[planet_name]
            if mt_sign == sign and mt_start <= degree_in_sign <= mt_end:
                return "mooltrikona"
        return "own_sign"

    if planet_name in MOOLTRIKONA:
        mt_sign, mt_start, mt_end = MOOLTRIKONA[planet_name]
        if mt_sign == sign and mt_start <= degree_in_sign <= mt_end:
            return "mooltrikona"

    if planet_name in ("Rahu", "Ketu"):
        return "neutral"

    sign_lord = SIGN_LORDS.get(sign)
    if not sign_lord:
        return "neutral"

    if planets_in_signs:
        return get_compound_relationship(planet_name, sign, planets_in_signs)

    if sign_lord in NATURAL_FRIENDS.get(planet_name, []):
        return "friend"
    if sign_lord in NATURAL_ENEMIES.get(planet_name, []):
        return "enemy"
    return "neutral"


def get_compound_relationship(planet_name, sign, planets_in_signs):
    """
    Compute Panchadha Maitri (5-fold compound relationship).
    Combines natural relationship with temporary friendship.
    Temporary friend = any planet in signs 2,3,4,10,11,12 from the planet.
    Temporary enemy = any planet in signs 1,5,6,7,8,9 (same sign counts as 1).

    Parameters
    ----------
    planet_name : str
    sign : str - the sign the planet occupies
    planets_in_signs : dict - {planet_name: sign_index} for all planets

    Returns one of: great_friend, friend, neutral, enemy, great_enemy
    """
    sign_lord = SIGN_LORDS.get(sign)
    if not sign_lord or planet_name in ("Rahu", "Ketu"):
        return "neutral"

    natural = _natural_relationship(planet_name, sign_lord)

    planet_sign_idx = ZODIAC_SIGNS.index(sign)
    sign_lord_idx = None
    for p, idx in planets_in_signs.items():
        if p == sign_lord:
            sign_lord_idx = idx
            break
    if sign_lord_idx is None:
        return natural

    dist = (sign_lord_idx - planet_sign_idx) % 12
    temp_friend_positions = {1, 2, 3, 9, 10, 11}
    is_temp_friend = dist in temp_friend_positions

    compound = _combine_relationships(natural, is_temp_friend)
    return compound


def _natural_relationship(planet, other):
    if other in NATURAL_FRIENDS.get(planet, []):
        return "friend"
    if other in NATURAL_ENEMIES.get(planet, []):
        return "enemy"
    return "neutral"


def _combine_relationships(natural, is_temp_friend):
    """Panchadha Maitri combination table."""
    if natural == "friend" and is_temp_friend:
        return "great_friend"
    if natural == "friend" and not is_temp_friend:
        return "neutral"
    if natural == "neutral" and is_temp_friend:
        return "friend"
    if natural == "neutral" and not is_temp_friend:
        return "enemy"
    if natural == "enemy" and is_temp_friend:
        return "neutral"
    if natural == "enemy" and not is_temp_friend:
        return "great_enemy"
    return "neutral"


def check_combustion(planet_name, planet_lon, sun_lon, is_retrograde=False):
    """
    Check if a planet is combust (too close to the Sun).
    Sun, Rahu, Ketu cannot be combust.
    """
    if planet_name in ("Sun", "Rahu", "Ketu"):
        return False

    orb_data = COMBUSTION_ORBS.get(planet_name)
    if orb_data is None:
        return False

    if isinstance(orb_data, dict):
        orb = orb_data["retrograde"] if is_retrograde else orb_data["direct"]
    else:
        orb = orb_data

    angular_dist = abs(planet_lon - sun_lon)
    if angular_dist > 180:
        angular_dist = 360 - angular_dist

    return angular_dist <= orb


def get_digbala(planet_name, house):
    """Check if a planet has directional strength in its current house."""
    from constants import DIGBALA_HOUSES
    ideal_house = DIGBALA_HOUSES.get(planet_name)
    if ideal_house is None:
        return False
    return house == ideal_house
