"""Input validation for DashaFlow public API."""

import re
import pytz

_DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def validate_birth_input(dob: str, time: str, lat: float, lon: float, timezone: str):
    """Validate common birth chart inputs. Raises ValueError on bad data."""
    if not isinstance(dob, str) or not _DATE_RE.match(dob):
        raise ValueError(f"Invalid date format '{dob}'. Expected YYYY-MM-DD.")
    if not isinstance(time, str) or not _TIME_RE.match(time):
        raise ValueError(f"Invalid time format '{time}'. Expected HH:MM (24h).")
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} out of range [-90, 90].")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude {lon} out of range [-180, 180].")
    if timezone not in pytz.all_timezones:
        raise ValueError(f"Unknown timezone '{timezone}'. Use IANA format (e.g. 'Asia/Kolkata').")
