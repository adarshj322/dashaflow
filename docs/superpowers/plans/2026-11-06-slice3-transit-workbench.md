# Slice 3 — Transit Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship dashaflow 1.4.0 and rishi-ai-mcp 1.4.0 with three timing getters: sign ingresses, a retro-aware Sade Sati timeline, and SAV-weighted gochara.

**Architecture:** A new `src/dashaflow/transit.py` holds the scan/bisection engine, span builder, and gochara table. Public functions are re-exported from `__init__.py`; gochara reuses `calculate_transit()` rather than duplicating ephemeris code. MCP wraps each getter 1:1.

**Tech Stack:** Python 3.10+, pyswisseph, pytz, pytest, ruff, hatchling. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-11-06-slice3-transit-workbench-design.md`

## Global Constraints

- Range cap: **15 years**; longer or reversed ranges raise `InvalidInputError`.
- Ingress precision: bisection to **≤ 60 seconds**; `instant_utc` minute precision.
- Sampling: 1 day for Sun/Mars/Mercury/Venus; 5 days for Jupiter/Saturn/Rahu/Ketu.
- All Swiss Ephemeris access under `_SWE_LOCK` per call, never across a whole scan.
- Lahiri ayanamsha, existing `_configure_swiss_ephemeris('')` behavior.
- Backward compatibility: `cast_transit`, `calculate_transit`, and their outputs unchanged.
- Engine version `1.4.0`; MCP floor `dashaflow>=1.4.0,<2.0.0`; MCP version `1.4.0`.
- Local checks: `python -m pytest tests/ --junitxml=<file>` (parse testsuite counts; pytest 9 prints "No tests collected" misleadingly) and `python -m ruff check src tests`.
- Branch: `feature/slice3-transit-workbench` (design doc already committed).

## Review Focus

- A query that starts inside an active Sade Sati span must show `starts_before_range` and `active_at_start`, not a fake ingress date.
- A Saturn retrograde crossing the Sade Sati boundary must appear in `crossings` and produce separate spans, never be silently absorbed.
- Ingress local date can differ from the UTC date (Jupiter Cancer: 2026-06-01T20:20Z = 2026-06-02 IST); tests pin the local date.
- Reversed/over-long ranges, unknown bodies, and Moon requests must raise `InvalidInputError`, not scan forever.
- Node gochara notes must say `Raman convention (nodes)`; classical planets must not.

---

### Task 1: Ingress core and `get_transit_ingresses`

**Files:**
- Create: `src/dashaflow/transit.py`
- Modify: `src/dashaflow/__init__.py` (import + `__all__`)
- Test: `tests/test_transit_workbench.py`

**Interfaces:**
- Consumes: `constants.PLANETS`, `constants.ZODIAC_SIGNS`, `vedic_calculator._SWE_LOCK`, `vedic_calculator._configure_swiss_ephemeris`, `vedic_calculator.get_sign_and_degree`, `vedic_calculator.calculate_vedic_chart`, `_validation.validate_birth_input`, `_validation.validate_query_date`, `errors.InvalidInputError`.
- Produces:
  ```python
  def get_transit_ingresses(dob: str, time: str, lat: float, lon: float,
                            timezone: str, start_date: str, end_date: str,
                            bodies: list[str] | None = None) -> dict
  ```

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_transit_workbench.py
import datetime
import pytest
import dashaflow
from dashaflow.errors import InvalidInputError

DEMO = dict(dob="1990-04-15", time="14:30", lat=28.6139, lon=77.2090,
            timezone="Asia/Kolkata")

def test_saturn_ingress_anchor_aquarius():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2023-01-01", end_date="2023-02-01",
        bodies=["Saturn"])
    ev = [e for e in out["ingresses"] if e["to_sign"] == "Aquarius"]
    assert len(ev) == 1
    assert ev[0]["from_sign"] == "Capricorn"
    assert ev[0]["date"] in ("2023-01-16", "2023-01-17", "2023-01-18")
    assert ev[0]["house_from_lagna"] == 7
    assert ev[0]["house_from_moon"] == 4

def test_ingress_self_consistency():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2023-01-01", end_date="2025-01-01",
        bodies=["Jupiter", "Saturn", "Rahu"])
    assert out["ingresses"] == sorted(out["ingresses"], key=lambda e: (e["instant_utc"], e["planet"]))
    assert all(e["from_sign"] != e["to_sign"] for e in out["ingresses"])

def test_retrograde_reentry_present():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2022-04-01", end_date="2023-02-01",
        bodies=["Saturn"])
    assert any(e["direction"] == "retrograde" for e in out["ingresses"])

def test_ketu_mirrors_rahu():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2023-01-01", end_date="2025-01-01",
        bodies=["Rahu", "Ketu"])
    rahu = [e for e in out["ingresses"] if e["planet"] == "Rahu"]
    ketu = [e for e in out["ingresses"] if e["planet"] == "Ketu"]
    assert len(rahu) == len(ketu)
    for r, k in zip(rahu, ketu):
        assert r["instant_utc"] == k["instant_utc"]
        assert k["direction"] == "retrograde"

def test_ingress_local_date_across_utc_midnight():
    out = dashaflow.get_transit_ingresses(
        **DEMO, start_date="2026-05-25", end_date="2026-06-10",
        bodies=["Jupiter"])
    ev = [e for e in out["ingresses"] if e["to_sign"] == "Cancer"][0]
    assert ev["instant_utc"].startswith("2026-06-01T20:")
    assert ev["date"] == "2026-06-02"

@pytest.mark.parametrize("kwargs", [
    dict(start_date="2023-02-01", end_date="2023-01-01"),
    dict(start_date="2000-01-01", end_date="2020-01-01"),
    dict(start_date="2023-01-01", end_date="2023-02-01", bodies=["Moon"]),
    dict(start_date="2023-01-01", end_date="2023-02-01", bodies=["Pluto"]),
])
def test_ingress_validation(kwargs):
    with pytest.raises(InvalidInputError):
        dashaflow.get_transit_ingresses(**DEMO, **kwargs)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_transit_workbench.py -q`
Expected: FAIL / errors because `dashaflow.get_transit_ingresses` does not exist.

- [ ] **Step 3: Implement the ingress core**

In `transit.py`:

```python
_INGRESS_BODIES = ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_DEFAULT_BODIES = ("Jupiter", "Saturn", "Rahu")
_STEP_DAYS = {"Sun": 1, "Mars": 1, "Mercury": 1, "Venus": 1,
              "Jupiter": 5, "Saturn": 5, "Rahu": 5, "Ketu": 5}
_MAX_RANGE_YEARS = 15
_BISECTION_SECONDS = 60

def get_transit_ingresses(dob, time, lat, lon, timezone,
                          start_date, end_date, bodies=None) -> dict: ...
```

Implementation notes:
- Validate birth input, both dates, body names, range cap (`(end - start).days > 365 * 15 + 5`).
- Range boundaries are **local midnights** in the supplied timezone: localize `start_date` 00:00 and `end_date + 1 day` 00:00, convert to UTC Julian days, and sample between them. `end_date` is inclusive.
- Call `_configure_swiss_ephemeris('')` once at scan start (inside `_SWE_LOCK`), then individual `swe.calc_ut` calls under the lock.
- Ketu longitude = `(Rahu longitude + 180) % 360`; Ketu direction always `retrograde`.
- `_sign_index(jd, body)` compares `int(lon // 30)`.
- `_crossings(start, end, body)`: sample at the computed UTC bounds; bisection returns the true instant. Convert the final JD to UTC with `swe.revjul`, then to the supplied timezone for `date`.
- Bisection predicate is the sign index, never monotonic longitude.
- `direction`: `swe.calc_ut(jd, planet_id, FLG_SIDEREAL | FLG_SPEED)[0][3] < 0`; Sun direct, Rahu/Ketu retrograde.
- Sort by `(instant_utc, planet)`.
- `house_from_lagna`/`house_from_moon` from natal chart signs.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_transit_workbench.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dashaflow/transit.py src/dashaflow/__init__.py tests/test_transit_workbench.py
git commit -m "feat: transit ingress scanner with retrograde re-entries"
```

---

### Task 2: `get_sade_sati_timeline`

**Files:**
- Modify: `src/dashaflow/transit.py`
- Modify: `src/dashaflow/__init__.py`
- Test: `tests/test_transit_workbench.py`

**Interfaces:**
- Consumes: Task 1 `_crossings`, `_sign_index`, `_local_date`, natal chart Moon sign.
- Produces:
  ```python
  def get_sade_sati_timeline(dob: str, time: str, lat: float, lon: float,
                             timezone: str, start_date: str, end_date: str,
                             merge_gap_days: int = 180) -> dict
  ```

- [ ] **Step 1: Write the failing tests**

```python
def test_sade_sati_spans_demo_chart():
    out = dashaflow.get_sade_sati_timeline(
        **DEMO, start_date="2010-01-01", end_date="2022-01-01")
    assert out["natal_moon_sign"] == "Scorpio"
    assert out["active_at_start"] is False
    assert out["active_at_end"] is False
    spans = out["spans"]
    assert spans[0] == {"phase": "rising", "start": "2011-11-15",
                        "end": "2014-11-01", "days": 1083, "gap_days": 80,
                        "in_phase_days": 1003, "interruptions": 1,
                        "starts_before_range": False, "ends_after_range": False}
    assert [s["phase"] for s in spans] == ["rising", "peak", "setting", "peak", "setting"]
    assert spans[-1]["start"] == "2017-10-26"
    assert spans[-1]["end"] == "2020-01-23"

def test_sade_sati_zero_merge_splits_off_gap():
    out = dashaflow.get_sade_sati_timeline(
        **DEMO, start_date="2010-01-01", end_date="2022-01-01",
        merge_gap_days=0)
    rising = [s for s in out["spans"] if s["phase"] == "rising"]
    assert len(rising) == 2
    assert rising[0]["end"] == "2012-05-15"
    assert rising[1]["start"] == "2012-08-04"

def test_sade_sati_clipped_range_flags():
    out = dashaflow.get_sade_sati_timeline(
        **DEMO, start_date="2016-01-01", end_date="2016-12-31")
    span = out["spans"][0]
    assert span["phase"] == "peak"
    assert span["starts_before_range"] is True
    assert span["ends_after_range"] is True
    assert out["active_at_start"] is True
    assert out["active_at_end"] is True

def test_sade_sati_crossings_have_phases():
    out = dashaflow.get_sade_sati_timeline(
        **DEMO, start_date="2017-01-01", end_date="2018-01-01")
    echo = [c for c in out["crossings"] if c["to_phase"] == "peak"]
    assert echo and echo[0]["date"] == "2017-06-21"
    assert echo[0]["from_phase"] == "setting"
    assert echo[0]["direction"] == "retrograde"

def test_sade_sati_negative_merge_gap_rejected():
    with pytest.raises(InvalidInputError):
        dashaflow.get_sade_sati_timeline(
            **DEMO, start_date="2010-01-01", end_date="2011-01-01",
            merge_gap_days=-1)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_transit_workbench.py -q`
Expected: FAIL because the function is missing.

- [ ] **Step 3: Implement the span builder**

- Build Saturn crossings with Task 1's helper.
- Reject `merge_gap_days < 0` with `InvalidInputError`.
- Phase from Moon: `{11: "rising", 0: "peak", 1: "setting"}`, else `off`.
- Emit disjoint segments; `end` is the day before the next change; `days` is inclusive.
- Merge only same-phase segments separated by an `off` gap `<= merge_gap_days`; add `gap_days`, `interruptions`; cross-phase excursions stay separate.
- Set `starts_before_range`/`ends_after_range` when the span edge is the query edge; `active_at_start`/`active_at_end` from the phase at each edge.
- Crossings carry `from_sign`, `to_sign`, `from_phase`, `to_phase`, `direction`, `instant_utc`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_transit_workbench.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dashaflow/transit.py src/dashaflow/__init__.py tests/test_transit_workbench.py
git commit -m "feat: retro-aware Sade Sati timeline with clipped-range flags"
```

---

### Task 3: `get_gochara`

**Files:**
- Modify: `src/dashaflow/transit.py`
- Modify: `src/dashaflow/__init__.py`
- Test: `tests/test_transit_workbench.py`

**Interfaces:**
- Consumes: `calculate_transit` (noon snapshot), natal `ashtakavarga.sarvashtakavarga`.
- Produces:
  ```python
  def get_gochara(dob: str, time: str, lat: float, lon: float,
                  timezone: str, transit_date: str) -> dict
  ```

- [ ] **Step 1: Write the failing tests**

```python
def test_gochara_jupiter_cancer_mixed():
    out = dashaflow.get_gochara(**DEMO, transit_date="2026-06-02")
    jup = out["planets"]["Jupiter"]
    assert jup["house_from_moon"] == 9
    assert jup["sav_points"] == 19
    assert jup["house_quality"] == "favorable"
    assert jup["weighted_verdict"] == "mixed"
    assert out["sav_average"] == 28.08

def test_gochara_saturn_pisces_unfavorable():
    out = dashaflow.get_gochara(**DEMO, transit_date="2026-06-02")
    sat = out["planets"]["Saturn"]
    assert sat["house_from_moon"] == 5
    assert sat["house_quality"] == "unfavorable"
    assert sat["weighted_verdict"] == "unfavorable"

def test_gochara_node_notes_label_raman():
    out = dashaflow.get_gochara(**DEMO, transit_date="2026-06-02")
    assert any("Raman convention (nodes)" in n for n in out["planets"]["Rahu"]["notes"])
    assert all("Raman convention" not in n for n in out["planets"]["Sun"]["notes"])
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_transit_workbench.py -q`
Expected: FAIL because the function is missing.

- [ ] **Step 3: Implement gochara**

- Compute natal chart; call `calculate_transit(transit_date, natal_chart, timezone)`.
- Favourable table: Sun (3,6,10,11), Moon (1,3,6,7,10,11), Mars (3,6,11), Mercury (2,4,6,8,10,11), Jupiter (2,5,7,9,11), Venus (1,2,3,4,5,8,9,11,12), Saturn (3,6,11), Rahu (3,6,11), Ketu (3,6,11).
- `sav_average = round(sum(sav.values()) / 12, 2)`.
- Verdict truth table: favourable+above → `favorable`; favourable+below → `mixed`; unfavourable+above → `mixed`; unfavourable+below → `unfavorable`.
- Notes include the house rule and the SAV comparison; nodes append `Raman convention (nodes)`.
- Include `is_retrograde` per planet from the transit snapshot.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_transit_workbench.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/dashaflow/transit.py src/dashaflow/__init__.py tests/test_transit_workbench.py
git commit -m "feat: SAV-weighted gochara with BPHS table and Raman node labelling"
```

---

### Task 4: Schemas, exports, docs

**Files:**
- Modify: `src/dashaflow/schemas.py`
- Modify: `src/dashaflow/__init__.py` (`__all__` already touched in Tasks 1-3)
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test_schemas.py` or `tests/test_transit_workbench.py`

**Interfaces:**
- Produces: `validate("transit_ingresses" | "sade_sati_timeline" | "gochara", payload)`.

- [ ] **Step 1: Write the failing schema tests**

```python
def test_workbench_schemas_accept_outputs():
    pytest.importorskip("jsonschema")
    from dashaflow.schemas import validate
    ing = dashaflow.get_transit_ingresses(**DEMO, start_date="2023-01-01", end_date="2023-02-01")
    ss = dashaflow.get_sade_sati_timeline(**DEMO, start_date="2010-01-01", end_date="2022-01-01")
    go = dashaflow.get_gochara(**DEMO, transit_date="2026-06-02")
    validate("transit_ingresses", ing)
    validate("sade_sati_timeline", ss)
    validate("gochara", go)
```

- [ ] **Step 2: Run test to verify failure**

Run: `python -m pytest tests/test_transit_workbench.py::test_workbench_schemas_accept_outputs -q`
Expected: FAIL with unknown schema.

- [ ] **Step 3: Add schemas and docs**

- Add three schema dicts to `schemas.py` and register them in `_SCHEMAS`.
- README: add three API-table rows; add a "Transit timing" section with the gochara table, the retrograde caveat, and the Raman node note.
- CHANGELOG `[Unreleased]` section.

- [ ] **Step 4: Run full checks**

Run: `python -m pytest tests/ --junitxml=/tmp/opencode/slice3.xml` then parse testsuite counts; `python -m ruff check src tests`.
Expected: 0 failures/errors; ruff "All checks passed!".

- [ ] **Step 5: Commit**

```bash
git add src/dashaflow/schemas.py README.md CHANGELOG.md tests/test_transit_workbench.py
git commit -m "docs: publish transit workbench schemas and README section"
```

---

### Task 5: Release dashaflow 1.4.0

**Files:**
- Modify: `src/dashaflow/_version.py`, `CHANGELOG.md`

- [ ] **Step 1: Bump and date**

`_version.py` → `"1.4.0"`; `## [Unreleased]` → `## [1.4.0] - 2026-11-06`.

- [ ] **Step 2: Full verification**

`python -m pytest tests/ --junitxml=/tmp/opencode/rel14.xml` (parse counts), `python -m ruff check src tests`, `python -m build --wheel`.
Expected: 0 failures; ruff clean; wheel `dashaflow-1.4.0`.

- [ ] **Step 3: Commit, push, PR, merge, tag, publish**

```bash
git add src/dashaflow/_version.py CHANGELOG.md
git commit -m "chore(release): 1.4.0"
git push origin feature/slice3-transit-workbench
gh pr create --base main --head feature/slice3-transit-workbench ...
gh pr merge <n> --admin --merge
git checkout main && git pull --ff-only
gh release create v1.4.0 --target main ...
```

Approve the `pypi` environment via the pending_deployments API, wait for the publish job, verify `https://pypi.org/pypi/dashaflow/json` reports 1.4.0, then clean-venv install.

- [ ] **Step 4: Commit nothing further; record release URL**

---

### Task 6: MCP tools

**Files:**
- Modify: `rishi_ai_mcp.py`
- Modify: `test_rishi_ai_mcp.py`
- Modify: `system_prompt.md`
- Modify: `pyproject.toml` (`dashaflow>=1.4.0,<2.0.0`)

**Interfaces:**
- Consumes: dashaflow 1.4.0 getters.
- Produces: `get_transit_ingresses_tool`, `get_sade_sati_timeline_tool`, `get_gochara_tool`.

- [ ] **Step 1: Write failing MCP tests**

```python
async def test_tool_count_12():
    tools = await rishi_ai_mcp.mcp.list_tools()
    assert len(tools) == 12

def test_ingress_tool_shape():
    out = rishi_ai_mcp.get_transit_ingresses_tool(
        dob="1990-04-15", time="14:30", lat=28.6139, lon=77.2090,
        timezone="Asia/Kolkata", start_date="2023-01-01", end_date="2023-02-01")
    assert out["ingresses"][0]["to_sign"] == "Aquarius"

def test_gochara_tool_shape():
    out = rishi_ai_mcp.get_gochara_tool(
        dob="1990-04-15", time="14:30", lat=28.6139, lon=77.2090,
        timezone="Asia/Kolkata", transit_date="2026-06-02")
    assert out["planets"]["Jupiter"]["weighted_verdict"] == "mixed"

def test_workbench_tool_error_maps_to_tool_error():
    with pytest.raises(ToolError):
        rishi_ai_mcp.get_sade_sati_timeline_tool(
            dob="1990-04-15", time="14:30", lat=28.6139, lon=77.2090,
            timezone="Asia/Kolkata", start_date="2023-02-01", end_date="2023-01-01")
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest test_rishi_ai_mcp.py -q`
Expected: FAIL because the tools are missing.

- [ ] **Step 3: Implement the three tools**

Thin wrappers with `try/except Exception as e: _raise(e)`, docstrings listing output keys, and this `system_prompt.md` timing paragraph: "For 'when does X change sign' use `get_transit_ingresses_tool`; for Sade Sati periods use `get_sade_sati_timeline_tool`; for transit quality use `get_gochara_tool`. Keep `cast_transit_chart` for a single-date snapshot." Bump the floor in `pyproject.toml`.

- [ ] **Step 4: Run MCP checks**

Run: `python -m pytest test_rishi_ai_mcp.py --junitxml=/tmp/opencode/mcp-slice3.xml`; `python -m ruff check --select F,E9 rishi_ai_mcp.py test_rishi_ai_mcp.py`.
Expected: 37 tests, 0 failures; ruff clean.

- [ ] **Step 5: Commit**

```bash
git add rishi_ai_mcp.py test_rishi_ai_mcp.py system_prompt.md pyproject.toml
git commit -m "feat: transit workbench MCP tools"
```

---

### Task 7: Release rishi-ai-mcp 1.4.0

**Files:**
- Modify: `rishi_ai_mcp.py` (`__version__`), `CHANGELOG.md`

- [ ] **Step 1: Bump, date, verify, wheel build**

Mirror Task 5 with `__version__ = "1.4.0"` and `## [1.4.0] - 2026-11-06`.

- [ ] **Step 2: PR, CI, merge, tag, publish, approve, verify**

Same flow as Task 5. Wait for PyPI to serve 1.4.0 (the simple-index CDN can lag ~10 min; re-run failed CI if pip cannot see it), then clean-venv verify: 12 tools, `run_prompt` still works, all three workbench tools return shapes.

- [ ] **Step 3: Clean up branches**

Delete `feature/slice3-transit-workbench` after merge.
