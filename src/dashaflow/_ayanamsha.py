"""Ayanamsha variant allowlist and resolver."""

import swisseph as swe

from .errors import InvalidInputError

AYANAMSHA_VARIANTS: dict[str, tuple[str, int]] = {
    "lahiri": ("Lahiri", swe.SIDM_LAHIRI),
    "lahiri_icrc": ("Lahiri-ICRC", swe.SIDM_LAHIRI_ICRC),
    "true_citra": ("True Citra", swe.SIDM_TRUE_CITRA),
    "raman": ("Raman", swe.SIDM_RAMAN),
    "krishnamurti": ("Krishnamurti (KP old)", swe.SIDM_KRISHNAMURTI),
    "krishnamurti_vp291": ("Krishnamurti VP291 (KP new)", swe.SIDM_KRISHNAMURTI_VP291),
    "yukteshwar": ("Yukteshwar", swe.SIDM_YUKTESHWAR),
    "fagan_bradley": ("Fagan-Bradley", swe.SIDM_FAGAN_BRADLEY),
}

_ALIASES = {
    "icrc": "lahiri_icrc",
    "true_chitra": "true_citra",
    "kp": "krishnamurti",
    "kp_old": "krishnamurti",
    "kp_new": "krishnamurti_vp291",
    "kp_vp291": "krishnamurti_vp291",
    "yukteshvara": "yukteshwar",
}


def resolve_ayanamsha(value: str | None) -> tuple[str, str, int]:
    """Resolve an ayanamsha name or alias to (key, display, SIDM constant)."""
    if value is None or value == "":
        value = "lahiri"
    if not isinstance(value, str):
        raise InvalidInputError(
            f"Unknown ayanamsha {value!r}. Supported: {', '.join(AYANAMSHA_VARIANTS)}.")
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    key = _ALIASES.get(key, key)
    try:
        display, sidm = AYANAMSHA_VARIANTS[key]
    except KeyError:
        raise InvalidInputError(
            f"Unknown ayanamsha {value!r}. Supported: {', '.join(AYANAMSHA_VARIANTS)}.") from None
    return key, display, sidm
