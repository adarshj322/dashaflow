"""Birth-time sensitivity — how fragile a chart is to time uncertainty.

A Lagna moves ~1 deg per 4 minutes, so a few minutes of birth-time error
can flip the ascendant, a Moon pada, or the Vimshottari balance lord while
nothing in the chart says so. get_time_sensitivity() re-casts at the edges
of a stated uncertainty window and reports what moves, so agents can hedge
borderline charts instead of asserting them.
"""

import datetime

from ._validation import (
    validate_ayanamsha,
    validate_birth_input,
    validate_ephe_path,
    validate_query_date,
)
from .errors import InvalidInputError
from .vedic_calculator import calculate_vedic_chart


def _shift(dob_str: str, time_str: str, minutes: int) -> tuple:
    """Shift a birth datetime by minutes; return (dob, time) handling rollover."""
    fmt = "%Y-%m-%d %H:%M:%S" if time_str.count(":") == 2 else "%Y-%m-%d %H:%M"
    dt = datetime.datetime.strptime(f"{dob_str} {time_str}", fmt)
    dt += datetime.timedelta(minutes=minutes)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")


def _lagna_key(chart: dict) -> tuple:
    lagna = chart["lagna"]
    return lagna["sign"], lagna["degree"]


def _moon_key(chart: dict) -> tuple:
    moon = chart["planets"]["Moon"]
    return moon["sign"], moon["nakshatra"], moon["pada"]


def get_time_sensitivity(dob: str, time: str, lat: float, lon: float,
                         timezone: str, window_minutes: int = 4,
                         query_date: str = None, ephe_path: str = '',
                         ayanamsha: str = "lahiri") -> dict:
    """Report how the chart changes across a birth-time uncertainty window.

    Casts the chart at time-window and time+window and diffs the three.
    verdict is 'fragile' if anything structural flips inside the window,
    'borderline' if a cusp/pada edge lies within one window's movement
    (twice the error would flip it), else 'robust'.
    """
    validate_birth_input(dob, time, lat, lon, timezone)
    validate_query_date(query_date, "query_date")
    validate_ephe_path(ephe_path)
    validate_ayanamsha(ayanamsha)
    if not isinstance(window_minutes, (int, float)) or window_minutes <= 0:
        raise InvalidInputError(
            f"Invalid window_minutes '{window_minutes}'. Must be a positive number.")

    base = calculate_vedic_chart(dob, time, lat, lon, timezone, query_date, ephe_path,
                                 ayanamsha=ayanamsha)
    lo_dob, lo_time = _shift(dob, time, -window_minutes)
    hi_dob, hi_time = _shift(dob, time, +window_minutes)
    lo = calculate_vedic_chart(lo_dob, lo_time, lat, lon, timezone, query_date, ephe_path,
                               ayanamsha=ayanamsha)
    hi = calculate_vedic_chart(hi_dob, hi_time, lat, lon, timezone, query_date, ephe_path,
                               ayanamsha=ayanamsha)
    charts = (lo, base, hi)

    base_sign, base_deg = _lagna_key(base)
    lagna_signs = {_lagna_key(c)[0] for c in charts}
    lagna_stable = len(lagna_signs) == 1
    if lagna_stable:
        lagna_shift = max(_lagna_key(c)[1] for c in charts) - min(_lagna_key(c)[1] for c in charts)
    else:
        degs = sorted(_lagna_key(c)[1] for c in charts)
        lagna_shift = round((30 - degs[0]) + degs[-1], 3)
    cusp_distance = round(min(base_deg, 30 - base_deg), 3)

    moon_keys = {_moon_key(c) for c in charts}
    moon_pada_stable = len(moon_keys) == 1

    houses = [{p: d["house"] for p, d in c["planets"].items()} for c in charts]
    houses_stable = houses[0] == houses[1] == houses[2]

    balance_lords = {c["dashas"]["timeline"][0]["planet"] for c in charts}
    balance_stable = len(balance_lords) == 1

    notes = []
    if not lagna_stable:
        notes.append(f"Lagna flips within +-{window_minutes} min: "
                     f"{sorted(lagna_signs)[0]} <-> {sorted(lagna_signs)[-1]}.")
    if not moon_pada_stable:
        notes.append("Moon nakshatra/pada changes within the window; "
                     "Vimshottari balance is uncertain.")
    if not balance_stable:
        notes.append(f"Dasha balance lord changes: {sorted(balance_lords)}.")
    moved = [p for p in houses[0] if not (houses[0][p] == houses[1][p] == houses[2][p])]
    if moved:
        notes.append(f"Houses shift for: {', '.join(sorted(moved))}.")

    if not (lagna_stable and moon_pada_stable and balance_stable and houses_stable):
        verdict = "fragile"
    elif cusp_distance <= lagna_shift:
        verdict = "borderline"
        notes.append(f"Lagna {base_deg} deg {base_sign} is {cusp_distance} deg from a cusp; "
                     f"~{lagna_shift} deg moves across the window.")
    else:
        verdict = "robust"

    return {
        "window_minutes": window_minutes,
        "lagna": {"sign": base_sign, "degree": base_deg},
        "lagna_shift_deg": round(lagna_shift, 3),
        "lagna_stable": lagna_stable,
        "moon_pada_stable": moon_pada_stable,
        "houses_stable": houses_stable,
        "balance_lord_stable": balance_stable,
        "verdict": verdict,
        "notes": notes,
    }
