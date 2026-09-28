"""Tests for dashaflow.schemas — published JSON Schemas for AI consumers."""

import json

import dashaflow
from dashaflow import schemas


def _chart():
    return dashaflow.cast_chart(
        "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
        query_date="2026-01-01",
    )


class TestSchemas:
    def test_compact_schema_validates_compact_chart(self):
        import jsonschema

        compact = dashaflow.summarize_chart(_chart())
        jsonschema.validate(compact, schemas.COMPACT_CHART_SCHEMA)

    def test_full_chart_has_schema(self):
        assert "required" in schemas.FULL_CHART_SCHEMA
        assert "dashas" in schemas.FULL_CHART_SCHEMA["properties"]

    def test_all_five_outputs_have_schemas(self):
        for name in ("COMPACT_CHART_SCHEMA", "FULL_CHART_SCHEMA",
                     "TRANSIT_SCHEMA", "COMPATIBILITY_SCHEMA",
                     "MUHURTHA_SCHEMA", "CAREER_SCHEMA"):
            schema = getattr(schemas, name)
            assert schema.get("type") == "object", name
            assert "properties" in schema, name
