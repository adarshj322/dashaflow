"""Production guarantees: error taxonomy, thread-safety, determinism,
ephemeris-range honesty, output contract, and JSON-serializability."""

import concurrent.futures
import json

import pytest

import dashaflow
from dashaflow import CalculationError, DashaFlowError, EphemerisError, InvalidInputError

KWARGS = dict(time="14:30", lat=28.6139, lon=77.2090, timezone="Asia/Kolkata")


def test_error_taxonomy_backward_compatible():
    assert issubclass(InvalidInputError, ValueError)
    assert issubclass(InvalidInputError, DashaFlowError)
    assert issubclass(EphemerisError, DashaFlowError)
    assert issubclass(CalculationError, DashaFlowError)
    assert set(["DashaFlowError", "InvalidInputError", "EphemerisError", "CalculationError"]) <= set(
        dashaflow.__all__
    )


def test_invalid_input_raises_taxonomy_error():
    with pytest.raises(InvalidInputError):
        dashaflow.cast_chart("2023-02-30", **KWARGS)
    with pytest.raises(ValueError):  # backward compat
        dashaflow.cast_chart("2023-02-30", **KWARGS)


def test_transit_rejects_malformed_natal_chart():
    from dashaflow.vedic_calculator import calculate_transit
    with pytest.raises(InvalidInputError):
        calculate_transit("2026-03-29", {"lagna": {}}, "Asia/Kolkata")


def test_provenance_metadata_present():
    chart = dashaflow.cast_chart("1990-04-15", query_date="2026-01-01", **KWARGS)
    meta = chart["metadata"]
    assert meta["ephemeris_accuracy"] == "full"
    assert meta["ephemeris"] == "bundled"
    assert meta["dashaflow_version"] == dashaflow.__version__
    assert meta["swe_version"]
    assert meta["computed_at_utc"]


def test_out_of_range_birth_flags_reduced_accuracy():
    chart = dashaflow.cast_chart("1700-06-15", query_date="1700-07-01", **KWARGS)
    assert chart["metadata"]["ephemeris_accuracy"].startswith("reduced")
    # Still a contract-valid chart (Moshier fallback), not an exception.
    assert chart["lagna"]["sign"]


def test_determinism_same_inputs_same_outputs():
    kwargs = dict(KWARGS, query_date="2026-01-01")
    first = dashaflow.cast_chart("1990-04-15", **kwargs)
    second = dashaflow.cast_chart("1990-04-15", **kwargs)
    first["metadata"].pop("computed_at_utc")
    second["metadata"].pop("computed_at_utc")
    assert first == second


def test_concurrent_charts_match_serial_results():
    births = [
        ("1990-04-15", 28.6139, 77.2090, "Asia/Kolkata"),
        ("1918-10-16", 12.9716, 77.5946, "Asia/Kolkata"),
        ("2000-01-01", 51.5074, -0.1278, "Europe/London"),
        ("1985-07-04", 40.7128, -74.0060, "America/New_York"),
    ]
    serial = [dashaflow.cast_chart(d, "12:00", la, lo, tz, query_date="2026-01-01")["lagna"]["sign"]
              for d, la, lo, tz in births]

    def work(args):
        d, la, lo, tz = args
        return dashaflow.cast_chart(d, "12:00", la, lo, tz, query_date="2026-01-01")["lagna"]["sign"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        parallel = list(pool.map(work, births * 3))
    assert parallel == serial * 3


def test_full_chart_and_transit_json_serializable():
    chart = dashaflow.cast_chart("1990-04-15", **KWARGS)
    json.dumps(chart)
    transit = dashaflow.cast_transit("2026-03-29", "1990-04-15", "14:30",
                                     28.6139, 77.2090, "Asia/Kolkata")
    json.dumps(transit)
    assert set(transit) >= {"planets", "sade_sati", "rahu_ketu_axis"}
