"""Transit workbench — ingress scanning over a date range.

`cast_transit` answers "where are the planets on date X". These getters answer
timing questions: when a body changes sign, when Sade Sati starts and stops,
and how a transit scores against the native's ashtakavarga. All ephemeris work
runs under the shared `_SWE_LOCK`; a scan acquires it per call, never across
the whole range.
"""

import datetime
import logging

import pytz
import swisseph as swe

from ._validation import validate_birth_input, validate_query_date
from .constants import PLANETS, ZODIAC_SIGNS
from .errors import InvalidInputError
from .vedic_calculator import (
    _SWE_LOCK,
    _configure_swiss_ephemeris,
    calculate_vedic_chart,
)

logger = logging.getLogger(__name__)

_INGRESS_BODIES = ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_DEFAULT_BODIES = ("Jupiter", "Saturn", "Rahu")
_STEP_DAYS = {"Sun": 1, "Mars": 1, "Mercury": 1, "Venus": 1,
              "Jupiter": 5, "Saturn": 5, "Rahu": 5, "Ketu": 5}
_MAX_RANGE_YEARS = 15
_BISECTION_SECONDS = 60


def _validate_range(start_date: str, end_date: str) -> tuple:
    """Validate a date range and return (start, end) as date objects."""
    validate_query_date(start_date, "start_date")
    validate_query_date(end_date, "end_date")
    start = datetime.date.fromisoformat(start_date)
    end = datetime.date.fromisoformat(end_date)
    if start > end:
        raise InvalidInputError(
            f"Invalid range: start_date '{start_date}' is after end_date '{end_date}'.")
    if (end - start).days > 365 * _MAX_RANGE_YEARS + 5:
        raise InvalidInputError(
            f"Range too large: {_MAX_RANGE_YEARS} years maximum. "
            f"Requested {start_date} to {end_date}.")
    return start, end


def _jd_from_datetime(dt: datetime.datetime) -> float:
    """Julian day from an aware datetime (converted to UTC)."""
    utc = dt.astimezone(pytz.utc)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0
        + utc.microsecond / 3.6e9,
    )


def _local_midnight_jd(day: datetime.date, tz) -> float:
    """Julian day for local midnight of `day`, handling DST gaps."""
    try:
        local = tz.localize(datetime.datetime.combine(day, datetime.time(0)), is_dst=None)
    except Exception as exc:
        raise InvalidInputError(
            f"Unrepresentable local midnight '{day}' in '{tz.zone}': {exc}") from exc
    return _jd_from_datetime(local)


def _jd_to_utc_datetime(jd: float) -> datetime.datetime:
    """UTC datetime from a Julian day."""
    year, month, day, hour = swe.revjul(jd)
    base = datetime.datetime(year, month, day) + datetime.timedelta(hours=hour)
    return pytz.utc.localize(base)


def _longitude(jd: float, body: str) -> float:
    """Sidereal longitude of `body` at Julian day `jd` (Ketu derived from Rahu)."""
    with _SWE_LOCK:
        if body == "Ketu":
            res, _ = swe.calc_ut(jd, PLANETS["Rahu"], swe.FLG_SIDEREAL)
            return (res[0] + 180.0) % 360.0
        res, _ = swe.calc_ut(jd, PLANETS[body], swe.FLG_SIDEREAL)
        return res[0]


def _sign_index(jd: float, body: str) -> int:
    """Zodiac sign index (0=Aries) of `body` at Julian day `jd`."""
    return int(_longitude(jd, body) // 30) % 12


def _is_retrograde(jd: float, body: str) -> bool:
    """True when the body moves retrograde at `jd`; nodes are always retrograde."""
    if body in ("Rahu", "Ketu"):
        return True
    with _SWE_LOCK:
        res, _ = swe.calc_ut(jd, PLANETS[body], swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return res[3] < 0


def _crossings(start_jd: float, end_jd: float, body: str) -> list:
    """All sign changes of `body` in [start_jd, end_jd], bisected to a minute.

    The predicate is the sign index, not longitude: stations reverse longitude
    inside a bracket, and bisection on a non-monotonic quantity would lie.
    """
    step = _STEP_DAYS[body]
    events = []
    prev_jd = start_jd
    prev_sign = _sign_index(prev_jd, body)
    while prev_jd < end_jd:
        next_jd = min(prev_jd + step, end_jd)
        next_sign = _sign_index(next_jd, body)
        if next_sign != prev_sign:
            lo, hi = prev_jd, next_jd
            lo_sign = prev_sign
            while (hi - lo) * 86400.0 > _BISECTION_SECONDS:
                mid = (lo + hi) / 2.0
                if _sign_index(mid, body) == lo_sign:
                    lo = mid
                else:
                    hi = mid
            events.append((hi, prev_sign, next_sign))
            prev_sign = next_sign
        prev_jd = next_jd
    return events


def _house_from(sign_idx: int, reference_idx: int) -> int:
    """1-based house of `sign_idx` counted from `reference_idx`."""
    return (sign_idx - reference_idx) % 12 + 1


_PHASES = {11: "rising", 0: "peak", 1: "setting"}


def _sade_sati_phase(sign_idx: int, moon_idx: int) -> str:
    """Sade Sati phase for a Saturn sign relative to the natal Moon sign."""
    return _PHASES.get((sign_idx - moon_idx) % 12, "off")


def _local_date(jd: float, tz) -> datetime.date:
    """Local calendar date of a Julian day in `tz`."""
    return _jd_to_utc_datetime(jd).astimezone(tz).date()


def _build_sade_sati_spans(crossings: list, start: datetime.date,
                           end: datetime.date, moon_idx: int, tz,
                           merge_gap_days: int) -> list:
    """Disjoint phase spans, merging same-phase spans across short off gaps."""
    start_jd = _local_midnight_jd(start, tz)
    phase = _sade_sati_phase(_sign_index(start_jd, "Saturn"), moon_idx)
    raw = []
    seg_start = start
    edge = True
    for jd, _from_idx, to_idx in crossings:
        day = _local_date(jd, tz)
        if day <= seg_start:
            edge = False
            phase = _sade_sati_phase(to_idx, moon_idx)
            continue
        if day > end:
            break
        raw.append((phase, seg_start, day - datetime.timedelta(days=1), edge, False))
        edge = False
        phase = _sade_sati_phase(to_idx, moon_idx)
        seg_start = day
    raw.append((phase, seg_start, end, edge, True))

    spans = []
    current = None
    gap_days = 0
    gap_seen = False
    for span_phase, span_start, span_end, starts_edge, ends_edge in raw:
        if span_phase == "off":
            gap_days += (span_end - span_start).days + 1
            gap_seen = True
            continue
        span_days = (span_end - span_start).days + 1
        if (current is not None and current["phase"] == span_phase
                and gap_seen and gap_days <= merge_gap_days):
            current["end"] = span_end
            current["days"] += gap_days + span_days
            current["gap_days"] += gap_days
            current["interruptions"] += 1
            current["ends_after_range"] = ends_edge
        else:
            if current is not None:
                spans.append(current)
            current = {
                "phase": span_phase,
                "start": span_start,
                "end": span_end,
                "days": span_days,
                "gap_days": 0,
                "interruptions": 0,
                "starts_before_range": starts_edge,
                "ends_after_range": ends_edge,
            }
        gap_days = 0
        gap_seen = False
    if current is not None:
        spans.append(current)

    for span in spans:
        span["in_phase_days"] = span["days"] - span["gap_days"]
        span["start"] = span["start"].isoformat()
        span["end"] = span["end"].isoformat()
    return spans


def get_sade_sati_timeline(dob: str, time: str, lat: float, lon: float,
                           timezone: str, start_date: str, end_date: str,
                           merge_gap_days: int = 180) -> dict:
    """
    Sade Sati phases as a timeline of spans and raw crossings.

    A span is a disjoint phase window (``rising``, ``peak``, ``setting``).
    Same-phase spans separated by an "off" gap of ``merge_gap_days`` or less
    are merged and counted in ``interruptions``; a retrograde excursion into a
    different Sade Sati phase stays its own span. ``crossings`` keeps every
    Saturn sign change, entry and exit, so nothing is hidden.

    Parameters
    ----------
    dob, time, lat, lon, timezone : natal birth details (``HH:MM[:SS]``).
    start_date, end_date : ``YYYY-MM-DD``, inclusive, 15 years maximum.
    merge_gap_days : absorb off gaps up to this many days. Default 180.
        ``0`` returns literal spans.

    Returns
    -------
    dict with ``natal_moon_sign``, ``range``, ``merge_gap_days``,
    ``active_at_start``, ``active_at_end``, ``spans``, and ``crossings``.
    """
    validate_birth_input(dob, time, lat, lon, timezone)
    start, end = _validate_range(start_date, end_date)
    if (not isinstance(merge_gap_days, int) or isinstance(merge_gap_days, bool)
            or merge_gap_days < 0):
        raise InvalidInputError(
            f"Invalid merge_gap_days '{merge_gap_days}'. Must be a non-negative integer.")

    natal_chart = calculate_vedic_chart(dob, time, lat, lon, timezone)
    moon_sign = natal_chart["planets"]["Moon"]["sign"]
    moon_idx = ZODIAC_SIGNS.index(moon_sign)
    tz = pytz.timezone(timezone)
    start_jd = _local_midnight_jd(start, tz)
    end_jd = _local_midnight_jd(end + datetime.timedelta(days=1), tz)

    with _SWE_LOCK:
        _configure_swiss_ephemeris('')

    crossings_raw = _crossings(start_jd, end_jd, "Saturn")
    crossings = []
    for jd, from_idx, to_idx in crossings_raw:
        day = _local_date(jd, tz)
        if day < start or day > end:
            continue
        crossings.append({
            "date": day.isoformat(),
            "instant_utc": _jd_to_utc_datetime(jd).strftime("%Y-%m-%dT%H:%M:00Z"),
            "from_sign": ZODIAC_SIGNS[from_idx],
            "to_sign": ZODIAC_SIGNS[to_idx],
            "from_phase": _sade_sati_phase(from_idx, moon_idx),
            "to_phase": _sade_sati_phase(to_idx, moon_idx),
            "direction": "retrograde" if _is_retrograde(jd, "Saturn") else "direct",
        })

    spans = _build_sade_sati_spans(
        crossings_raw, start, end, moon_idx, tz, merge_gap_days)

    start_phase = _sade_sati_phase(_sign_index(start_jd, "Saturn"), moon_idx)
    end_phase = _sade_sati_phase(
        _sign_index(end_jd - 1.0 / 86400.0, "Saturn"), moon_idx)
    logger.debug("sade sati range=%s..%s spans=%d crossings=%d",
                 start_date, end_date, len(spans), len(crossings))

    return {
        "natal_moon_sign": moon_sign,
        "range": {"start": start_date, "end": end_date},
        "merge_gap_days": merge_gap_days,
        "active_at_start": start_phase != "off",
        "active_at_end": end_phase != "off",
        "spans": spans,
        "crossings": crossings,
    }


def get_transit_ingresses(dob: str, time: str, lat: float, lon: float,
                          timezone: str, start_date: str, end_date: str,
                          bodies: list = None) -> dict:
    """
    Find exact sign-ingress instants for selected bodies over a date range.

    Parameters
    ----------
    dob, time, lat, lon, timezone : natal birth details (``HH:MM[:SS]``).
    start_date, end_date : ``YYYY-MM-DD``, inclusive, 15 years maximum.
    bodies : optional list. Default ``["Jupiter", "Saturn", "Rahu"]``.
        Allowed: Sun, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.
        Moon is rejected (it changes sign every ~2.25 days).

    Returns
    -------
    dict with ``range``, ``bodies``, and chronological ``ingresses``. Each
    ingress carries ``planet``, local ``date``, ``instant_utc`` (minute
    precision), ``from_sign``, ``to_sign``, ``direction`` (direct/retrograde),
    and houses from the natal Lagna and Moon.
    """
    validate_birth_input(dob, time, lat, lon, timezone)
    start, end = _validate_range(start_date, end_date)

    if bodies is None:
        bodies = list(_DEFAULT_BODIES)
    elif isinstance(bodies, str):
        bodies = [bodies]
    else:
        bodies = list(bodies)
    if "Moon" in bodies:
        raise InvalidInputError(
            "Moon ingresses are not supported; it changes sign every ~2.25 days. "
            "Use cast_transit() for Moon positions.")
    invalid = [b for b in bodies if b not in _INGRESS_BODIES]
    if invalid:
        raise InvalidInputError(
            f"Unknown body {invalid[0]!r}. Allowed: {list(_INGRESS_BODIES)}.")
    bodies = list(dict.fromkeys(bodies))

    natal_chart = calculate_vedic_chart(dob, time, lat, lon, timezone)
    lagna_idx = ZODIAC_SIGNS.index(natal_chart["lagna"]["sign"])
    moon_idx = ZODIAC_SIGNS.index(natal_chart["planets"]["Moon"]["sign"])
    tz = pytz.timezone(timezone)

    start_jd = _local_midnight_jd(start, tz)
    end_jd = _local_midnight_jd(end + datetime.timedelta(days=1), tz)

    with _SWE_LOCK:
        _configure_swiss_ephemeris('')

    ingresses = []
    for body in bodies:
        for jd, from_idx, to_idx in _crossings(start_jd, end_jd, body):
            utc = _jd_to_utc_datetime(jd)
            ingresses.append({
                "planet": body,
                "date": utc.astimezone(tz).date().isoformat(),
                "instant_utc": utc.strftime("%Y-%m-%dT%H:%M:00Z"),
                "from_sign": ZODIAC_SIGNS[from_idx],
                "to_sign": ZODIAC_SIGNS[to_idx],
                "direction": "retrograde" if _is_retrograde(jd, body) else "direct",
                "house_from_lagna": _house_from(to_idx, lagna_idx),
                "house_from_moon": _house_from(to_idx, moon_idx),
            })
    ingresses.sort(key=lambda e: (e["instant_utc"], e["planet"]))
    logger.debug("transit ingresses range=%s..%s bodies=%d events=%d",
                 start_date, end_date, len(bodies), len(ingresses))

    return {
        "range": {"start": start_date, "end": end_date},
        "bodies": bodies,
        "ingresses": ingresses,
    }
