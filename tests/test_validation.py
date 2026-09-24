"""Validation tests for dashaflow._validation and public API wrappers."""

import pytest

import dashaflow
from dashaflow._validation import (
    validate_birth_input,
    validate_ephe_path,
    validate_query_date,
)


def test_valid_input_passes():
    validate_birth_input("1990-04-15", "14:30", 28.61, 77.21, "Asia/Kolkata")


def test_impossible_calendar_date_rejected():
    with pytest.raises(ValueError):
        validate_birth_input("2023-02-30", "12:00", 0.0, 0.0, "Asia/Kolkata")


def test_bad_format_rejected():
    with pytest.raises(ValueError):
        validate_birth_input("15-04-1990", "14:30", 0.0, 0.0, "Asia/Kolkata")
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "2pm", 0.0, 0.0, "Asia/Kolkata")


def test_non_numeric_lat_lon_rejected_as_valueerror():
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", "28.6", 77.2, "Asia/Kolkata")
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", 28.6, None, "Asia/Kolkata")
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", float("nan"), 0.0, "Asia/Kolkata")
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", 0.0, float("inf"), "Asia/Kolkata")
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", True, 0.0, "Asia/Kolkata")


def test_lat_lon_range():
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", 91.0, 0.0, "Asia/Kolkata")
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", 0.0, 181.0, "Asia/Kolkata")


def test_unknown_timezone():
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", 0.0, 0.0, "Mars/Olympus")
    with pytest.raises(ValueError):
        validate_birth_input("1990-04-15", "14:30", 0.0, 0.0, None)


def test_query_date_validation():
    validate_query_date(None)
    validate_query_date("2026-01-01")
    with pytest.raises(ValueError):
        validate_query_date("2023-02-30", "query_date")
    with pytest.raises(ValueError):
        validate_query_date("not-a-date", "transit_date")


def test_ephe_path_validation(tmp_path):
    validate_ephe_path("")
    validate_ephe_path(str(tmp_path))
    with pytest.raises(ValueError):
        validate_ephe_path("/nonexistent/ephe/dir/xyz")
    with pytest.raises(ValueError):
        validate_ephe_path(123)


def test_cast_chart_rejects_bad_query_date():
    with pytest.raises(ValueError):
        dashaflow.cast_chart("1990-04-15", "14:30", 28.61, 77.21, "Asia/Kolkata",
                             query_date="2023-02-30")


def test_cast_transit_rejects_bad_transit_date():
    with pytest.raises(ValueError):
        dashaflow.cast_transit("bad-date", "1990-04-15", "14:30", 28.61, 77.21, "Asia/Kolkata")


def test_cast_chart_rejects_bad_ephe_path():
    with pytest.raises(ValueError):
        dashaflow.cast_chart("1990-04-15", "14:30", 28.61, 77.21, "Asia/Kolkata",
                             ephe_path="/nonexistent/dir")
