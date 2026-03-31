from .constants import NAKSHATRAS, NAK_SPAN, PADA_SPAN


def get_nakshatra(longitude):
    """
    Returns Nakshatra details for a given sidereal longitude (0-360).
    """
    longitude = longitude % 360.0
    nak_idx = int(longitude / NAK_SPAN)
    if nak_idx >= 27:
        nak_idx = 26
    degree_in_nak = longitude - (nak_idx * NAK_SPAN)
    pada = int(degree_in_nak / PADA_SPAN) + 1
    if pada > 4:
        pada = 4

    nak = NAKSHATRAS[nak_idx]
    return {
        "name": nak["name"],
        "pada": pada,
        "lord": nak["lord"],
        "index": nak_idx,
        "degree_in_nakshatra": round(degree_in_nak, 4),
    }
