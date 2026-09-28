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

_SCHEMAS = {
    "compact": COMPACT_CHART_SCHEMA,
    "full": FULL_CHART_SCHEMA,
    "transit": TRANSIT_SCHEMA,
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
