"""
Published JSON Schemas for dashaflow outputs.

AI agents and MCP servers consume these to validate payloads and generate
tool schemas. This module has no third-party imports — schemas are plain
dicts. Use validate() with the optional `jsonschema` package installed.
"""

COMPACT_CHART_SCHEMA = {
    "type": "object",
    "required": ["lagna", "planets", "dashas", "yogas", "strengths"],
    "properties": {
        "lagna": {"type": "object"},
        "planets": {"type": "object"},
        "dashas": {"type": "object"},
        "yogas": {"type": "array", "items": {"type": "string"}},
        "strengths": {"type": "object"},
        "sav": {"type": "object"},
        "doshas": {"type": "object"},
        "time_sensitivity": {"type": ["object", "null"]},
        "ayanamsha": {"type": "string"},
        "ayanamsha_variant": {"type": "string"},
        "query_date": {"type": ["string", "null"]},
    },
}

FULL_CHART_SCHEMA = {
    "type": "object",
    "required": ["metadata", "panchang", "lagna", "planets", "dashas",
                 "yogini_dasha", "chara_dasha", "yogas", "ashtakavarga",
                 "sodhita_ashtakavarga", "jaimini_karakas", "shadbala",
                 "vimshopaka"],
    "properties": {
        "metadata": {"type": "object"},
        "panchang": {"type": "object"},
        "lagna": {"type": "object"},
        "planets": {"type": "object"},
        "dashas": {"type": "object"},
        "yogini_dasha": {"type": "object"},
        "chara_dasha": {"type": "object"},
        "yogas": {"type": "array"},
        "ashtakavarga": {"type": "object"},
        "sodhita_ashtakavarga": {"type": "object"},
        "jaimini_karakas": {"type": "object"},
        "shadbala": {"type": "object"},
        "vimshopaka": {"type": "object"},
    },
}

TRANSIT_SCHEMA = {
    "type": "object",
    "required": ["transit_date", "planets", "sade_sati", "rahu_ketu_axis"],
    "properties": {
        "transit_date": {"type": "string"},
        "planets": {"type": "object"},
        "sade_sati": {"type": "object"},
        "rahu_ketu_axis": {"type": "object"},
    },
}

COMPATIBILITY_SCHEMA = {
    "type": "object",
    "required": ["scores", "total_score", "max_score"],
    "properties": {
        "scores": {"type": "object"},
        "total_score": {"type": "number"},
        "max_score": {"type": "number"},
        "additional_kutas": {"type": "object"},
        "kuja_dosha": {"type": "object"},
    },
}

MUHURTHA_SCHEMA = {
    "type": "object",
    "required": ["activity", "verdict", "score"],
    "properties": {
        "activity": {"type": "string"},
        "verdict": {"type": "string",
                    "enum": ["auspicious", "mixed_favorable", "mixed",
                             "inauspicious", "error"]},
        "score": {"type": "number"},
        "positive_factors": {"type": "array"},
        "negative_factors": {"type": "array"},
    },
}

CAREER_SCHEMA = {
    "type": "object",
    "required": ["tenth_house", "career_themes"],
    "properties": {
        "tenth_house": {"type": "object"},
        "d10_indicators": {"type": "object"},
        "career_themes": {"type": "array"},
        "strength_factors": {"type": "array"},
    },
}

TRANSIT_INGRESSES_SCHEMA = {
    "type": "object",
    "required": ["range", "bodies", "ingresses"],
    "properties": {
        "range": {
            "type": "object",
            "required": ["start", "end"],
            "properties": {
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
        },
        "bodies": {"type": "array", "items": {"type": "string"}},
        "ingresses": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["planet", "date", "instant_utc", "from_sign",
                             "to_sign", "direction", "house_from_lagna",
                             "house_from_moon"],
                "properties": {
                    "planet": {"type": "string"},
                    "date": {"type": "string"},
                    "instant_utc": {"type": "string"},
                    "from_sign": {"type": "string"},
                    "to_sign": {"type": "string"},
                    "direction": {"type": "string",
                                  "enum": ["direct", "retrograde"]},
                    "house_from_lagna": {"type": "integer", "minimum": 1,
                                         "maximum": 12},
                    "house_from_moon": {"type": "integer", "minimum": 1,
                                        "maximum": 12},
                },
            },
        },
    },
}

SADE_SATI_TIMELINE_SCHEMA = {
    "type": "object",
    "required": ["natal_moon_sign", "range", "merge_gap_days",
                 "active_at_start", "active_at_end", "spans", "crossings"],
    "properties": {
        "natal_moon_sign": {"type": "string"},
        "range": {
            "type": "object",
            "required": ["start", "end"],
            "properties": {
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
        },
        "merge_gap_days": {"type": "integer", "minimum": 0},
        "active_at_start": {"type": "boolean"},
        "active_at_end": {"type": "boolean"},
        "spans": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["phase", "start", "end", "days", "gap_days",
                             "in_phase_days", "interruptions",
                             "starts_before_range", "ends_after_range"],
                "properties": {
                    "phase": {"type": "string",
                              "enum": ["rising", "peak", "setting"]},
                    "start": {"type": "string"},
                    "end": {"type": "string"},
                    "days": {"type": "integer", "minimum": 1},
                    "gap_days": {"type": "integer", "minimum": 0},
                    "in_phase_days": {"type": "integer", "minimum": 0},
                    "interruptions": {"type": "integer", "minimum": 0},
                    "starts_before_range": {"type": "boolean"},
                    "ends_after_range": {"type": "boolean"},
                },
            },
        },
        "crossings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["date", "instant_utc", "from_sign", "to_sign",
                             "from_phase", "to_phase", "direction"],
                "properties": {
                    "date": {"type": "string"},
                    "instant_utc": {"type": "string"},
                    "from_sign": {"type": "string"},
                    "to_sign": {"type": "string"},
                    "from_phase": {"type": "string"},
                    "to_phase": {"type": "string"},
                    "direction": {"type": "string",
                                  "enum": ["direct", "retrograde"]},
                },
            },
        },
    },
}

GOCHARA_SCHEMA = {
    "type": "object",
    "required": ["transit_date", "reference", "natal_moon_sign",
                 "sav_average", "planets"],
    "properties": {
        "transit_date": {"type": "string"},
        "reference": {"type": "string", "enum": ["moon"]},
        "natal_moon_sign": {"type": "string"},
        "sav_average": {"type": "number"},
        "planets": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["sign", "house_from_moon", "is_retrograde",
                             "sav_points", "house_quality",
                             "weighted_verdict", "notes"],
                "properties": {
                    "sign": {"type": "string"},
                    "house_from_moon": {"type": "integer", "minimum": 1,
                                        "maximum": 12},
                    "is_retrograde": {"type": "boolean"},
                    "sav_points": {"type": "integer", "minimum": 0},
                    "house_quality": {"type": "string",
                                      "enum": ["favorable", "unfavorable"]},
                    "weighted_verdict": {"type": "string",
                                         "enum": ["favorable", "mixed",
                                                  "unfavorable"]},
                    "notes": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}

_SCHEMAS = {
    "compact": COMPACT_CHART_SCHEMA,
    "full": FULL_CHART_SCHEMA,
    "transit": TRANSIT_SCHEMA,
    "transit_ingresses": TRANSIT_INGRESSES_SCHEMA,
    "sade_sati_timeline": SADE_SATI_TIMELINE_SCHEMA,
    "gochara": GOCHARA_SCHEMA,
    "compatibility": COMPATIBILITY_SCHEMA,
    "muhurtha": MUHURTHA_SCHEMA,
    "career": CAREER_SCHEMA,
}


def validate(schema_name: str, payload: dict) -> None:
    """Validate payload against a named schema. Needs `jsonschema` installed."""
    if schema_name not in _SCHEMAS:
        from .errors import InvalidInputError
        raise InvalidInputError(
            f"Unknown schema '{schema_name}'. Known: {sorted(_SCHEMAS)}.")
    try:
        import jsonschema
    except ImportError:
        raise ImportError(
            "validate() needs the optional 'jsonschema' package "
            "(pip install jsonschema).") from None
    jsonschema.validate(payload, _SCHEMAS[schema_name])
