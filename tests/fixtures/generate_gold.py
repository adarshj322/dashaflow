"""One-time generator for tests/fixtures/gold_charts.json.

Fetches geocentric apparent observer ecliptic longitudes of date
(QUANTITIES=31) from JPL Horizons (DE441) for each chart's birth instant
and rewrites the fixture, preserving the ``published`` blocks.

Never imported by the test suite; tests read only the committed JSON and
never touch the network. Regenerating against the same Horizons version
must be text-identical (float round-trip through json.dump keeps numeric
literals free of trailing zeros).

Usage: python tests/fixtures/generate_gold.py
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import pytz

FIXTURE_PATH = Path(__file__).parent / "gold_charts.json"
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# Sun..Saturn in fixture order with Horizons COMMAND ids.
BODIES = [
    ("Sun", "10"),
    ("Moon", "301"),
    ("Mercury", "199"),
    ("Venus", "299"),
    ("Mars", "499"),
    ("Jupiter", "599"),
    ("Saturn", "699"),
]


def local_to_utc_iso(entry):
    """Convert a chart's local birth time to UTC and confirm the stored field."""
    tz = pytz.timezone(entry["timezone"])
    parts = [int(p) for p in entry["time"].split(":")]
    naive = datetime(
        int(entry["dob"][:4]), int(entry["dob"][5:7]), int(entry["dob"][8:10]),
        *parts,
    )
    utc = tz.localize(naive).astimezone(pytz.utc)
    iso = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    if iso != entry["utc"]:
        raise ValueError(
            f"{entry['name']}: computed UTC {iso} != stored {entry['utc']}"
        )
    return utc


def fetch_longitude(command, instant):
    """Return the observer ecliptic longitude (CSV column 3) for one body."""
    start = instant.strftime("%Y-%m-%d %H:%M")
    stop = (instant + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
    params = {
        "COMMAND": command,
        "CENTER": "500@399",
        "EPHEM_TYPE": "OBSERVER",
        "QUANTITIES": "31",
        "CSV_FORMAT": "YES",
        "EXTRA_PREC": "YES",
        "ANG_FORMAT": "DEG",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1m",
    }
    url = HORIZONS_URL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8", errors="replace")
    try:
        block = text.split("$$SOE")[1].split("$$EOE")[0]
    except IndexError as err:
        raise ValueError(f"COMMAND {command}: no $$SOE/$$EOE block in response") from err
    for line in block.strip().splitlines():
        line = line.strip()
        if line:
            return float(line.split(",")[3].strip())
    raise ValueError(f"COMMAND {command}: empty ephemeris block")


def main():
    fixture = json.loads(FIXTURE_PATH.read_text())
    for entry in fixture["charts"]:
        instant = local_to_utc_iso(entry)
        tropical = {}
        for name, command in BODIES:
            tropical[name] = fetch_longitude(command, instant)
            print(f"{entry['name']} {name}: {tropical[name]!r}")
        # Rebuild in fixture key order so a regenerate is text-identical.
        fixture["charts"][fixture["charts"].index(entry)] = {
            "name": entry["name"],
            "dob": entry["dob"],
            "time": entry["time"],
            "lat": entry["lat"],
            "lon": entry["lon"],
            "timezone": entry["timezone"],
            "utc": entry["utc"],
            "published": entry["published"],
            "horizons_tropical": tropical,
        }
    with open(FIXTURE_PATH, "w") as f:
        json.dump(fixture, f, indent=2, sort_keys=False)
        f.write("\n")
    print(f"rewrote {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
