"""
Yogini Dasha — 36-year Tantric cycle of eight Yoginis.

Order and years (lords in parentheses): Mangala 1 (Moon), Pingala 2 (Sun),
Dhanya 3 (Jupiter), Bhramari 4 (Mars), Bhadrika 5 (Mercury), Ulka 6 (Saturn),
Siddha 7 (Venus), Sankata 8 (Rahu). The cycle repeats (3 rounds ≈ 108 years).

Starting Yogini from the birth nakshatra (numbered 1-27 from Ashwini):
remainder of (nakshatra_number + 3) ÷ 8 → 1 Mangala … 7 Siddha, 0 Sankata.
Balance at birth is proportional to the Moon's remaining arc in its
nakshatra (same method as Vimshottari). Sub-periods divide each Mahadasha
proportionally (lord years / 36), starting from the Mahadasha's own Yogini.
"""

import datetime
import logging
import math

from .constants import NAK_SPAN
from .dasha import SIDEREAL_YEAR_DAYS
from .nakshatra import get_nakshatra

logger = logging.getLogger(__name__)

# (name, lord, years, temperament)
YOGINIS = [
    ("Mangala", "Moon", 1, "auspicious beginnings, emotional warmth"),
    ("Pingala", "Sun", 2, "authority and visibility; can scorch"),
    ("Dhanya", "Jupiter", 3, "prosperity, learning, dharma"),
    ("Bhramari", "Mars", 4, "restless drive, conflict, movement"),
    ("Bhadrika", "Mercury", 5, "intellect, commerce, skill"),
    ("Ulka", "Saturn", 6, "obstruction, delay, hard lessons"),
    ("Siddha", "Venus", 7, "fulfilment, pleasure, accomplishment"),
    ("Sankata", "Rahu", 8, "crisis, rupture, forced change"),
]
YOGINI_YEARS = {name: years for name, _lord, years, _t in YOGINIS}
YOGINI_TOTAL = 36.0
YOGINI_CYCLES = 3  # 3 rounds ≈ 108-year lifetime


def _start_index(nak_idx_0based: int) -> int:
    """0-based index into YOGINIS for a 0-based nakshatra index."""
    remainder = ((nak_idx_0based + 1) + 3) % 8
    return 7 if remainder == 0 else remainder - 1


def _build_yogini_subs(start_dt, total_days: float, starting_name: str) -> list:
    """Proportional sub-periods cycling from the parent Yogini onward."""
    seq_start = next(i for i, (name, _l, _y, _t) in enumerate(YOGINIS) if name == starting_name)
    periods = []
    cursor = start_dt
    for i in range(8):
        name, lord, years, temperament = YOGINIS[(seq_start + i) % 8]
        sub_days = total_days * years / YOGINI_TOTAL
        end = cursor + datetime.timedelta(days=sub_days)
        periods.append({
            "yogini": name,
            "lord": lord,
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "days": round(sub_days, 2),
            "_start_dt": cursor,
            "_end_dt": end,
        })
        cursor = end
    return periods


def calculate_yogini_dasha(moon_longitude: float, birth_dt, query_dt=None) -> dict:
    """
    Compute the Yogini Dasha timeline from Moon's sidereal longitude.

    Returns dict with keys: maha, antar, pratyantar, timeline. Each active
    period carries yogini, lord, temperament, start, end, days.
    """
    if isinstance(moon_longitude, bool) or not isinstance(moon_longitude, (int, float)):
        raise ValueError(f"Invalid moon_longitude '{moon_longitude}'. Must be a number.")
    if not math.isfinite(moon_longitude):
        raise ValueError(f"Invalid moon_longitude '{moon_longitude}'. Must be finite.")
    moon_longitude = moon_longitude % 360.0
    if not isinstance(birth_dt, datetime.datetime):
        raise ValueError("birth_dt must be a datetime.datetime.")
    if query_dt is None:
        logger.debug("query_dt omitted; defaulting to today at noon (stable within a day)")
        query_dt = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    if not isinstance(query_dt, datetime.datetime):
        raise ValueError("query_dt must be a datetime.datetime.")
    if hasattr(birth_dt, 'tzinfo') and birth_dt.tzinfo:
        birth_dt = birth_dt.replace(tzinfo=None)
    if hasattr(query_dt, 'tzinfo') and query_dt.tzinfo:
        query_dt = query_dt.replace(tzinfo=None)

    def _public(period):
        return {k: v for k, v in period.items() if not k.startswith("_")}

    def _find_active(periods, moment):
        for p in periods:
            if p["_start_dt"] <= moment < p["_end_dt"]:
                return p
        return None

    def _exact_days(period):
        return (period["_end_dt"] - period["_start_dt"]).total_seconds() / 86400.0

    nak_info = get_nakshatra(moon_longitude)
    start_idx = _start_index(nak_info["index"])

    # Balance from unrounded longitude (same precision rule as Vimshottari).
    elapsed = ((moon_longitude % 360.0) - nak_info["index"] * NAK_SPAN) / NAK_SPAN
    remaining = 1.0 - elapsed

    timeline = []
    cursor = birth_dt
    first_name, first_lord, first_years, first_temp = YOGINIS[start_idx]
    first_days = first_years * remaining * SIDEREAL_YEAR_DAYS
    first_end = cursor + datetime.timedelta(days=first_days)
    timeline.append({
        "yogini": first_name, "lord": first_lord, "temperament": first_temp,
        "start": cursor.strftime("%Y-%m-%d"), "end": first_end.strftime("%Y-%m-%d"),
        "years": round(first_years * remaining, 4), "days": round(first_days, 2),
        "_start_dt": cursor, "_end_dt": first_end,
    })
    cursor = first_end

    idx = start_idx + 1
    horizon = birth_dt + datetime.timedelta(days=YOGINI_TOTAL * YOGINI_CYCLES * SIDEREAL_YEAR_DAYS)
    guard = 0
    while cursor < horizon and guard < 40:
        name, lord, years, temperament = YOGINIS[idx % 8]
        days = years * SIDEREAL_YEAR_DAYS
        end = cursor + datetime.timedelta(days=days)
        timeline.append({
            "yogini": name, "lord": lord, "temperament": temperament,
            "start": cursor.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d"),
            "years": float(years), "days": round(days, 2),
            "_start_dt": cursor, "_end_dt": end,
        })
        cursor = end
        idx += 1
        guard += 1

    active_maha = _find_active(timeline, query_dt)
    active_antar = active_pratyantar = None
    if active_maha:
        active_antar = _find_active(
            _build_yogini_subs(active_maha["_start_dt"], _exact_days(active_maha), active_maha["yogini"]),
            query_dt)
        if active_antar:
            active_pratyantar = _find_active(
                _build_yogini_subs(active_antar["_start_dt"], _exact_days(active_antar),
                                   active_antar["yogini"]),
                query_dt)

    compact = [{"yogini": t["yogini"], "lord": t["lord"],
                "start": t["start"], "end": t["end"]} for t in timeline]
    return {
        "maha": _public(active_maha) if active_maha else None,
        "antar": _public(active_antar) if active_antar else None,
        "pratyantar": _public(active_pratyantar) if active_pratyantar else None,
        "timeline": compact,
    }
