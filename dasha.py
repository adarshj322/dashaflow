import datetime
from constants import VIMSHOTTARI_YEARS, DASHA_SEQUENCE, NAK_SPAN
from nakshatra import get_nakshatra


def _add_years_days(dt, years, days):
    """Add fractional years (as whole years + remaining days) to a datetime."""
    total_days = years * 365.2425 + days
    return dt + datetime.timedelta(days=total_days)


def _build_sub_periods(start_dt, total_days, starting_lord):
    """
    Build sub-periods (Antardasha or Pratyantardasha) within a parent period.
    The sub-period sequence starts from the parent lord and cycles through
    the Dasha sequence.
    """
    seq_start = DASHA_SEQUENCE.index(starting_lord)
    periods = []
    cursor = start_dt

    for i in range(9):
        lord = DASHA_SEQUENCE[(seq_start + i) % 9]
        proportion = VIMSHOTTARI_YEARS[lord] / 120.0
        sub_days = total_days * proportion
        end = cursor + datetime.timedelta(days=sub_days)
        periods.append({
            "planet": lord,
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "days": round(sub_days, 2),
        })
        cursor = end

    return periods


def calculate_dashas(moon_longitude, birth_dt, query_dt=None):
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
    dict with keys: maha, antar, pratyantar, timeline
    """
    if query_dt is None:
        query_dt = datetime.datetime.now()
    if hasattr(birth_dt, 'tzinfo') and birth_dt.tzinfo:
        birth_dt = birth_dt.replace(tzinfo=None)
    if hasattr(query_dt, 'tzinfo') and query_dt.tzinfo:
        query_dt = query_dt.replace(tzinfo=None)

    nak_info = get_nakshatra(moon_longitude)
    nak_lord = nak_info["lord"]

    elapsed_fraction = nak_info["degree_in_nakshatra"] / NAK_SPAN
    remaining_fraction = 1.0 - elapsed_fraction

    seq_start = DASHA_SEQUENCE.index(nak_lord)

    # Build Mahadasha timeline starting from birth
    timeline = []
    cursor = birth_dt

    first_maha_years = VIMSHOTTARI_YEARS[nak_lord] * remaining_fraction
    first_maha_days = first_maha_years * 365.2425
    first_end = cursor + datetime.timedelta(days=first_maha_days)
    timeline.append({
        "planet": nak_lord,
        "start": cursor.strftime("%Y-%m-%d"),
        "end": first_end.strftime("%Y-%m-%d"),
        "years": round(first_maha_years, 4),
        "days": round(first_maha_days, 2),
    })
    cursor = first_end

    # Remaining 8 full cycles, then repeat to cover 120+ years
    for cycle in range(2):
        start_offset = 1 if cycle == 0 else 0
        for i in range(start_offset, 9):
            lord = DASHA_SEQUENCE[(seq_start + i) % 9]
            years = VIMSHOTTARI_YEARS[lord]
            days = years * 365.2425
            end = cursor + datetime.timedelta(days=days)
            timeline.append({
                "planet": lord,
                "start": cursor.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "years": float(years),
                "days": days,
            })
            cursor = end

    active_maha = None
    active_antar = None
    active_pratyantar = None

    for period in timeline:
        p_start = datetime.datetime.strptime(period["start"], "%Y-%m-%d")
        p_end = datetime.datetime.strptime(period["end"], "%Y-%m-%d")
        if p_start <= query_dt < p_end:
            active_maha = period
            break

    if active_maha:
        maha_start = datetime.datetime.strptime(active_maha["start"], "%Y-%m-%d")
        maha_days = active_maha["days"]
        antars = _build_sub_periods(maha_start, maha_days, active_maha["planet"])

        for antar in antars:
            a_start = datetime.datetime.strptime(antar["start"], "%Y-%m-%d")
            a_end = datetime.datetime.strptime(antar["end"], "%Y-%m-%d")
            if a_start <= query_dt < a_end:
                active_antar = antar
                break

        if active_antar:
            antar_start = datetime.datetime.strptime(active_antar["start"], "%Y-%m-%d")
            antar_days = active_antar["days"]
            pratyantars = _build_sub_periods(antar_start, antar_days, active_antar["planet"])

            for prat in pratyantars:
                pr_start = datetime.datetime.strptime(prat["start"], "%Y-%m-%d")
                pr_end = datetime.datetime.strptime(prat["end"], "%Y-%m-%d")
                if pr_start <= query_dt < pr_end:
                    active_pratyantar = prat
                    break

    # Trim timeline to a reasonable window (birth to ~120 years)
    compact_timeline = []
    for t in timeline:
        compact_timeline.append({
            "planet": t["planet"],
            "start": t["start"],
            "end": t["end"],
        })
        t_end = datetime.datetime.strptime(t["end"], "%Y-%m-%d")
        if t_end > birth_dt + datetime.timedelta(days=120 * 365.2425):
            break

    return {
        "maha": active_maha,
        "antar": active_antar,
        "pratyantar": active_pratyantar,
        "timeline": compact_timeline,
    }
