"""
Chara Dasha — Jaimini sign-based periods (K.N. Rao / Upadesa Sutra method).

Each rashi's Mahadasha length comes from counting to its lord:
Savya signs (Aries, Taurus, Gemini, Libra, Scorpio, Sagittarius) count
forward (zodiacally) to the lord; Apasavya signs (Cancer, Leo, Virgo,
Capricorn, Aquarius, Pisces) count backward. Counts are exclusive
(minus one), giving 1-11 years; a lord placed in its own sign gives
12 years. Scorpio (Mars/Ketu) and Aquarius (Saturn/Rahu) use the
stronger of the two lords (placement dignity, tie → primary lord).

The cycle starts at the Lagna sign and runs zodiacally when the 9th
from Lagna is a Savya sign, else backward. Antardashas divide each
Mahadasha proportionally by the cycle's sign lengths, starting from
the Mahadasha's own sign in the cycle direction.

Verified against K.N. Rao's published Amitabh Bachchan sequence
(Aquarius 1942 → Pisces 1951 → Aries 1959 → Taurus 1964 → Gemini 1968
→ Cancer 1971 → Leo 1980 → Virgo 1991 → Libra 2003 → Scorpio 2014).
"""

import datetime
import logging

from .constants import SIGN_LORDS, ZODIAC_SIGNS
from .dasha import SIDEREAL_YEAR_DAYS
from .dignity import get_dignity

logger = logging.getLogger(__name__)

# Savya (direct-count) vs Apasavya (reverse-count) signs.
SAVYA_SIGNS = {0, 1, 2, 6, 7, 8}
APASAVYA_SIGNS = {3, 4, 5, 9, 10, 11}

# Dual lordship: (primary, co-lord) for strength resolution.
DUAL_LORDS = {7: ("Mars", "Ketu"), 10: ("Saturn", "Rahu")}

# Dignity ladder for dual-lord strength comparison.
_DIGNITY_RANK = {
    "own_sign": 6, "exalted": 5, "mooltrikona": 4, "great_friend": 3,
    "friend": 2, "neutral": 1, "enemy": 0, "great_enemy": -1, "debilitated": -2,
}

CHARA_HORIZON_YEARS = 120.0


def _resolve_lord(sign_idx: int, planets_in_signs: dict) -> tuple:
    """(lord_name, lord_sign_idx) with dual-lord strength resolution."""
    sign = ZODIAC_SIGNS[sign_idx]
    if sign_idx in DUAL_LORDS:
        primary, co = DUAL_LORDS[sign_idx]
        best, best_rank, best_pos = primary, -99, None
        for cand in (primary, co):
            pos = planets_in_signs.get(cand)
            if pos is None:
                continue
            dignity = get_dignity(cand, ZODIAC_SIGNS[pos], 15.0, planets_in_signs)
            rank = _DIGNITY_RANK.get(dignity, 1)
            if rank > best_rank:
                best, best_rank, best_pos = cand, rank, pos
        return best, best_pos
    lord = SIGN_LORDS[sign]
    return lord, planets_in_signs.get(lord)


def _sign_duration(sign_idx: int, planets_in_signs: dict) -> int:
    """Chara Mahadasha length for one sign (1-12 years)."""
    _lord, lord_pos = _resolve_lord(sign_idx, planets_in_signs)
    if lord_pos is None:
        raise ValueError(f"Cannot resolve lord position for {ZODIAC_SIGNS[sign_idx]}.")
    if lord_pos == sign_idx:
        return 12  # lord in own sign
    if sign_idx in SAVYA_SIGNS:
        return (lord_pos - sign_idx) % 12  # forward, exclusive
    return (sign_idx - lord_pos) % 12  # backward, exclusive


def _build_chara_subs(start_dt, total_days: float, starting_idx: int,
                      dur_by_sign: dict, forward: bool) -> list:
    """Proportional Antardashas from the parent sign in cycle direction."""
    total = sum(dur_by_sign.values())
    periods = []
    cursor = start_dt
    step = 1 if forward else -1
    for i in range(12):
        idx = (starting_idx + step * i) % 12
        sign = ZODIAC_SIGNS[idx]
        sub_days = total_days * dur_by_sign[idx] / total
        end = cursor + datetime.timedelta(days=sub_days)
        periods.append({
            "sign": sign,
            "lord": SIGN_LORDS[sign] if idx not in DUAL_LORDS else "/".join(DUAL_LORDS[idx]),
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "days": round(sub_days, 2),
            "_start_dt": cursor,
            "_end_dt": end,
        })
        cursor = end
    return periods


def calculate_chara_dasha(lagna_sign: str, birth_dt, query_dt=None,
                          planets_in_signs: dict = None) -> dict:
    """
    Compute the Chara Dasha timeline from the Lagna sign.

    Parameters
    ----------
    lagna_sign : str — Ascendant sign.
    birth_dt, query_dt : datetime.datetime.
    planets_in_signs : dict — {planet: 0-11 D1 sign_idx} for lord
        placement (required for durations).

    Returns dict with keys: maha, antar, timeline, direction, convention.
    Each period carries sign, lord, years, start, end, days.
    """
    if lagna_sign not in ZODIAC_SIGNS:
        raise ValueError(f"Invalid lagna_sign '{lagna_sign}'. Must be a zodiac sign.")
    if not isinstance(planets_in_signs, dict) or not planets_in_signs:
        raise ValueError("planets_in_signs is required for Chara durations.")
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

    lagna_idx = ZODIAC_SIGNS.index(lagna_sign)
    forward = ((lagna_idx + 8) % 12) in SAVYA_SIGNS  # 9th from Lagna
    step = 1 if forward else -1

    # One full 12-sign cycle of durations from the Lagna onward.
    cycle_idx = [(lagna_idx + step * i) % 12 for i in range(12)]
    dur_by_sign = {idx: _sign_duration(idx, planets_in_signs) for idx in cycle_idx}
    cycle_years = [dur_by_sign[idx] for idx in cycle_idx]

    timeline = []
    cursor = birth_dt
    horizon = birth_dt + datetime.timedelta(days=CHARA_HORIZON_YEARS * SIDEREAL_YEAR_DAYS)
    k = 0
    guard = 0
    # Worst case 1y/sign → 12y/cycle → 120 periods to clear the horizon;
    # the guard is a runaway fuse only, set far above any real count.
    while cursor < horizon and guard < 200:
        idx = cycle_idx[k % 12]
        sign = ZODIAC_SIGNS[idx]
        years = cycle_years[k % 12]
        days = years * SIDEREAL_YEAR_DAYS
        end = cursor + datetime.timedelta(days=days)
        lord = SIGN_LORDS[sign] if idx not in DUAL_LORDS else "/".join(DUAL_LORDS[idx])
        timeline.append({
            "sign": sign, "lord": lord,
            "start": cursor.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d"),
            "years": float(years), "days": round(days, 2),
            "_start_dt": cursor, "_end_dt": end,
        })
        cursor = end
        k += 1
        guard += 1

    active_maha = _find_active(timeline, query_dt)
    active_antar = None
    if active_maha:
        maha_idx = ZODIAC_SIGNS.index(active_maha["sign"])
        subs = _build_chara_subs(active_maha["_start_dt"], _exact_days(active_maha),
                                 maha_idx, dur_by_sign, forward)
        active_antar = _find_active(subs, query_dt)

    compact = [{"sign": t["sign"], "lord": t["lord"],
                "start": t["start"], "end": t["end"]} for t in timeline]
    return {
        "maha": _public(active_maha) if active_maha else None,
        "antar": _public(active_antar) if active_antar else None,
        "timeline": compact,
        "direction": "zodiacal" if forward else "reverse",
        "convention": "K.N. Rao sign-to-lord counts (own-sign lord = 12y), dual-lord strength",
    }
