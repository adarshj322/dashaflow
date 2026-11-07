# Correctness Lock — Design (v1.5.0)

- **Status:** approved; correctness-only trim applied 2026-11-07
- **Date:** 2026-11-07
- **Scope:** dashaflow 1.4.1 → 1.5.0; rishi-ai-mcp 1.4.0 → 1.5.0
- **Source:** final research report §1, §4, §5; roadmap rows 1, 2, 4
- **Supersedes:** nothing. Extends every casting function additively.

## 1. Intent

The ayanamsha variant decision moves planets by up to 1.446°, while the ephemeris
kernel reproduces JPL to 0.001 arcsec — a gap of four to seven orders of
magnitude. Today the engine hardcodes Lahiri (`vedic_calculator.py:60`), the
wrapper discards ephemeris return flags so a Moshier substitution is silent.

This release locks correctness first: make the variant an explicit, validated
choice; add the gold corpus and tolerance ladder that can prove a future change
did not move numbers; harden the ephemeris wrapper so silent substitution is
logged. No new astrological features.

## 2. Goals

- **G1** A validated ayanamsha allowlist parameter on every casting function,
  Lahiri default, with variant + degrees + ephemeris version in chart metadata.
- **G2** A three-entry gold corpus from published oracles plus the tolerance
  ladder (ayanamsha ±0.02°, planets ±0.05°, ascendant ±0.50°, dasha ±1 day).
- **G3** Wrapper hardening: first-call ephemeris-flag check, lock-held
  re-assertion of path + sidereal mode, forced-Moshier and arctic regression
  tests.
- **G4** Backward compatibility: existing calls unchanged, SAV=337 intact,
  tool count stays 12.
- **G5** Ship dashaflow 1.5.0 and rishi-ai-mcp 1.5.0.

## 3. Non-goals

- The pysweph strangler swap (row 3), bounded cache (row 6), process pool
  (row 8), schema consolidation (row 7), property tests (row 5), coverage/eval/
  token CI (row 9), trusted publishing (row 10).
- Changing the default ayanamsha; Lahiri stays the default.
- Per-node ayanamsha options; Ketu remains mean Rahu + 180°.
- New MCP tools or a composite tool; the surface stays at 12.
- Free-form user-supplied ayanamsha constants.
- Pre-cast reuse (`base_chart` on `get_time_sensitivity`, row 0) — deferred.
- The `serr` 3-tuple logging seam — deferred to the row 3 backend swap; on
  pyswisseph 2.10.03 every call returns a 2-tuple.

## 4. Anti-goals

- Silently accepting an unknown variant or a free-form constant.
- Casting with one variant and transiting with another.
- Generating gold values from dashaflow itself; self-generated goldens assert
  nothing.
- Holding `_SWE_LOCK` for a whole transit scan.
- Claiming the deferred `serr` seam fixes the upstream 2-tuple hole — row 3
  activates it; the flag check is what catches Moshier today.
- Changing `"ayanamsha": "Lahiri"` metadata for default calls.

## 5. Constraints

- Python 3.10+, `pyswisseph` 2.10.03, Lahiri default.
- Additive keyword arguments only; existing positional order preserved.
- Every ephemeris touch under `_SWE_LOCK`; path and sidereal mode re-asserted
  inside the lock.
- Gold fixtures from published oracles, never the engine.
- Engine and server released separately; rishi pins
  `dashaflow>=1.5.0,<2.0.0`.

## 6. Approaches considered

### 6.1 Variant exposure

**A — explicit `ayanamsha` keyword on every casting function (chosen).** The
variant is scoped to one call, visible in metadata, and testable in isolation.

**B — module-level `set_ayanamsha()` global setter.** Rejected: hidden
process-wide state, a new thread hazard, and an agent cannot scope a variant to
one chart without racing another request.

**C — only `cast_chart` and the main MCP tool.** Rejected: every drill-down tool
recasts independently, so a Raman chart would silently become Lahiri on the
second call.

### 6.2 Sensitivity reuse (deferred — row 0)

Deferred in the correctness-only trim. The rationale is preserved for the
row-0 follow-up.

**A — `base_chart` keyword on `get_time_sensitivity` (chosen).** Additive,
public, and directly testable by call count.

**B — private helper imported by the server.** Rejected: the server would depend
on a private symbol or duplicate the diff logic.

**C — cache the base chart.** Rejected: row 6 is gated; this change is waste
removal, not caching.

### 6.3 Allowlist breadth

The report's prose lists seven variants and omits Yukteshwar, while its measured
table includes it at a 1.378° offset. **Eight measured variants are chosen** —
dropping a variant after measuring it is arbitrary, and each gets a separation
guard. Say so at approval if you want it out.

## 7. Engine API

### 7.1 Variant table

Canonical keys, display names, and the installed backend's measured offset from
Lahiri at the same Julian day:

| Key | Display | SIDM | Offset vs Lahiri |
|---|---|---|---|
| `lahiri` | Lahiri | `SIDM_LAHIRI` | 0 |
| `lahiri_icrc` | Lahiri-ICRC | `SIDM_LAHIRI_ICRC` | −0.0003° |
| `true_citra` | True Citra | `SIDM_TRUE_CITRA` | −0.0171° |
| `raman` | Raman | `SIDM_RAMAN` | −1.4463° |
| `krishnamurti` | Krishnamurti (KP old) | `SIDM_KRISHNAMURTI` | −0.0969° |
| `krishnamurti_vp291` | Krishnamurti VP291 (KP new) | `SIDM_KRISHNAMURTI_VP291` | −0.0767° |
| `yukteshwar` | Yukteshwar | `SIDM_YUKTESHWAR` | −1.3783° |
| `fagan_bradley` | Fagan-Bradley | `SIDM_FAGAN_BRADLEY` | +0.8832° |

Aliases normalize case, spaces, and hyphens: `icrc`, `true_chitra`, `kp`,
`kp_old`, `kp_new`, `kp_vp291`, `yukteshvara`, `fagan-bradley`.

Measured fact to pin in the corpus test: the installed backend gives Lahiri
**23.857092°** at JD 2451545.0, while the report's constant pin is
**23.853222°**. The 0.0039° difference is inside the ±0.02° rung. The test
asserts the rung and records the measured value so a dependency bump that moves
it is visible.

### 7.2 Signatures (new arguments last)

```python
calculate_vedic_chart(..., ephe_path='', ayanamsha="lahiri")
cast_chart(..., ephe_path='', ayanamsha="lahiri")
cast_charts(births, query_date=None, ephe_path='', max_workers=4, ayanamsha="lahiri")
cast_transit(..., timezone="Asia/Kolkata", ayanamsha="lahiri")
calculate_compatibility(..., ayanamsha="lahiri")          # one variant, both charts
check_muhurtha(..., ayanamsha="lahiri")
analyze_career(..., ayanamsha="lahiri")
get_time_sensitivity(..., ephe_path='', ayanamsha="lahiri")
get_transit_ingresses(..., bodies=None, ayanamsha="lahiri")
get_sade_sati_timeline(..., merge_gap_days=180, ayanamsha="lahiri")
get_gochara(..., transit_date, ayanamsha="lahiri")
```

`calculate_transit(transit_date_str, natal_chart, timezone_str="Asia/Kolkata")`
reads the variant from `natal_chart["metadata"]["ayanamsha_variant"]` and
defaults to `lahiri` for pre-1.5 charts. It does not take a new parameter.

`_configure_swiss_ephemeris(ephe_path='', ayanamsha="lahiri")` sets both the
path and the sidereal mode. Every call site passes the variant explicitly.
`transit.py`'s `_longitude` and `_is_retrograde` take the variant and re-assert
it inside the lock before each `calc_ut`, closing the cross-thread variant-leak
window that per-scan configuration would otherwise open.

### 7.3 Validation and errors

A new internal `_ayanamsha.py` holds the mapping, aliases, and
`resolve_ayanamsha(value) -> (key, display, sidm)`. `_validation.py` gains
`validate_ayanamsha`. `None` or `""` resolves to `lahiri`; a non-string or an
unknown key raises:

```
InvalidInputError: Unknown ayanamsha 'xyz'. Supported: lahiri, lahiri_icrc,
true_citra, raman, krishnamurti, krishnamurti_vp291, yukteshwar, fagan_bradley.
```

Validation runs at every public boundary and again in `calculate_vedic_chart`
for direct callers. The resolved SIDM constant is passed down, so a typo cannot
reach Swiss Ephemeris.

### 7.4 Metadata

```python
"metadata": {
    "ayanamsha": "Lahiri",              # display; unchanged for default calls
    "ayanamsha_variant": "lahiri",      # new canonical key
    "ayanamsha_degrees": 23.8571,       # variant-specific, as today
    "swe_version": swe.version,         # existing ephemeris version
    "ephemeris": ephe_path or "bundled",
    ...
}
```

Cache-key contract: no cache exists in either repo today (verified). Row 6's
cache key **must** include `ayanamsha_variant`; the metadata key is the source
of truth. This is recorded here because the report makes the key amendment a
blocking acceptance criterion on the variant parameter.

## 8. MCP surface

All 12 tools gain `ayanamsha: str = "lahiri"` as their last parameter;
compatibility uses one shared variant for both charts. Each docstring gets one
line:

```
ayanamsha: One of lahiri (default), lahiri_icrc, true_citra, raman,
krishnamurti, krishnamurti_vp291, yukteshwar, fagan_bradley.
```

`cast_vedic_chart` passes the same `ayanamsha` to its sensitivity cast;
base-chart reuse is deferred (section 11). `system_prompt.md` gains the routing rule: default Lahiri; change only when the
user explicitly names a system; state the variant in the answer; KP ayanamsha
only with sub-lord theory.

Tool count stays 12. Definition tokens grow by roughly 1–2 KB; row 7's
consolidation absorbs it later.

## 9. Gold corpus and tolerance ladder

### 9.1 Fixtures

New `tests/fixtures/gold_charts.json`, one entry per chart, with a provenance
header (oracle, oracle version, ayanamsha, ayanamsha constant). New
`tests/test_gold_corpus.py` loads the file; `test_comprehensive.py` is
untouched.

| Entry | Birth data | Oracle |
|---|---|---|
| Raman Standard Horoscope | 1918-10-16 14:20 IST, Bangalore 12.9716N 77.5946E | Lagna reference 24.95° and nakshatras from the published Raman chart; planets from JPL Horizons DE441 |
| Mumbai 1995 | 1995-06-15 14:30 IST, Mumbai 19.0760N 72.8777E | JPL Horizons DE441 planet longitudes; the Vedika article's table is discarded as fabricated (its Moon is 19° off Horizons) |
| Decade-spread chart | 1975-01-15 09:00 IST, Delhi 28.6139N 77.2090E | JPL Horizons DE441 planet longitudes |

**Oracle correction (2026-11-07).** The research note's Vedika-published
Mumbai and Gandhi values were checked against JPL Horizons DE441 and are wrong:
the article puts the Mumbai Moon at Aquarius 20.11° while Horizons gives
Capricorn 1.34° sidereal (a 19° error), and the engine matches Horizons to
0.01°. The article is an illustrative marketing page, not a reference. The
corpus uses Horizons for planets, the published Raman lagna and nakshatras for
the categorical/ascendant anchors, and the existing engine-vs-Horizons checks
for the Mumbai and 1970s entries.

A one-time generator at `tests/fixtures/generate_gold.py` queries the Horizons
API (stdlib `urllib.request`, no new runtime dependency) and writes the
committed JSON. The test suite never touches the network. Each Horizons value
is stored as an apparent geocentric ecliptic longitude of date; the test
compares `engine_sidereal + engine_ayanamsha_degrees` to it within 0.05°. The
absolute ayanamsha is pinned separately at J2000.

### 9.2 Ladder

- Ayanamsha at JD 2451545.0: `abs(v - 23.853222) <= 0.02`; record 23.857092 in
  the test comment.
- Planets: `engine_sidereal + engine_ayanamsha_degrees` within 0.05° of the
  Horizons tropical longitude; sign exact. Seven classical planets only — the
  mean node has no Horizons target and stays covered by the opposition
  invariant and the Raman nakshatra values.
- Ascendant: within 0.50° of the published Raman reference (24.95°); sign
  exact.
- Moon nakshatra and pada: exact against the published Raman values and the
  Horizons-derived longitude.
- Dasha: the report's ±1-day external rung is the target, but no exact
  published dasha dates are available yet. The test asserts the Vimshottari
  formula invariant instead: first lord equals the Moon's nakshatra lord, the
  first period ends at birth + remaining fraction × lord years within one day,
  and the 120-year timeline tiles with no gaps or overlaps.
- Separation guards: Lahiri vs Raman at least 1.0° apart; Lahiri vs ICRC within
  0.01°; Lahiri vs True Citra within 0.05°.
- Variant metadata: a non-default cast records its canonical key and a
  different `ayanamsha_degrees`.

## 10. Wrapper hardening

### 10.1 First-call ephemeris-flag check

Capture the flags returned by `swe.calc_ut` (today discarded at every call
site). On the first calculation per process, under `_SWE_LOCK`, check the
Moshier bit (`swe.FLG_MOSEPH`); if set, log once:

```
WARNING dashaflow.vedic_calculator: Swiss ephemeris unavailable; using
Moshier fallback (reduced accuracy). Provide .se1 files via ephe_path.
```

`metadata["ephemeris_accuracy"]` becomes flag-derived rather than path/year
heuristic. A bad `ephe_path` that silently falls back can no longer report
"full (custom ephemeris path)".

### 10.2 `serr` seam (deferred — row 3)

Not part of 1.5.0. A future helper `_unpack_swe(result, func, jd)` accepts 2- or
3-tuples and logs a non-empty `serr` at WARNING with function and Julian day.
On pyswisseph 2.10.03
every call returns a 2-tuple, so this is a no-op seam; row 3's pysweph swap
activates it. The design does not pretend otherwise.

### 10.3 Lock and re-assertion

Every `swe.*` touch runs under `_SWE_LOCK` with the path and sidereal mode
re-asserted. Counted call sites: `vedic_calculator.py` (main calc, panchang,
transit), `transit.py` (4), `panchang.py` (2). `_longitude`/`_is_retrograde`
re-assert per call; the scan loop still does not hold the lock.

### 10.4 Regression tests

- **Forced Moshier:** cast a 1990 chart with a nonexistent `ephe_path`; assert
  the warning fires and metadata says reduced, not full.
- **Arctic:** cast at 78.2232N, 15.6469E (Longyearbyen) for 1990-06-15 12:00;
  assert a finite ascendant and a valid chart. The Placidus→Porphyry fallback
  is silent on this backend, so the test pins the current result; row 3 will
  tighten it with backend warnings.
- **Concurrent variants:** 8-way threads alternating Lahiri and Raman; assert
  each chart's metadata and ayanamsha degrees match its requested variant and
  never mix.

## 11. Pre-cast reuse (row 0 — deferred)

Deferred in the correctness-only trim; no 1.5.0 signature or behavior depends
on it. The design below is kept for the follow-up.

`get_time_sensitivity(..., ayanamsha="lahiri", base_chart=None)`:

- With `base_chart`: two casts (lo/hi) instead of three; the MCP compact path
  drops from four total to three, saving ~2.1 ms (~23%).
- `base_chart` must be a dict with `lagna`, `planets`, and `dashas`; anything
  else raises `InvalidInputError`. It is the caller's chart for the same birth
  data; the function never mutates it.
- Test: monkeypatch `calculate_vedic_chart` and assert 2 calls with
  `base_chart` vs 3 without; assert the returned dict is identical either way.
- MCP `cast_vedic_chart` passes the chart it already cast.

## 12. Backward compatibility

- Every new argument is appended; existing positional calls are unchanged.
- Default Lahiri produces the same positions and dasha dates as 1.4.1.
- New metadata keys are additive. If any schema enumerates metadata keys, add
  `ayanamsha_variant`; compact schemas are unaffected.
- SAV=337 and all output-contract checks unchanged.
- MCP: existing tool names, args, and defaults unchanged; tool count stays 12.
- `base_chart` and the `serr` seam are deferred; no 1.5.0 call path uses them.

## 13. Testing and release

- TDD for every item: failing test first, then the smallest implementation.
- Local gate: `python -m pytest tests/ --junitxml=<file>` plus
  `python -m ruff check src tests`.
- dashaflow 1.5.0: feature branch → PR (1 approval, 4 checks) → merge → PyPI
  (environment approval) → clean-venv verify.
- rishi-ai-mcp 1.5.0: bump `dashaflow>=1.5.0,<2.0.0`, same PR gate, PyPI,
  clean-venv tool-count and variant smoke test.
- CHANGELOG entries in both repos.

## 14. Risks and open questions

- **Yukteshwar inclusion** deviates from the report's seven-variant prose;
  recommendation is to keep all eight measured variants.
- **J2000 constant:** installed backend gives 23.857092°, the pin is
  23.853222°; the rung absorbs it, but the test must assert the rung, not exact
  equality.
- **Gold corpus oracle:** the Vedika article's Mumbai and Gandhi values were
  proven wrong against JPL Horizons and are discarded; planets now come from
  Horizons DE441, lagna/nakshatras from the published Raman chart. The ±1-day
  dasha rung remains a formula invariant until exact published dasha dates are
  sourced.
- **Arctic fallback** is not directly observable on pyswisseph 2.10.03; the
  test pins behavior until row 3.
- **MCP definition tokens** grow slightly; accepted, row 7 reverses it.

## 15. Approval

Approve this doc (and the eight-variant allowlist) and I will invoke
`writing-plans` to produce the implementation plan. No code changes before
approval.
