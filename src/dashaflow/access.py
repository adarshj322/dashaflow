"""
Access shape — compact projections and focused getters for AI consumers.

A full chart is ~38KB of JSON. Most agent questions need one fact
(current Antardasha? Mars dignity?). These helpers project exactly
what's needed without recomputation. All functions are pure over a
chart dict as returned by cast_chart / calculate_vedic_chart.
"""

COMPACT_PLANET_FIELDS = ("sign", "house", "nakshatra", "dignity")


def summarize_chart(chart: dict, detail: str = "compact") -> dict:
    """
    Project a chart to a compact (~<4KB) summary for AI consumers.

    detail="compact" (default): five sections — lagna, condensed planets
    (sign/house/nakshatra/dignity only), active dasha lords for all three
    systems (no timelines), yoga names, strength totals+bands, SAV only,
    dosha flags. Each truncated section names the getter that returns
    the full data.
    detail="full": returns the chart unchanged.
    """
    if detail == "full":
        return chart
    if detail != "compact":
        from .errors import InvalidInputError
        raise InvalidInputError(
            f"Invalid detail '{detail}'. Expected 'compact' or 'full'.")

    dashas = chart.get("dashas", {})
    yogini = chart.get("yogini_dasha", {})
    chara = chart.get("chara_dasha", {})

    def _level(system: dict, *names: str) -> dict:
        out = {}
        for name in names:
            period = system.get(name) or {}
            out[name] = period.get("planet") or period.get("yogini") or period.get("sign")
        return out

    planets = {}
    for name, data in chart.get("planets", {}).items():
        planets[name] = {k: data.get(k) for k in COMPACT_PLANET_FIELDS}

    strengths = {}
    shadbala = chart.get("shadbala", {})
    vimshopaka = chart.get("vimshopaka", {})
    for name in chart.get("planets", {}):
        strengths[name] = {
            "shadbala_rupas": (shadbala.get(name) or {}).get("total_rupas"),
            "vimshopaka": (vimshopaka.get(name) or {}).get("total_20"),
            "vimshopaka_band": (vimshopaka.get(name) or {}).get("band"),
            "_detail": "call get_strength_table for full components",
        }

    doshas = {
        "kaal_sarpa": (chart.get("kaal_sarpa") or {}).get("type")
        if chart.get("kaal_sarpa") else None,
        "graha_yuddha": [w.get("planet1") + "/" + w.get("planet2", "")
                         for w in (chart.get("graha_yuddha") or [])],
        "gandanta": [g.get("planet") for g in (chart.get("gandanta") or [])],
    }

    return {
        "lagna": {
            "sign": chart.get("lagna", {}).get("sign"),
            "degree": chart.get("lagna", {}).get("degree"),
            "nakshatra": chart.get("lagna", {}).get("nakshatra"),
        },
        "planets": planets,
        "dashas": {
            "vimshottari": _level(dashas, "maha", "antar", "pratyantar"),
            "yogini": _level(yogini, "maha", "antar"),
            "chara": _level(chara, "maha", "antar"),
            "_detail": "call get_dasha_periods for full chains with dates",
        },
        "yogas": [y.get("name") for y in (chart.get("yogas") or [])],
        "strengths": strengths,
        "_yoga_detail": "call get_yoga_list for formed_by and descriptions",
        "sav": chart.get("ashtakavarga", {}).get("sarvashtakavarga", {}),
        "doshas": doshas,
        "query_date": chart.get("metadata", {}).get("query_date"),
    }


def get_dasha_periods(chart: dict) -> dict:
    """Full dasha chains (with dates) for Vimshottari, Yogini, Chara."""
    return {
        "vimshottari": chart.get("dashas", {}),
        "yogini": chart.get("yogini_dasha", {}),
        "chara": chart.get("chara_dasha", {}),
    }


def get_strength_table(chart: dict) -> dict:
    """Per-planet strength: Shadbala rupas, Vimshopaka total+band, Sodhya Pinda."""
    shadbala = chart.get("shadbala", {})
    vimshopaka = chart.get("vimshopaka", {})
    pinda = chart.get("sodhita_ashtakavarga", {}).get("sodhya_pinda", {})
    table = {}
    for name in chart.get("planets", {}):
        table[name] = {
            "shadbala_rupas": (shadbala.get(name) or {}).get("total_rupas"),
            "shadbala_required": (shadbala.get(name) or {}).get("required_rupas"),
            "is_strong": (shadbala.get(name) or {}).get("is_strong"),
            "vimshopaka": (vimshopaka.get(name) or {}).get("total_20"),
            "vimshopaka_band": (vimshopaka.get(name) or {}).get("band"),
            "sodhya_pinda": pinda.get(name),
        }
    return table


def get_yoga_list(chart: dict) -> list:
    """Full yoga entries (name, formed_by, description)."""
    return [
        {"name": y.get("name"), "formed_by": y.get("formed_by"),
         "description": y.get("description")}
        for y in (chart.get("yogas") or [])
    ]
