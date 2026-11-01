"""Input validation for DashaFlow public API."""

import datetime
import math
import os
import re

import pytz

from .errors import InvalidInputError

_DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _check_calendar_date(value: str, field_name: str = "date") -> None:
    """Reject impossible calendar dates that pass the regex (e.g. 2023-02-30)."""
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise InvalidInputError(f"Invalid {field_name} '{value}'. Not a real calendar date (YYYY-MM-DD).") from None


def validate_date_string(value: str, field_name: str = "date") -> None:
    """Validate a YYYY-MM-DD string (format + real calendar date)."""
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise InvalidInputError(f"Invalid {field_name} format '{value}'. Expected YYYY-MM-DD.")
    _check_calendar_date(value, field_name)


def validate_birth_input(dob: str, time: str, lat: float, lon: float, timezone: str) -> None:
    """Validate common birth chart inputs. Raises InvalidInputError on bad data."""
    validate_date_string(dob, "dob")
    if not isinstance(time, str) or not _TIME_RE.match(time):
        raise InvalidInputError(f"Invalid time format '{time}'. Expected HH:MM (24h).")
    if isinstance(lat, bool) or not isinstance(lat, (int, float)) or not math.isfinite(lat):
        raise InvalidInputError(f"Invalid latitude '{lat}'. Must be a finite number in [-90, 90].")
    if isinstance(lon, bool) or not isinstance(lon, (int, float)) or not math.isfinite(lon):
        raise InvalidInputError(f"Invalid longitude '{lon}'. Must be a finite number in [-180, 180].")
    if not (-90 <= lat <= 90):
        raise InvalidInputError(f"Latitude {lat} out of range [-90, 90].")
    if not (-180 <= lon <= 180):
        raise InvalidInputError(f"Longitude {lon} out of range [-180, 180].")
    if not isinstance(timezone, str):
        raise InvalidInputError(f"Unknown timezone '{timezone}'. Use IANA format (e.g. 'Asia/Kolkata').")
    try:
        pytz.timezone(timezone)
    except Exception:
        raise InvalidInputError(f"Unknown timezone '{timezone}'. Use IANA format (e.g. 'Asia/Kolkata').") from None


def validate_query_date(query_date: str | None, field_name: str = "query_date") -> None:
    """Validate an optional YYYY-MM-DD query/transit date. None is allowed."""
    if query_date is None:
        return
    validate_date_string(query_date, field_name)


def validate_ephe_path(ephe_path: str) -> None:
    """Validate Swiss Ephemeris path. Empty string means bundled ephemeris."""
    if ephe_path in (None, ""):
        return
    if not isinstance(ephe_path, str):
        raise InvalidInputError(f"Invalid ephe_path '{ephe_path}'. Expected a directory path string.")
    if not os.path.isdir(ephe_path):
        raise InvalidInputError(f"Invalid ephe_path '{ephe_path}'. Directory does not exist.")
