import datetime
import logging
import math

from .constants import DASHA_SEQUENCE, NAK_SPAN, VIMSHOTTARI_TOTAL, VIMSHOTTARI_YEARS
from .nakshatra import get_nakshatra

logger = logging.getLogger(__name__)

# Sidereal year (time for Sun to return to same sidereal longitude).
# Vimshottari periods are defined in sidereal years, not tropical years.
# 365.2425 (tropical) drifts ~1.6 days over a 120-year cycle vs 365.2563.
SIDEREAL_YEAR_DAYS = 365.2563


def _build_sub_periods(start_dt, total_days: float, starting_lord: str) -> list:
    """
    Build sub-periods (Antardasha or Pratyantardasha) within a parent period.
    The sub-period sequence starts from the parent lord and cycles through
    the Dasha sequence.

    Internal boundaries keep full datetime precision; start/end strings are
    date-only for backwards-compatible output. Private _start_dt/_end_dt
    keys are used for active-period lookup to avoid up-to-1-day truncation
    error on sukshma/prana levels.
    """
    seq_start = DASHA_SEQUENCE.index(starting_lord)
    periods = []
    cursor = start_dt

    for i in range(9):
        lord = DASHA_SEQUENCE[(seq_start + i) % 9]
        proportion = VIMSHOTTARI_YEARS[lord] / VIMSHOTTARI_TOTAL
        sub_days = total_days * proportion
        end = cursor + datetime.timedelta(days=sub_days)
        periods.append({
            "planet": lord,
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "days": round(sub_days, 2),
            "_start_dt": cursor,
            "_end_dt": end,
        })
        cursor = end

    return periods


def calculate_dashas(moon_longitude: float, birth_dt, query_dt=None) -> dict:
    """
    Compute Vimshottari Dasha timeline from Moon's sidereal longitude at birth.

    Parameters
    ----------
    moon_longitude : float
        Sidereal longitude of the Moon at birth (0-360).
    birth_dt : datetime.datetime
        Birth datetime (timezone-aware or naive).
    query_dt : datetime.datetime, optional
        Date to find active Maha/Antar/Pratyantar for. Defaults to today.

    Returns
    -------
    dict with keys: maha, antar, pratyantar, sukshma, prana, timeline.
    Active levels are None when the query predates birth or falls beyond
    the ~120-year span.

    Notes
    -----
    Period lengths use the sidereal year (365.2563 days). Sub-period
    boundaries keep full datetime precision internally; start/end strings
    remain date-only for backwards compatibility.
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
        """Strip internal datetime helpers so output stays JSON-serializable."""
        return {k: v for k, v in period.items() if not k.startswith("_")}

    def _find_active(periods, moment):
        for p in periods:
            if p["_start_dt"] <= moment < p["_end_dt"]:
                return p
        return None

    def _exact_days(period):
        """Exact span in days — never the rounded display value, so sub-periods
        tile the parent boundary with no gap/overlap drift."""
        return (period["_end_dt"] - period["_start_dt"]).total_seconds() / 86400.0

    nak_info = get_nakshatra(moon_longitude)
    nak_lord = nak_info["lord"]

    # Balance from the UNROUNDED longitude: get_nakshatra() rounds
    # degree_in_nakshatra to 4dp (~1h error), so recompute exactly here.
    nak_idx = int((moon_longitude % 360.0) / NAK_SPAN)
    elapsed_fraction = ((moon_longitude % 360.0) - nak_idx * NAK_SPAN) / NAK_SPAN
    remaining_fraction = 1.0 - elapsed_fraction

    seq_start = DASHA_SEQUENCE.index(nak_lord)

    # Build Mahadasha timeline starting from birth.
    # First (balance) period + full lords until 120 sidereal years are covered.
    timeline = []
    cursor = birth_dt

    first_maha_years = VIMSHOTTARI_YEARS[nak_lord] * remaining_fraction
    first_maha_days = first_maha_years * SIDEREAL_YEAR_DAYS
    first_end = cursor + datetime.timedelta(days=first_maha_days)
    timeline.append({
        "planet": nak_lord,
        "start": cursor.strftime("%Y-%m-%d"),
        "end": first_end.strftime("%Y-%m-%d"),
        "years": round(first_maha_years, 4),
        "days": round(first_maha_days, 2),
        "_start_dt": cursor,
        "_end_dt": first_end,
    })
    cursor = first_end

    # Remaining lords in sequence, repeating until 120+ sidereal years covered.
    idx = 1
    horizon = birth_dt + datetime.timedelta(days=VIMSHOTTARI_TOTAL * SIDEREAL_YEAR_DAYS)
    while cursor < horizon:
        lord = DASHA_SEQUENCE[(seq_start + idx) % 9]
        years = VIMSHOTTARI_YEARS[lord]
        days = years * SIDEREAL_YEAR_DAYS
        end = cursor + datetime.timedelta(days=days)
        timeline.append({
            "planet": lord,
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "years": float(years),
            "days": round(days, 2),
            "_start_dt": cursor,
            "_end_dt": end,
        })
        cursor = end
        idx += 1
        if idx > 30:  # safety: 30 mahadashas >> 120 years
            break

    # Query before birth or beyond the 120-year cycle → no active periods.
    active_maha = _find_active(timeline, query_dt)
    active_antar = None
    active_pratyantar = None
    active_sukshma = None
    active_prana = None

    if active_maha:
        antars = _build_sub_periods(active_maha["_start_dt"], _exact_days(active_maha), active_maha["planet"])
        active_antar = _find_active(antars, query_dt)

        if active_antar:
            pratyantars = _build_sub_periods(active_antar["_start_dt"], _exact_days(active_antar), active_antar["planet"])
            active_pratyantar = _find_active(pratyantars, query_dt)

            # Level 4: Sukshma Dasha
            if active_pratyantar:
                sukshmas = _build_sub_periods(
                    active_pratyantar["_start_dt"], _exact_days(active_pratyantar), active_pratyantar["planet"])
                active_sukshma = _find_active(sukshmas, query_dt)

                # Level 5: Prana Dasha
                if active_sukshma:
                    pranas = _build_sub_periods(
                        active_sukshma["_start_dt"], _exact_days(active_sukshma), active_sukshma["planet"])
                    active_prana = _find_active(pranas, query_dt)

    # Trim timeline to a reasonable window (birth to ~120 years)
    compact_timeline = []
    for t in timeline:
        compact_timeline.append({
            "planet": t["planet"],
            "start": t["start"],
            "end": t["end"],
        })
        if t["_end_dt"] > horizon:
            break

    return {
        "maha": _public(active_maha) if active_maha else None,
        "antar": _public(active_antar) if active_antar else None,
        "pratyantar": _public(active_pratyantar) if active_pratyantar else None,
        "sukshma": _public(active_sukshma) if active_sukshma else None,
        "prana": _public(active_prana) if active_prana else None,
        "timeline": compact_timeline,
    }
