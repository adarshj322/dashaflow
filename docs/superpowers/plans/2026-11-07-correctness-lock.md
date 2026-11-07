# Correctness Lock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship dashaflow 1.5.0 and rishi-ai-mcp 1.5.0 with a validated ayanamsha allowlist, a JPL-anchored gold corpus, ephemeris wrapper hardening.

**Architecture:** A new private `_ayanamsha.py` owns the eight-variant table, aliases, and `resolve_ayanamsha()`. Every casting function gains an `ayanamsha` keyword, resolves it once, and passes the canonical key down. `calculate_vedic_chart` writes the variant into metadata; transit functions read it back from the natal chart and re-assert the sidereal mode inside every locked `calc_ut`. The gold corpus is a committed JSON fixture generated once from JPL Horizons DE441; tests never touch the network.

**Tech Stack:** Python 3.10+, pyswisseph 2.10.03, pytz, pytest, ruff, hatchling. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-11-07-correctness-lock-design.md`

## Global Constraints

- Eight variants, canonical keys: `lahiri` (default), `lahiri_icrc`, `true_citra`, `raman`, `krishnamurti`, `krishnamurti_vp291`, `yukteshwar`, `fagan_bradley`.
- Lahiri default must produce the same positions, dasha dates, and metadata display (`"ayanamsha": "Lahiri"`) as 1.4.1.
- New arguments are appended after existing ones; existing positional calls keep working.
- Ayanamsha resolution normalizes case, spaces, and hyphens; unknown values raise `InvalidInputError` listing all options.
- Every `swe.*` touch runs under `_SWE_LOCK`; path and sidereal mode are re-asserted inside the lock before each per-call `calc_ut`.
- Gold values come from JPL Horizons DE441 only — never from the engine; tests never access the network.
- SAV total stays 337; MCP tool count stays 12.
- dashaflow 1.5.0 and rishi-ai-mcp 1.5.0; rishi pins `dashaflow>=1.5.0,<2.0.0`.
- Branch: `feature/correctness-lock` in dashaflow; `feature/correctness-lock` in rishi-ai-mcp.
- Local gate: `python -m pytest tests/ --junitxml=/tmp/opencode/<name>.xml` (parse `testsuite` counts; pytest 9.1.1's `-q` can print "No tests collected" misleadingly) and `python -m ruff check src tests`.
- rishi tests run with the global Python from the rishi repo root; its checked-in `.venv` is stale and must not be used.

## Review Focus

- An agent requests Raman once and a later drill-down silently returns Lahiri — every natal, transit, sensitivity, strength, dasha, and yoga path must carry the variant, and the compact MCP result must name it.
- A pre-1.5 chart dict has `metadata` but no `ayanamsha_variant` — `calculate_transit` must default to Lahiri, not crash or mix variants.
- `ephe_path` points at a directory with no `.se1` files — the chart must report reduced accuracy and log once, never claim `full (custom ephemeris path)`.
- Concurrent requests use different variants — the process-global sidereal mode must not leak between charts or transit scans.

---

### Task 1: Ayanamsha allowlist and resolver

**Files:**
- Create: `src/dashaflow/_ayanamsha.py`
- Modify: `src/dashaflow/_validation.py`
- Test: `tests/test_ayanamsha.py`

**Interfaces:**
- Produces:
  ```python
  AYANAMSHA_VARIANTS: dict[str, tuple[str, int]]   # key -> (display, SIDM constant)
  def resolve_ayanamsha(value: str | None) -> tuple[str, str, int]  # (key, display, sidm)
  def validate_ayanamsha(value: str | None) -> None
  ```

- [ ] **Step 1: Create the branch and commit the approved docs**

```bash
git checkout -b feature/correctness-lock
git add docs/superpowers/specs/2026-11-07-correctness-lock-design.md \
        docs/superpowers/plans/2026-11-07-correctness-lock.md
git commit -m "docs: correctness lock design and implementation plan"
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_ayanamsha.py
import pytest
import swisseph as swe

from dashaflow import InvalidInputError
from dashaflow._ayanamsha import AYANAMSHA_VARIANTS, resolve_ayanamsha
from dashaflow._validation import validate_ayanamsha

EXPECTED = {
    "lahiri": ("Lahiri", swe.SIDM_LAHIRI),
    "lahiri_icrc": ("Lahiri-ICRC", swe.SIDM_LAHIRI_ICRC),
    "true_citra": ("True Citra", swe.SIDM_TRUE_CITRA),
    "raman": ("Raman", swe.SIDM_RAMAN),
    "krishnamurti": ("Krishnamurti (KP old)", swe.SIDM_KRISHNAMURTI),
    "krishnamurti_vp291": ("Krishnamurti VP291 (KP new)", swe.SIDM_KRISHNAMURTI_VP291),
    "yukteshwar": ("Yukteshwar", swe.SIDM_YUKTESHWAR),
    "fagan_bradley": ("Fagan-Bradley", swe.SIDM_FAGAN_BRADLEY),
}


def test_variant_table_complete():
    assert AYANAMSHA_VARIANTS == EXPECTED


@pytest.mark.parametrize("value,key", [
    (None, "lahiri"), ("", "lahiri"), ("Lahiri", "lahiri"), ("LAHIRI", "lahiri"),
    ("lahiri-icrc", "lahiri_icrc"), ("icrc", "lahiri_icrc"),
    ("true chitra", "true_citra"), ("true_chitra", "true_citra"),
    ("kp", "krishnamurti"), ("kp_old", "krishnamurti"),
    ("kp_new", "krishnamurti_vp291"), ("kp_vp291", "krishnamurti_vp291"),
    ("yukteshvara", "yukteshwar"), ("fagan-bradley", "fagan_bradley"),
])
def test_resolution_and_aliases(value, key):
    assert resolve_ayanamsha(value)[0] == key


@pytest.mark.parametrize("bad", ["xyz", 42, object()])
def test_unknown_rejected(bad):
    with pytest.raises(InvalidInputError, match="Unknown ayanamsha"):
        resolve_ayanamsha(bad)


def test_error_lists_all_options():
    with pytest.raises(InvalidInputError) as exc:
        resolve_ayanamsha("xyz")
    for key in AYANAMSHA_VARIANTS:
        assert key in str(exc.value)


def test_validate_accepts_and_rejects():
    validate_ayanamsha("raman")
    with pytest.raises(InvalidInputError):
        validate_ayanamsha("nope")
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tests/test_ayanamsha.py --junitxml=/tmp/opencode/t1.xml`
Expected: collection error, `ModuleNotFoundError: No module named 'dashaflow._ayanamsha'`.

- [ ] **Step 4: Implement `src/dashaflow/_ayanamsha.py` and `validate_ayanamsha`**

The table is exactly `EXPECTED` above. Alias map:

```python
_ALIASES = {
    "icrc": "lahiri_icrc",
    "true_chitra": "true_citra",
    "kp": "krishnamurti",
    "kp_old": "krishnamurti",
    "kp_new": "krishnamurti_vp291",
    "kp_vp291": "krishnamurti_vp291",
    "yukteshvara": "yukteshwar",
}
```

`resolve_ayanamsha` maps `None`/`""` to `lahiri`, rejects non-strings, normalizes with
`value.strip().lower().replace("-", "_").replace(" ", "_")`, applies `_ALIASES`, then looks up
`AYANAMSHA_VARIANTS`. Unknown values raise:

```python
InvalidInputError(
    f"Unknown ayanamsha {value!r}. Supported: {', '.join(AYANAMSHA_VARIANTS)}.")
```

`validate_ayanamsha` in `_validation.py` calls `resolve_ayanamsha(value)` and discards the result.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ayanamsha.py --junitxml=/tmp/opencode/t1.xml`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/dashaflow/_ayanamsha.py src/dashaflow/_validation.py tests/test_ayanamsha.py
git commit -m "feat: add ayanamsha variant allowlist and resolver"
```

---

### Task 2: Chart calculation variant and metadata

**Files:**
- Modify: `src/dashaflow/vedic_calculator.py:57-60` (`_configure_swiss_ephemeris`), `:609-616` (contract), `:619-778` (`calculate_vedic_chart`)
- Test: `tests/test_ayanamsha.py`

**Interfaces:**
- Consumes: `resolve_ayanamsha`, `AYANAMSHA_VARIANTS` from Task 1.
- Produces:
  ```python
  def _configure_swiss_ephemeris(ephe_path: str = '', ayanamsha: str = "lahiri") -> None
  def calculate_vedic_chart(dob_str, time_str, lat, lon, timezone_str,
                            query_date_str=None, ephe_path='', ayanamsha="lahiri") -> dict
  ```
  Metadata gains `"ayanamsha_variant": str`; `"ayanamsha"` becomes the resolved display name.

- [ ] **Step 1: Write the failing tests**

Add `from dashaflow.vedic_calculator import calculate_vedic_chart` to the top of
`tests/test_ayanamsha.py`, then append:

```python
DELHI_1975 = ("1975-01-15", "09:00", 28.6139, 77.2090, "Asia/Kolkata")
DELHI_1990 = ("1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")
DELHI_1990_CUSP = ("1990-04-15", "11:35", 28.6139, 77.2090, "Asia/Kolkata")


def test_default_metadata_unchanged():
    chart = calculate_vedic_chart(
        "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")
    assert chart["metadata"]["ayanamsha"] == "Lahiri"
    assert chart["metadata"]["ayanamsha_variant"] == "lahiri"
    assert chart["metadata"]["ayanamsha_degrees"] == 23.7214


def test_raman_metadata_and_ayanamsha():
    chart = calculate_vedic_chart(*DELHI_1975, ayanamsha="raman")
    assert chart["metadata"]["ayanamsha"] == "Raman"
    assert chart["metadata"]["ayanamsha_variant"] == "raman"
    assert abs(chart["metadata"]["ayanamsha_degrees"] - 22.0621) < 0.001


def test_raman_flips_cusp_chart():
    # Raman's ayanamsha is smaller, so its sidereal longitudes run ~1.4463 deg ahead.
    lahiri = calculate_vedic_chart(*DELHI_1990_CUSP)
    raman = calculate_vedic_chart(*DELHI_1990_CUSP, ayanamsha="raman")
    assert lahiri["lagna"]["sign"] == "Gemini"
    assert raman["lagna"]["sign"] == "Cancer"


def test_invalid_variant_rejected_by_direct_caller():
    with pytest.raises(InvalidInputError, match="Unknown ayanamsha"):
        calculate_vedic_chart(*DELHI_1975, ayanamsha="nope")


def test_sav_invariant_survives_variant():
    assert calculate_vedic_chart(*DELHI_1975, ayanamsha="raman")["ashtakavarga"]["total_bindus"] == 337
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_ayanamsha.py -k "default_metadata or raman or invalid_variant or sav" --junitxml=/tmp/opencode/t2.xml`
Expected: FAIL — `calculate_vedic_chart()` has no `ayanamsha` argument.

- [ ] **Step 3: Implement**

- Import `AYANAMSHA_VARIANTS` and `resolve_ayanamsha` in `vedic_calculator.py`.
- Change `_configure_swiss_ephemeris` to `(ephe_path: str = '', ayanamsha: str = "lahiri")` and set the mode with `resolve_ayanamsha(ayanamsha)[2]`.
- Add `ayanamsha: str = "lahiri"` to `calculate_vedic_chart`; resolve once before the lock into `(variant_key, variant_display, _)`.
- Pass `variant_key` to both `_configure_swiss_ephemeris` calls in the function.
- Metadata: `"ayanamsha": variant_display`, `"ayanamsha_variant": variant_key`; keep `ayanamsha_degrees` as `round(ayanamsha_val, 4)`.
- In `_validate_chart_contract`, after the existing `ayanamsha_degrees` check:

```python
if chart_data["metadata"].get("ayanamsha_variant") not in AYANAMSHA_VARIANTS:
    raise CalculationError(
        f"Invalid ayanamsha_variant: {chart_data['metadata'].get('ayanamsha_variant')!r}")
```

- Update the `calculate_vedic_chart` docstring: sidereal with Lahiri default, `ayanamsha` selects a variant.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ayanamsha.py --junitxml=/tmp/opencode/t2.xml`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/dashaflow/vedic_calculator.py tests/test_ayanamsha.py
git commit -m "feat: expose ayanamsha variant in chart calculation and metadata"
```

---

### Task 3: Natal public API pass-through and compact projection

**Files:**
- Modify: `src/dashaflow/__init__.py` (`cast_chart`, `cast_charts`, `calculate_compatibility`, `check_muhurtha`, `analyze_career`; module docstring)
- Modify: `src/dashaflow/sensitivity.py` (`get_time_sensitivity`)
- Modify: `src/dashaflow/access.py` (`summarize_chart`)
- Modify: `src/dashaflow/schemas.py` (`COMPACT_CHART_SCHEMA`)
- Test: `tests/test_ayanamsha.py`, `tests/test_access_shape.py`

**Interfaces:**
- Consumes: `validate_ayanamsha`, `calculate_vedic_chart(..., ayanamsha=...)`.
- Produces:
  ```python
  cast_chart(..., ephe_path: str = '', ayanamsha: str = "lahiri") -> dict
  cast_charts(births, query_date=None, ephe_path='', max_workers=4,
              ayanamsha: str = "lahiri") -> list
  calculate_compatibility(..., ayanamsha: str = "lahiri") -> dict
  check_muhurtha(..., timezone: str, ayanamsha: str = "lahiri") -> dict
  analyze_career(..., timezone: str, ayanamsha: str = "lahiri") -> dict
  get_time_sensitivity(..., ephe_path='', ayanamsha: str = "lahiri") -> dict
  summarize_chart(...) compact adds "ayanamsha": str, "ayanamsha_variant": str
  ```

- [ ] **Step 1: Write the failing tests**

Add `import dashaflow` to the top of `tests/test_ayanamsha.py`, then append:

```python
def test_cast_chart_variant_pass_through():
    chart = dashaflow.cast_chart(*DELHI_1990_CUSP, ayanamsha="raman")
    assert chart["metadata"]["ayanamsha_variant"] == "raman"
    assert chart["lagna"]["sign"] == "Cancer"


def test_cast_chart_invalid_variant():
    with pytest.raises(InvalidInputError, match="Unknown ayanamsha"):
        dashaflow.cast_chart(*DELHI_1975, ayanamsha="nope")


def test_cast_charts_shared_variant():
    births = [DELHI_1975, ("1995-06-15", "14:30", 19.0760, 72.8777, "Asia/Kolkata")]
    charts = dashaflow.cast_charts(births, ayanamsha="raman")
    assert [c["metadata"]["ayanamsha_variant"] for c in charts] == ["raman", "raman"]


def test_every_natal_api_forwards_variant(monkeypatch):
    calls = []
    real = dashaflow.calculate_vedic_chart

    def recording(*args, **kwargs):
        calls.append(kwargs.get("ayanamsha"))
        return real(*args, **kwargs)

    monkeypatch.setattr(dashaflow, "calculate_vedic_chart", recording)

    dashaflow.calculate_compatibility(
        "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
        "1995-06-15", "14:30", 19.0760, 72.8777, "Asia/Kolkata",
        ayanamsha="raman")
    assert calls == ["raman", "raman"]

    calls.clear()
    dashaflow.check_muhurtha("travel", "2026-06-15", "10:00",
                             28.6139, 77.2090, "Asia/Kolkata", ayanamsha="raman")
    assert calls == ["raman"]

    calls.clear()
    dashaflow.analyze_career(*DELHI_1975, ayanamsha="raman")
    assert calls == ["raman"]


def test_time_sensitivity_forwards_variant(monkeypatch):
    import dashaflow.sensitivity as sensitivity

    seen = []
    real = sensitivity.calculate_vedic_chart

    def recording(*args, **kwargs):
        seen.append(kwargs.get("ayanamsha"))
        return real(*args, **kwargs)

    monkeypatch.setattr(sensitivity, "calculate_vedic_chart", recording)
    dashaflow.get_time_sensitivity(*DELHI_1990, ayanamsha="raman")
    assert seen == ["raman", "raman", "raman"]

    with pytest.raises(InvalidInputError, match="Unknown ayanamsha"):
        dashaflow.get_time_sensitivity(*DELHI_1990, ayanamsha="nope")
```

Append to `tests/test_access_shape.py`:

```python
def test_compact_projection_names_variant():
    chart = dashaflow.cast_chart(
        "1975-01-15", "09:00", 28.6139, 77.2090, "Asia/Kolkata",
        ayanamsha="raman")
    compact = summarize_chart(chart)
    assert compact["ayanamsha"] == "Raman"
    assert compact["ayanamsha_variant"] == "raman"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_ayanamsha.py tests/test_access_shape.py -k "variant" --junitxml=/tmp/opencode/t3.xml`
Expected: FAIL — unexpected keyword `ayanamsha`, and missing compact keys.

- [ ] **Step 3: Implement**

- Import `validate_ayanamsha` in `__init__.py`; call it at the top of each modified function.
- Append `ayanamsha` after the existing last argument and pass `ayanamsha=ayanamsha` to every `calculate_vedic_chart` call in `cast_chart`, `cast_charts`, `calculate_compatibility`, `check_muhurtha`, and `analyze_career`.
- In `get_time_sensitivity`, append `ayanamsha` after `ephe_path`, call `validate_ayanamsha`, and pass it to all three `calculate_vedic_chart` calls (base, lo, hi).
- In `summarize_chart`'s compact result, add:
  ```python
  "ayanamsha": chart.get("metadata", {}).get("ayanamsha"),
  "ayanamsha_variant": chart.get("metadata", {}).get("ayanamsha_variant", "lahiri"),
  ```
- Add the same two properties to `COMPACT_CHART_SCHEMA["properties"]` as strings.
- Update module/function docstrings that say "Sidereal Lahiri" to name the default and the variant parameter.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ayanamsha.py tests/test_access_shape.py tests/test_schemas.py --junitxml=/tmp/opencode/t3.xml`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dashaflow/__init__.py src/dashaflow/sensitivity.py src/dashaflow/access.py \
        src/dashaflow/schemas.py tests/test_ayanamsha.py tests/test_access_shape.py
git commit -m "feat: thread ayanamsha variant through natal public APIs"
```

---

### Task 4: Variant-aware transit paths

**Files:**
- Modify: `src/dashaflow/vedic_calculator.py:781-860` (`calculate_transit`)
- Modify: `src/dashaflow/transit.py:83-115` (helpers), `:217-300` (`get_sade_sati_timeline`), `:294-370` (`get_transit_ingresses`), `:398-470` (`get_gochara`)
- Modify: `src/dashaflow/__init__.py` (`cast_transit`)
- Test: `tests/test_ayanamsha.py`, `tests/test_transit_workbench.py`

**Interfaces:**
- Consumes: `resolve_ayanamsha`, `validate_ayanamsha`, chart metadata.
- Produces:
  ```python
  cast_transit(..., timezone: str = "Asia/Kolkata", ayanamsha: str = "lahiri") -> dict
  get_transit_ingresses(..., bodies=None, ayanamsha: str = "lahiri") -> dict
  get_sade_sati_timeline(..., merge_gap_days: int = 180, ayanamsha: str = "lahiri") -> dict
  get_gochara(..., transit_date: str, ayanamsha: str = "lahiri") -> dict
  ```
  `calculate_transit` keeps its signature and reads the variant from `natal_chart["metadata"]["ayanamsha_variant"]`, defaulting to `"lahiri"`.

- [ ] **Step 1: Write the failing tests**

Add `import concurrent.futures`, `import copy`, and
`from dashaflow.vedic_calculator import calculate_transit` to the top of
`tests/test_ayanamsha.py`, then append:

```python
def test_calculate_transit_reads_variant_from_natal():
    lahiri = dashaflow.cast_chart(*DELHI_1990_CUSP, ayanamsha="lahiri")
    raman = dashaflow.cast_chart(*DELHI_1990_CUSP, ayanamsha="raman")
    t_l = calculate_transit("2026-03-29", lahiri, "Asia/Kolkata")
    t_r = calculate_transit("2026-03-29", raman, "Asia/Kolkata")
    # The scan uses the Raman natal lagna (Cancer) and shifts the Sun forward.
    assert t_l["planets"]["Sun"]["house_from_lagna"] == 10
    assert t_r["planets"]["Sun"]["house_from_lagna"] == 9
    delta = (t_r["planets"]["Sun"]["degree"] - t_l["planets"]["Sun"]["degree"]) % 30
    assert abs(delta - 1.4463) < 0.02


def test_transit_pre_15_chart_defaults_lahiri():
    natal = dashaflow.cast_chart(*DELHI_1975)
    legacy = copy.deepcopy(natal)
    legacy["metadata"].pop("ayanamsha_variant")
    assert calculate_transit("2026-03-29", legacy, "Asia/Kolkata")["planets"] == \
        calculate_transit("2026-03-29", natal, "Asia/Kolkata")["planets"]


def test_cast_transit_variant_passthrough():
    natal = dashaflow.cast_chart(*DELHI_1975, ayanamsha="raman")
    direct = calculate_transit("2026-03-29", natal, "Asia/Kolkata")
    public = dashaflow.cast_transit(
        "2026-03-29", *DELHI_1975, ayanamsha="raman")
    assert public["planets"] == direct["planets"]


def test_gochara_variant_changes_reference():
    common = dict(dob=DELHI_1990[0], time=DELHI_1990[1], lat=DELHI_1990[2],
                  lon=DELHI_1990[3], timezone=DELHI_1990[4],
                  transit_date="2026-06-02")
    lahiri = dashaflow.get_gochara(**common)
    raman = dashaflow.get_gochara(**common, ayanamsha="raman")
    assert lahiri["natal_moon_sign"] == "Scorpio"
    assert raman["natal_moon_sign"] == "Sagittarius"


def test_ingress_variant_changes_natal_houses():
    common = dict(dob=DELHI_1990_CUSP[0], time=DELHI_1990_CUSP[1],
                  lat=DELHI_1990_CUSP[2], lon=DELHI_1990_CUSP[3],
                  timezone=DELHI_1990_CUSP[4],
                  start_date="2026-01-01", end_date="2026-02-01", bodies=["Sun"])
    lahiri = dashaflow.get_transit_ingresses(**common)
    raman = dashaflow.get_transit_ingresses(**common, ayanamsha="raman")
    assert lahiri["ingresses"] and raman["ingresses"]
    assert lahiri["ingresses"][0]["to_sign"] == "Capricorn"
    assert raman["ingresses"][0]["to_sign"] == "Capricorn"
    assert lahiri["ingresses"][0]["house_from_lagna"] == 8
    assert raman["ingresses"][0]["house_from_lagna"] == 7
    assert (lahiri["ingresses"][0]["instant_utc"]
            != raman["ingresses"][0]["instant_utc"])


def test_sade_sati_variant_changes_natal_moon():
    common = dict(dob=DELHI_1990[0], time=DELHI_1990[1], lat=DELHI_1990[2],
                  lon=DELHI_1990[3], timezone=DELHI_1990[4],
                  start_date="2026-01-01", end_date="2026-02-01")
    assert dashaflow.get_sade_sati_timeline(**common)["natal_moon_sign"] == "Scorpio"
    assert dashaflow.get_sade_sati_timeline(
        **common, ayanamsha="raman")["natal_moon_sign"] == "Sagittarius"


def test_concurrent_transit_scans_do_not_mix():
    def work(variant):
        return dashaflow.get_gochara(
            *DELHI_1990, transit_date="2026-06-02",
            ayanamsha=variant)["natal_moon_sign"]

    variants = ["lahiri", "raman"] * 4
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(work, variants)) == ["Scorpio", "Sagittarius"] * 4
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_ayanamsha.py -k "transit or gochara or ingress or sade or concurrent" --junitxml=/tmp/opencode/t4.xml`
Expected: FAIL — transit getters reject `ayanamsha`; `calculate_transit` ignores the natal variant.

- [ ] **Step 3: Implement**

- In `calculate_transit`, after the existing natal-structure block:

```python
metadata = natal_chart.get("metadata")
if metadata is not None and not isinstance(metadata, dict):
    raise InvalidInputError("Invalid natal_chart metadata: expected a dict.")
variant = (metadata or {}).get("ayanamsha_variant", "lahiri")
try:
    variant_key = resolve_ayanamsha(variant)[0]
except InvalidInputError:
    raise InvalidInputError(
        f"Invalid natal_chart ayanamsha_variant: {variant!r}") from None
```

Pass `variant_key` to `_configure_swiss_ephemeris('', variant_key)` inside the lock.

In `cast_transit`:

- Add `ayanamsha: str = "lahiri"` as the last parameter, call `validate_ayanamsha`, and pass `ayanamsha=ayanamsha` to its `calculate_vedic_chart` call. `calculate_transit` then reads the variant back from the chart metadata.

In `transit.py`:

- Add `ayanamsha` as the last parameter of all three public getters; call `validate_ayanamsha` and resolve the variant key once; pass `ayanamsha=variant_key` to each `calculate_vedic_chart` call.
- Add `ayanamsha: str = "lahiri"` to `_longitude`, `_sign_index`, `_is_retrograde`, `_crossings`, and `_build_sade_sati_spans`; thread it through every call, including the direct `_sign_index` calls in `get_sade_sati_timeline` and inside `_build_sade_sati_spans`.
- Inside `_longitude` and `_is_retrograde`, call `_configure_swiss_ephemeris('', ayanamsha)` inside `_SWE_LOCK` before each `swe.calc_ut`. This is the re-assertion that closes the cross-thread variant leak.
- Delete the scan-level `with _SWE_LOCK: _configure_swiss_ephemeris('')` blocks at `transit.py:256` and `:347`; per-call re-assertion replaces them.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ayanamsha.py tests/test_transit_workbench.py --junitxml=/tmp/opencode/t4.xml`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dashaflow/vedic_calculator.py src/dashaflow/transit.py src/dashaflow/__init__.py \
        tests/test_ayanamsha.py
git commit -m "feat: make transit scans variant-aware and race-safe"
```

---

### Task 5: Ephemeris wrapper hardening

**Files:**
- Modify: `src/dashaflow/vedic_calculator.py:39-54` (accuracy heuristics), `:324-352` (`_compute_raw_planets`), `:649-745` (`calculate_vedic_chart`), `:781-860` (`calculate_transit`)
- Modify: `src/dashaflow/transit.py:83-108` (helpers)
- Test: `tests/test_production.py`

**Interfaces:**
- Produces:
  ```python
  _EPHEMERIS_WARNING_EMITTED: bool
  def _check_ephemeris_flags(flags: int) -> None
  def _ephemeris_accuracy(flags: int, ephe_path: str) -> str
  def _compute_raw_planets(jd: float, flags: int) -> tuple[dict, float, int]
  ```

- [ ] **Step 1: Write the failing tests**

Add `import logging`, `import math`, and `import swisseph as swe` to the top of
`tests/test_production.py`. Replace the first assertion in
`test_provenance_metadata_present` with:

```python
    # Default install has no .se1 files; the backend returns Moshier flags.
    assert meta["ephemeris_accuracy"].startswith("reduced")
```

Append:

```python
def test_empty_ephemeris_dir_reports_reduced_not_custom_full(tmp_path):
    chart = dashaflow.cast_chart(
        "1990-04-15", query_date="2026-01-01", ephe_path=str(tmp_path), **KWARGS)
    assert chart["metadata"]["ephemeris"] == str(tmp_path)
    assert chart["metadata"]["ephemeris_accuracy"].startswith("reduced")


def test_moshier_warning_logged_once(monkeypatch, caplog, tmp_path):
    import dashaflow.vedic_calculator as vc

    monkeypatch.setattr(vc, "_EPHEMERIS_WARNING_EMITTED", False)
    with caplog.at_level(logging.WARNING, logger="dashaflow.vedic_calculator"):
        vc.calculate_vedic_chart(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
            query_date_str="2026-01-01", ephe_path=str(tmp_path))
        assert caplog.text.count("Moshier fallback") == 1
        caplog.clear()
        vc.calculate_vedic_chart(
            "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
            query_date_str="2026-01-01", ephe_path=str(tmp_path))
        assert "Moshier fallback" not in caplog.text


def test_ephemeris_accuracy_from_flags():
    from dashaflow.vedic_calculator import _ephemeris_accuracy

    assert _ephemeris_accuracy(swe.FLG_MOSEPH, "").startswith("reduced")
    assert _ephemeris_accuracy(swe.FLG_SWIEPH, "") == "full"
    assert _ephemeris_accuracy(swe.FLG_JPLEPH, "") == "full (JPL ephemeris)"


def test_arctic_chart_has_finite_lagna():
    chart = dashaflow.cast_chart(
        "1990-06-15", "12:00", 78.2232, 15.6469, "Arctic/Longyearbyen",
        query_date="2026-01-01")
    assert chart["lagna"]["sign"] == "Leo"
    assert math.isfinite(chart["lagna"]["degree"])
    assert abs(chart["lagna"]["degree"] - 28.91) <= 0.05
    assert chart["planets"]["Moon"]["sign"] == "Aquarius"


def test_concurrent_variants_do_not_mix():
    variants = ["lahiri", "raman"] * 4

    def work(variant):
        chart = dashaflow.cast_chart(
            "1990-04-15", "11:35", 28.6139, 77.2090, "Asia/Kolkata",
            ayanamsha=variant)
        return (chart["metadata"]["ayanamsha_variant"],
                chart["lagna"]["sign"],
                chart["metadata"]["ayanamsha_degrees"])

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(work, variants))

    for variant, (key, sign, degrees) in zip(variants, results):
        assert key == variant
        assert sign == ("Gemini" if variant == "lahiri" else "Cancer")
        expected = 23.7214 if variant == "lahiri" else 22.2751
        assert abs(degrees - expected) < 0.001
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_production.py --junitxml=/tmp/opencode/t5.xml`
Expected: FAIL — accuracy still reports `full`; helpers do not exist.

- [ ] **Step 3: Implement**

- Add `_EPHEMERIS_WARNING_EMITTED = False` and `_check_ephemeris_flags(flags)`; it logs the exact warning once when `flags & swe.FLG_MOSEPH`:
  `"Swiss ephemeris unavailable; using Moshier fallback (reduced accuracy). Provide .se1 files via ephe_path."`
- Replace the path/year heuristic with `_ephemeris_accuracy(flags, ephe_path)`: Moshier first → `"reduced (Moshier fallback — provide .se1 files via ephe_path for full accuracy)"`; then JPL → `"full (JPL ephemeris)"`; then custom path → `"full (custom ephemeris path)"`; else `"full"`. Delete `_FULL_ACCURACY_RANGE`.
- `_compute_raw_planets` captures the flags returned by each `swe.calc_ut` and returns `(raw_planets, sun_lon, calc_flags)`.
- `calculate_vedic_chart` calls `_check_ephemeris_flags(calc_flags)` inside the lock and derives `accuracy` from `calc_flags`; remove the birth-year warning.
- `calculate_transit` captures the flags from its `calc_ut` loop and calls `_check_ephemeris_flags` once after the loop.
- Import `_check_ephemeris_flags` from `.vedic_calculator` in `transit.py`; call it with the returned flags in `_longitude` and `_is_retrograde` inside the lock.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_production.py tests/test_transit_workbench.py --junitxml=/tmp/opencode/t5.xml`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dashaflow/vedic_calculator.py src/dashaflow/transit.py tests/test_production.py
git commit -m "fix: derive ephemeris accuracy from backend flags and log Moshier fallback"
```

---

### Task 6: JPL Horizons gold corpus and tolerance ladder

**Files:**
- Create: `tests/fixtures/gold_charts.json`
- Create: `tests/fixtures/generate_gold.py`
- Create: `tests/test_gold_corpus.py`

**Interfaces:**
- Consumes: `cast_chart(..., ayanamsha=...)`, `constants.ZODIAC_SIGNS`, `constants.NAK_SPAN`, `constants.VIMSHOTTARI_YEARS`, `dasha.SIDEREAL_YEAR_DAYS`.
- Produces: committed fixtures and tests only; no runtime code.

- [ ] **Step 1: Write the fixture**

Create `tests/fixtures/gold_charts.json` with exactly this content (Horizons DE441 values
retrieved 2026-11-07; geocentric apparent ecliptic longitude of date, degrees):

```json
{
  "provenance": {
    "oracle": "JPL Horizons",
    "oracle_version": "DE441",
    "retrieved": "2026-11-07",
    "ayanamsha": "Lahiri",
    "ayanamsha_constant": "SIDM_LAHIRI",
    "quantity": "observer ecliptic longitude of date, geocentric apparent (QUANTITIES=31)",
    "compare": "engine sidereal longitude + metadata ayanamsha_degrees, tolerance 0.05 deg",
    "generator": "tests/fixtures/generate_gold.py"
  },
  "charts": [
    {
      "name": "raman_standard_horoscope",
      "dob": "1918-10-16",
      "time": "14:20",
      "lat": 12.9716,
      "lon": 77.5946,
      "timezone": "Asia/Kolkata",
      "utc": "1918-10-16T08:50:00Z",
      "published": {
        "lagna_sign": "Capricorn",
        "lagna_degree_in_sign": 24.95,
        "lagna_nakshatra": "Dhanishta",
        "moon_pada": 1,
        "nakshatras": {
          "Sun": "Chitra",
          "Moon": "Shatabhisha",
          "Mars": "Jyeshtha",
          "Mercury": "Chitra",
          "Jupiter": "Punarvasu",
          "Venus": "Hasta",
          "Saturn": "Magha"
        }
      },
      "horizons_tropical": {
        "Sun": 202.1845834,
        "Moon": 332.4948776,
        "Mercury": 202.7810033,
        "Venus": 192.4234890,
        "Mars": 250.7324011,
        "Jupiter": 105.2850896,
        "Saturn": 145.6532866
      }
    },
    {
      "name": "mumbai_1995",
      "dob": "1995-06-15",
      "time": "14:30",
      "lat": 19.076,
      "lon": 72.8777,
      "timezone": "Asia/Kolkata",
      "utc": "1995-06-15T09:00:00Z",
      "published": null,
      "horizons_tropical": {
        "Sun": 83.8128573,
        "Moon": 295.1410738,
        "Mercury": 69.9484343,
        "Venus": 65.7141188,
        "Mars": 160.0358036,
        "Jupiter": 248.7822821,
        "Saturn": 354.385667
      }
    },
    {
      "name": "delhi_1975",
      "dob": "1975-01-15",
      "time": "09:00",
      "lat": 28.6139,
      "lon": 77.209,
      "timezone": "Asia/Kolkata",
      "utc": "1975-01-15T03:30:00Z",
      "published": null,
      "horizons_tropical": {
        "Sun": 294.3523075,
        "Moon": 324.1227873,
        "Mercury": 310.0250771,
        "Venus": 311.115035,
        "Mars": 265.1662979,
        "Jupiter": 345.8754805,
        "Saturn": 104.7108862
      }
    }
  ]
}
```

- [ ] **Step 2: Write the tests**

```python
# tests/test_gold_corpus.py
import datetime
import json
from pathlib import Path

import pytest

import dashaflow
from dashaflow.constants import NAK_SPAN, VIMSHOTTARI_YEARS, ZODIAC_SIGNS
from dashaflow.dasha import SIDEREAL_YEAR_DAYS

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "gold_charts.json").read_text())
CHARTS = FIXTURE["charts"]


def _cast(entry, ayanamsha="lahiri"):
    return dashaflow.cast_chart(
        entry["dob"], entry["time"], entry["lat"], entry["lon"],
        entry["timezone"], ayanamsha=ayanamsha)


def _sidereal_absolute(planet):
    return ZODIAC_SIGNS.index(planet["sign"]) * 30 + planet["degree_precise"]


@pytest.mark.parametrize("entry", CHARTS, ids=lambda e: e["name"])
def test_planets_match_horizons(entry):
    chart = _cast(entry)
    aya = chart["metadata"]["ayanamsha_degrees"]
    for name, tropical in entry["horizons_tropical"].items():
        delta = (_sidereal_absolute(chart["planets"][name]) + aya - tropical + 180) % 360 - 180
        assert abs(delta) <= 0.05, f"{entry['name']} {name}: {delta:+.4f} deg"


def test_ayanamsha_j2000_pin():
    chart = dashaflow.cast_chart(
        "2000-01-01", "12:00", 28.6139, 77.2090, "UTC")
    # Installed backend: 23.857092; report pin: 23.853222; rung absorbs the 0.0039 gap.
    assert abs(chart["metadata"]["ayanamsha_degrees"] - 23.853222) <= 0.02


@pytest.mark.parametrize("entry", CHARTS, ids=lambda e: e["name"])
def test_categorical_anchors(entry):
    chart = _cast(entry)
    published = entry["published"] or {}
    if "lagna_sign" in published:
        assert chart["lagna"]["sign"] == published["lagna_sign"]
        assert abs(chart["lagna"]["degree"] - published["lagna_degree_in_sign"]) <= 0.50
    if "lagna_nakshatra" in published:
        assert chart["lagna"]["nakshatra"] == published["lagna_nakshatra"]
    if "moon_pada" in published:
        assert chart["planets"]["Moon"]["pada"] == published["moon_pada"]
    for planet, nakshatra in published.get("nakshatras", {}).items():
        assert chart["planets"][planet]["nakshatra"] == nakshatra


def test_variant_metadata_rung():
    entry = next(e for e in CHARTS if e["name"] == "delhi_1975")
    lahiri = _cast(entry)["metadata"]
    raman = _cast(entry, ayanamsha="raman")["metadata"]
    assert raman["ayanamsha_variant"] == "raman"
    assert raman["ayanamsha"] == "Raman"
    assert raman["ayanamsha_degrees"] != lahiri["ayanamsha_degrees"]


def test_raman_shift_matches_ayanamsha_difference():
    entry = next(e for e in CHARTS if e["name"] == "delhi_1975")
    lahiri = _cast(entry)
    raman = _cast(entry, ayanamsha="raman")
    moon_delta = (_sidereal_absolute(raman["planets"]["Moon"])
                  - _sidereal_absolute(lahiri["planets"]["Moon"])) % 360
    # Raman's ayanamsha is smaller, so its sidereal longitudes sit ahead.
    assert abs(moon_delta - 1.4463) < 0.01


def test_separation_guards():
    entry = next(e for e in CHARTS if e["name"] == "raman_standard_horoscope")
    lahiri = _cast(entry)["metadata"]["ayanamsha_degrees"]
    raman = _cast(entry, ayanamsha="raman")["metadata"]["ayanamsha_degrees"]
    icrc = _cast(entry, ayanamsha="lahiri_icrc")["metadata"]["ayanamsha_degrees"]
    citra = _cast(entry, ayanamsha="true_citra")["metadata"]["ayanamsha_degrees"]
    assert abs(lahiri - raman) >= 1.0
    assert abs(lahiri - icrc) <= 0.01
    assert abs(lahiri - citra) <= 0.05


@pytest.mark.parametrize("entry", CHARTS, ids=lambda e: e["name"])
def test_vimshottari_formula_invariant(entry):
    chart = _cast(entry)
    moon = chart["planets"]["Moon"]
    timeline = chart["dashas"]["timeline"]
    lord = moon["nakshatra_lord"]
    assert timeline[0]["planet"] == lord

    moon_abs = _sidereal_absolute(moon)
    nak_idx = int(moon_abs / NAK_SPAN)
    remaining = 1 - (moon_abs - nak_idx * NAK_SPAN) / NAK_SPAN
    expected_days = VIMSHOTTARI_YEARS[lord] * SIDEREAL_YEAR_DAYS * remaining
    actual_days = (
        datetime.date.fromisoformat(timeline[0]["end"])
        - datetime.date.fromisoformat(timeline[0]["start"])).days
    assert abs(actual_days - expected_days) <= 1.0

    for earlier, later in zip(timeline, timeline[1:]):
        assert earlier["end"] == later["start"]
```

- [ ] **Step 3: Run the tests**

Run: `python -m pytest tests/test_gold_corpus.py --junitxml=/tmp/opencode/t6.xml`
Expected: PASS. If a planet rung misses, the fixture or the engine is wrong — do not loosen the 0.05° rung.

- [ ] **Step 4: Add the one-time generator**

Create `tests/fixtures/generate_gold.py` using stdlib `urllib.request` and `pytz` (already a dependency). It must:

- convert each chart's local birth time to UTC and confirm it matches the stored
  `utc` field;
- call `https://ssd.jpl.nasa.gov/api/horizons.api` with
  `COMMAND` = one of `10, 301, 199, 299, 499, 599, 699` for Sun..Saturn,
  `CENTER='500@399'`, `EPHEM_TYPE='OBSERVER'`, `QUANTITIES='31'`,
  `CSV_FORMAT='YES'`, `EXTRA_PREC='YES'`, `ANG_FORMAT='DEG'`,
  `START_TIME`/`STOP_TIME` a one-minute window at the UTC instant;
- parse the first row between `$$SOE` and `$$EOE` and read CSV column index 3
  (date, blank, blank, longitude, latitude);
- rewrite `gold_charts.json` preserving the `published` blocks, using
  `json.dump(..., indent=2, sort_keys=False)` plus a trailing newline. Keep
  numeric literals free of trailing zeros so a regenerate is text-identical.

The test suite must never import or run it.

- [ ] **Step 5: Run the generator once and re-run the tests**

Run: `python tests/fixtures/generate_gold.py && git diff --exit-code tests/fixtures/gold_charts.json`
Expected: no diff — the committed values reproduce from Horizons.

Run: `python -m pytest tests/test_gold_corpus.py --junitxml=/tmp/opencode/t6.xml`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/gold_charts.json tests/fixtures/generate_gold.py tests/test_gold_corpus.py
git commit -m "test: add JPL Horizons gold corpus with tolerance ladder"
```

---

### Task 7: MCP ayanamsha plumbing

**Files:**
- Modify: `/home/adarsh/cursorProjects/rishi-ai-mcp/rishi_ai_mcp.py`
- Modify: `/home/adarsh/cursorProjects/rishi-ai-mcp/system_prompt.md`
- Test: `/home/adarsh/cursorProjects/rishi-ai-mcp/test_rishi_ai_mcp.py`

**Interfaces:**
- Consumes: dashaflow 1.5.0 (`cast_chart`, `cast_transit`, `get_time_sensitivity`, and the three workbench getters all accept `ayanamsha`).
- Produces: all 12 MCP tools gain `ayanamsha: str = "lahiri"` as their last parameter.

- [ ] **Step 1: Create the branch and write the failing tests**

From `/home/adarsh/cursorProjects/rishi-ai-mcp`:

```bash
git checkout -b feature/correctness-lock
```

Append to `test_rishi_ai_mcp.py`:

```python
class TestAyanamshaVariants(unittest.TestCase):
    BIRTH = ("1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")

    def test_compact_chart_names_variant(self):
        result = cast_vedic_chart(*self.BIRTH, ayanamsha="raman")
        self.assertEqual(result["ayanamsha_variant"], "raman")
        self.assertEqual(result["planets"]["Moon"]["sign"], "Sagittarius")

    def test_invalid_variant_is_tool_error(self):
        from mcp.server.fastmcp.exceptions import ToolError
        with self.assertRaises(ToolError):
            cast_vedic_chart(*self.BIRTH, ayanamsha="nope")

    def test_all_tools_accept_ayanamsha(self):
        import asyncio
        import rishi_ai_mcp
        tools = asyncio.run(rishi_ai_mcp.mcp.list_tools())
        self.assertEqual(len(tools), 12)
        for tool in tools:
            self.assertIn("ayanamsha", tool.inputSchema["properties"], tool.name)

    def test_gochara_variant_changes_reference(self):
        from rishi_ai_mcp import get_gochara_tool
        common = dict(dob=self.BIRTH[0], time=self.BIRTH[1], lat=self.BIRTH[2],
                      lon=self.BIRTH[3], timezone=self.BIRTH[4],
                      transit_date="2026-06-02")
        self.assertEqual(get_gochara_tool(**common)["natal_moon_sign"], "Scorpio")
        self.assertEqual(
            get_gochara_tool(**common, ayanamsha="raman")["natal_moon_sign"],
            "Sagittarius")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest test_rishi_ai_mcp.py -k "Ayanamsha" --junitxml=/tmp/opencode/t7.xml`
Expected: FAIL — tools reject `ayanamsha`.

- [ ] **Step 3: Implement**

For each of the 12 tools, append `ayanamsha: str = "lahiri"` after the last parameter and
pass it to the dashaflow call it wraps:

| Tool | Change |
|---|---|
| `cast_vedic_chart` | `cast_chart(..., ayanamsha=ayanamsha)`; `get_time_sensitivity(..., ayanamsha=ayanamsha)` |
| `cast_transit_chart` | `cast_transit(..., ayanamsha=ayanamsha)` |
| `get_transit_ingresses_tool` | pass `ayanamsha=ayanamsha` |
| `get_sade_sati_timeline_tool` | pass `ayanamsha=ayanamsha` |
| `get_gochara_tool` | pass `ayanamsha=ayanamsha` |
| `get_dasha_periods_tool` | `cast_chart(..., ayanamsha=ayanamsha)` |
| `get_strength_table_tool` | `cast_chart(..., ayanamsha=ayanamsha)` |
| `get_time_sensitivity_tool` | `get_time_sensitivity(..., ayanamsha=ayanamsha)` |
| `get_yoga_list_tool` | `cast_chart(..., ayanamsha=ayanamsha)` |
| `calculate_compatibility_tool` | pass one shared `ayanamsha` |
| `check_muhurtha_tool` | pass `ayanamsha=ayanamsha` |
| `analyze_career_chart` | pass `ayanamsha=ayanamsha` |

Add this line to each docstring's Parameters block:

```
        ayanamsha: One of lahiri (default), lahiri_icrc, true_citra, raman,
            krishnamurti, krishnamurti_vp291, yukteshwar, fagan_bradley.
```

In `system_prompt.md`:

- Line 8: change "(Sidereal Lahiri)" to "(sidereal; Lahiri is the default variant)".
- Line 30: change "ayanamsha (Lahiri), ayanamsha degrees" to
  "ayanamsha (display name), ayanamsha_variant, ayanamsha degrees".
- Line 106: change the quoted sentence to
  `*"Let me cast your Vedic chart using <variant> ayanamsha..."*` and add:
  `Use Lahiri unless the user explicitly names another system; pass the same ayanamsha to every tool in the turn and state the variant in the answer. Use KP ayanamsha only when the user asks for KP/sub-lord analysis.`

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest test_rishi_ai_mcp.py --junitxml=/tmp/opencode/t7.xml`
Expected: all pass (37 existing + new tests).

- [ ] **Step 5: Commit**

```bash
git add rishi_ai_mcp.py system_prompt.md test_rishi_ai_mcp.py
git commit -m "feat: expose ayanamsha variant on all MCP tools"
```

---

### Task 8: Release dashaflow 1.5.0

**Files:**
- Modify: `src/dashaflow/_version.py`
- Modify: `CHANGELOG.md`
- Test: full suite

**Interfaces:**
- Produces: PyPI `dashaflow==1.5.0` and git tag `v1.5.0`.

- [ ] **Step 1: Bump version and changelog**

Set `__version__ = "1.5.0"` in `src/dashaflow/_version.py`. Add at the top of `CHANGELOG.md`:

```markdown
## [1.5.0] - 2026-11-07

### Added
- Ayanamsha variant parameter on every casting function: `lahiri` (default), `lahiri_icrc`, `true_citra`, `raman`, `krishnamurti`, `krishnamurti_vp291`, `yukteshwar`, `fagan_bradley`; aliases are accepted and unknown values raise `InvalidInputError`. Chart metadata gains `ayanamsha_variant`, and compact summaries name the variant.
- JPL Horizons DE441 gold corpus with the ayanamsha/planet/ascendant/nakshatra/dasha tolerance ladder.

### Changed
- `ephemeris_accuracy` now derives from the backend flags actually returned. A default install without `.se1` files reports reduced (Moshier) accuracy instead of claiming full.
- Transit scans read the variant from natal chart metadata and re-assert the sidereal mode inside every locked `calc_ut`.

### Fixed
- Silent Moshier substitution now logs once per process.
```

- [ ] **Step 2: Run the full local gate**

```bash
python -m pytest tests/ --junitxml=/tmp/opencode/t8.xml
python -m ruff check src tests
```

Expected: 0 failures/errors; ruff clean. Parse the XML count and compare against the 378-test baseline plus new tests.

- [ ] **Step 3: Commit and open the PR**

```bash
git add src/dashaflow/_version.py CHANGELOG.md
git commit -m "chore(release): 1.5.0"
git push -u origin feature/correctness-lock
gh pr create --base main --head feature/correctness-lock \
  --title "Correctness lock: ayanamsha variants, gold corpus, wrapper hardening" \
  --body "Implements docs/superpowers/specs/2026-11-07-correctness-lock-design.md. Adds the eight-variant ayanamsha allowlist and metadata, the JPL Horizons gold corpus, flag-derived ephemeris accuracy, and transit variant re-assertion."
gh pr checks --watch
```

- [ ] **Step 4: Merge and tag**

```bash
PR=$(gh pr view --json number -q .number)
gh pr merge "$PR" --admin --merge
git checkout main && git pull
gh release create v1.5.0 --title "dashaflow 1.5.0" \
  --notes "Correctness lock: ayanamsha variants, JPL gold corpus, ephemeris wrapper hardening."
```

Approve the `pypi` environment deployment in the GitHub UI when the publish workflow pauses.

- [ ] **Step 5: Verify the published wheel**

```bash
python -m venv /tmp/opencode/df150
/tmp/opencode/df150/bin/pip install --no-cache-dir dashaflow==1.5.0
/tmp/opencode/df150/bin/python - <<'EOF'
import dashaflow
chart = dashaflow.cast_chart("1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
                             ayanamsha="raman")
assert chart["metadata"]["ayanamsha_variant"] == "raman"
assert chart["planets"]["Moon"]["sign"] == "Sagittarius"
print("dashaflow", dashaflow.__version__, "ok")
EOF
```

Expected: prints `dashaflow 1.5.0 ok`. If PyPI has not propagated yet, retry after a minute.

---

### Task 9: Release rishi-ai-mcp 1.5.0

**Files:**
- Modify: `/home/adarsh/cursorProjects/rishi-ai-mcp/rishi_ai_mcp.py`
- Modify: `/home/adarsh/cursorProjects/rishi-ai-mcp/pyproject.toml`
- Modify: `/home/adarsh/cursorProjects/rishi-ai-mcp/CHANGELOG.md`
- Test: full rishi suite

**Interfaces:**
- Produces: PyPI `rishi-ai-mcp==1.5.0` pinning `dashaflow>=1.5.0,<2.0.0`.

- [ ] **Step 1: Bump version, floor, and changelog**

- `rishi_ai_mcp.py`: `__version__ = "1.5.0"`.
- `pyproject.toml`: `"dashaflow>=1.5.0,<2.0.0"`.
- `CHANGELOG.md` top entry:

```markdown
## [1.5.0] - 2026-11-07

### Added
- `ayanamsha` parameter on all 12 tools: `lahiri` (default), `lahiri_icrc`, `true_citra`, `raman`, `krishnamurti`, `krishnamurti_vp291`, `yukteshwar`, `fagan_bradley`.
- Compact `cast_vedic_chart` output names the active variant.
- `system_prompt.md` routing rule: Lahiri unless the user names a system; state the variant; KP only with sub-lord analysis.

### Changed
- Requires `dashaflow>=1.5.0`.
```

- [ ] **Step 2: Run the full local gate**

```bash
cd /home/adarsh/cursorProjects/rishi-ai-mcp
python -m pytest -q --junitxml=/tmp/opencode/t9.xml
```

Expected: all pass, including the 12-tool count and variant tests.

- [ ] **Step 3: Commit and open the PR**

```bash
git add rishi_ai_mcp.py pyproject.toml CHANGELOG.md
git commit -m "chore(release): 1.5.0"
git push -u origin feature/correctness-lock
gh pr create --base main --head feature/correctness-lock \
  --title "Ayanamsha variants on all tools" \
  --body "Exposes dashaflow 1.5.0 ayanamsha variants on all 12 tools, names the variant in compact output, and updates the system prompt routing contract."
gh pr checks --watch
```

- [ ] **Step 4: Merge, tag, and verify**

```bash
PR=$(gh pr view --json number -q .number)
gh pr merge "$PR" --admin --merge
git checkout main && git pull
gh release create v1.5.0 --title "rishi-ai-mcp 1.5.0" \
  --notes "Ayanamsha variants on all 12 tools; dashaflow>=1.5.0."
```

Approve the `pypi` environment deployment when prompted. Then:

```bash
python -m venv /tmp/opencode/rishi150
/tmp/opencode/rishi150/bin/pip install --no-cache-dir rishi-ai-mcp==1.5.0
/tmp/opencode/rishi150/bin/python - <<'EOF'
import asyncio
import rishi_ai_mcp
from rishi_ai_mcp import cast_vedic_chart

tools = asyncio.run(rishi_ai_mcp.mcp.list_tools())
assert len(tools) == 12
assert all("ayanamsha" in t.inputSchema["properties"] for t in tools)
chart = cast_vedic_chart("1990-04-15", "14:30", 28.6139, 77.2090,
                         "Asia/Kolkata", ayanamsha="raman")
assert chart["ayanamsha_variant"] == "raman"
assert chart["planets"]["Moon"]["sign"] == "Sagittarius"
print("rishi-ai-mcp", rishi_ai_mcp.__version__, "ok")
EOF
```

Expected: prints `rishi-ai-mcp 1.5.0 ok`.
