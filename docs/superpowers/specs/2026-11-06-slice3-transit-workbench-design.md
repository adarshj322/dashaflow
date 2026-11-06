# Slice 3 — Transit Workbench Design

- **Status:** proposed, awaiting partner approval
- **Date:** 2026-11-06
- **Scope:** dashaflow engine 1.4.0 + rishi-ai-mcp 1.4.0
- **Supersedes:** nothing. Extends `cast_transit()` without changing it.

## 1. Intent

AI agents answer timing questions for users: *when does Saturn leave my Moon
sign*, *is 2027 a good year to change jobs*, *when does Jupiter enter my 10th
house*. The engine can currently answer only *where are the planets on date X*
(`cast_transit`, one noon snapshot, `vedic_calculator.py:781`). This slice adds
the time dimension: exact ingress instants, a Sade Sati timeline that survives
Saturn retrograde loops, and a per-planet gochara verdict weighted by the
native's Sarvashtakavarga.

The engine stays a calculator. It reports dates, spans, bindus and a
rule-derived verdict with notes. Interpretation stays with the calling agent.

## 2. Goals

- **G1** Exact sign-ingress instants (minute precision) across a bounded date
  range, including retrograde re-entries as separate events.
- **G2** Sade Sati as phase spans plus raw crossings, so retrograde
  interruptions are visible instead of silently merged away.
- **G3** Per-planet gochara: classical house-from-Moon quality combined with the
  natal SAV bindus of the transiting sign, with explicit notes.
- **G4** Compact-by-default payloads and three focused MCP tools that mirror the
  engine getters.
- **G5** Published JSON schemas, deterministic tests, and full backward
  compatibility (existing `cast_transit` untouched).

## 3. Non-goals

- Transit-to-natal aspect search (conjunctions, trines, orbs).
- Dasha–transit fusion or event prediction.
- Outer planets, KP transits, Moon ingresses, SVG rendering.
- Batch scanning over multiple natal charts.
- Server-side MCP prompts (Slice 4).

## 4. Anti-goals

- A scan that holds `_SWE_LOCK` for the whole range and blocks other callers.
- Deduplicating retrograde re-entries so the timeline looks tidy but lies.
- Emitting a single "destiny score" or claiming certainty from bindus.
- Changing `cast_transit`'s signature, output, or noon-snapshot semantics.

## 5. Constraints

- Python 3.10+, Swiss Ephemeris via existing `pyswisseph`, Lahiri ayanamsha.
- All ephemeris access under the process-wide `_SWE_LOCK`, acquired per call,
  never for the whole scan.
- One new public module plus additive exports; no new dependencies.
- Hard range cap: **15 years** per call (payload and compute bound).
- Payload targets: 5-year 3-body ingress scan < 4 KB; 15-year Sade Sati < 2 KB;
  gochara < 3 KB.

## 6. Approaches considered

**A — Three focused getters (chosen).** `get_transit_ingresses`,
`get_sade_sati_timeline`, `get_gochara`. Mirrors the Slice 1 getter pattern,
keeps each payload small, and makes each function independently testable.
Cost: three more MCP tools (9 → 12).

**B — One composite `get_transit_workbench(sections=[...])`.** One tool, one
call. Rejected because the default payload is large for the most common
question ("when does Saturn ingress?"), and routing a `sections` list is harder
for agents than picking a named tool.

**C — Extend `cast_transit` with `start_date`/`end_date`.** Fewest names.
Rejected because it makes the common one-date call heavier, muddies the
backward-compatible contract, and forces a single output shape onto three
different questions.

A is chosen; if you prefer B or C, say so before approving.

## 7. Engine API

### 7.1 Module layout

New `src/dashaflow/transit.py`, importing shared internals from
`vedic_calculator` (`_SWE_LOCK`, `_configure_swiss_ephemeris`,
`get_sign_and_degree`) and constants from `constants.py` (`PLANETS`,
`ZODIAC_SIGNS`). No circular import: `vedic_calculator` never imports
`transit`.

Public exports added to `__init__.py` and `__all__`:

```python
get_transit_ingresses(dob, time, lat, lon, timezone,
                      start_date, end_date, bodies=None) -> dict
get_sade_sati_timeline(dob, time, lat, lon, timezone,
                       start_date, end_date, merge_gap_days=180) -> dict
get_gochara(dob, time, lat, lon, timezone, transit_date) -> dict
```

Birth details come first, matching `get_time_sensitivity`. All three validate
with `validate_birth_input`; range functions validate both dates with
`validate_query_date`.

### 7.2 `get_transit_ingresses`

Default bodies: `("Jupiter", "Saturn", "Rahu")`. Allowed set: Sun, Mars,
Mercury, Jupiter, Venus, Saturn, Rahu, Ketu. Moon is rejected (it changes sign
every ~2.25 days and would dominate any payload); agents wanting Moon
positions use `cast_transit`.

Output:

```python
{
  "range": {"start": "2023-01-01", "end": "2026-01-01"},
  "bodies": ["Jupiter", "Saturn", "Rahu"],
  "ingresses": [
    {
      "planet": "Saturn",
      "date": "2023-01-17",              # local calendar date
      "instant_utc": "2023-01-17T12:34:00Z",  # minute precision
      "from_sign": "Capricorn",
      "to_sign": "Aquarius",
      "direction": "direct",             # direct | retrograde
      "house_from_lagna": 7,
      "house_from_moon": 4
    }
  ]
}
```

Rules:

- Events are chronological across all bodies; ties broken by planet name.
- `direction` is `retrograde` when the body's longitudinal speed is negative at
  the crossing instant; Rahu and Ketu are always `retrograde`.
- Ketu is derived from Rahu + 180°; its crossings share Rahu's instants and
  carry the opposite signs. Ketu is only computed when requested or when
  present in `bodies`.
- Houses come from the natal chart's Lagna and Moon signs.
- Ranges with `start_date > end_date` or longer than 15 years raise
  `InvalidInputError`.

### 7.3 `get_sade_sati_timeline`

Sade Sati is Saturn transiting the 12th, 1st, or 2nd sign from the natal Moon:
`rising`, `peak`, `setting`. Output:

```python
{
  "natal_moon_sign": "Scorpio",
  "range": {"start": "2010-01-01", "end": "2022-01-01"},
  "merge_gap_days": 180,
  "active_at_start": false,
  "active_at_end": false,
  "spans": [
    {"phase": "rising", "start": "2011-11-15", "end": "2014-11-01",
     "days": 1083, "gap_days": 80, "in_phase_days": 1003,
     "interruptions": 1, "starts_before_range": false, "ends_after_range": false},
    {"phase": "peak", "start": "2014-11-02", "end": "2017-01-25",
     "days": 816, "gap_days": 0, "in_phase_days": 816,
     "interruptions": 0, "starts_before_range": false, "ends_after_range": false},
    {"phase": "setting", "start": "2017-01-26", "end": "2017-06-20",
     "days": 146, "gap_days": 0, "in_phase_days": 146,
     "interruptions": 0, "starts_before_range": false, "ends_after_range": false},
    {"phase": "peak", "start": "2017-06-21", "end": "2017-10-25",
     "days": 127, "gap_days": 0, "in_phase_days": 127,
     "interruptions": 0, "starts_before_range": false, "ends_after_range": false},
    {"phase": "setting", "start": "2017-10-26", "end": "2020-01-23",
     "days": 820, "gap_days": 0, "in_phase_days": 820,
     "interruptions": 0, "starts_before_range": false, "ends_after_range": false}
  ],
  "crossings": [
    {"date": "2011-11-15", "instant_utc": "2011-11-15T04:42:00Z",
     "from_sign": "Virgo", "to_sign": "Libra",
     "from_phase": "off", "to_phase": "rising", "direction": "direct"}
  ]
}
```

Date and span semantics:

- All `start`/`end` values are **local calendar dates** in the supplied
  timezone, inclusive. A span ends on the day before the next phase change.
- `days` is the inclusive day count of the returned span.
- `gap_days` is the number of absorbed "off" days inside a merged span;
  `in_phase_days = days - gap_days`.
- `interruptions` counts absorbed **off** gaps only (Saturn left the 12/1/2
  zone and returned). It does not count a retrograde excursion into another
  Sade Sati phase.
- Spans are disjoint and chronological. A retrograde excursion from one Sade
  Sati phase into another (the 2017 setting → peak → setting echo) is its own
  span, because the phase genuinely changed; it is not merged and not
  double-counted.
- Only off gaps of `merge_gap_days` or less are absorbed. The default **180**
  absorbs the 2011–2020 cycle's 80-day break; `merge_gap_days=0` returns literal
  spans. This is a presentation policy, not a mathematical fact, and is flagged
  for astrologer sign-off.
- `starts_before_range` is true when the phase was already active at
  `start_date` and the span was clipped to the range edge. `ends_after_range`
  is the analogous flag at `end_date`.
- `active_at_start` / `active_at_end` report whether the range boundary itself
  falls inside a Sade Sati phase.
- `crossings` lists every Saturn sign change in the range, entries and exits,
  with `from_phase`/`to_phase` (`rising | peak | setting | off`) and direction.
  `instant_utc` has minute precision.

### 7.4 `get_gochara`

Transit positions at local noon on `transit_date` (same instant convention as
`cast_transit`). Reference is always the natal Moon. Output:

```python
{
  "transit_date": "2026-06-02",
  "reference": "moon",
  "natal_moon_sign": "Scorpio",
  "sav_average": 28.08,
  "planets": {
    "Jupiter": {
      "sign": "Cancer",
      "house_from_moon": 9,
      "is_retrograde": false,
      "sav_points": 19,
      "house_quality": "favorable",
      "weighted_verdict": "mixed",
      "notes": ["9th from Moon is favourable",
                "SAV 19 below sign average 28.08"]
    }
  }
}
```

Favourable houses from the Moon (B.V. Raman's table):

| Planet | Favourable houses |
|---|---|
| Sun | 3, 6, 10, 11 |
| Moon | 1, 3, 6, 7, 10, 11 |
| Mars | 3, 6, 11 |
| Mercury | 2, 4, 6, 8, 10, 11 |
| Jupiter | 2, 5, 7, 9, 11 |
| Venus | 1, 2, 3, 4, 5, 8, 9, 11, 12 |
| Saturn | 3, 6, 11 |
| Rahu | 3, 6, 11 |
| Ketu | 3, 6, 11 |

`house_quality` is `favorable` or `unfavorable` (houses outside the table).
`weighted_verdict` combines house quality with SAV:

| House | SAV vs average | Verdict |
|---|---|---|
| favourable | at/above | `favorable` |
| favourable | below | `mixed` |
| unfavourable | at/above | `mixed` |
| unfavourable | below | `unfavorable` |

`notes` states the rule used, so an agent can explain the verdict. SAV is the
sign-level Sarvashtakavarga from the natal chart (already present at
`ashtakavarga.sarvashtakavarga`). Using the transiting planet's own BAV is a
known refinement, deferred; the doc records it as a limitation.

## 8. Algorithms and precision

- Sampling step: 1 day for Sun, Mars, Mercury, Venus; 5 days for Jupiter,
  Saturn, Rahu, Ketu. A sign change and a return within one step is impossible
  at these speeds.
- Ingress detection: compare the sign index at adjacent samples; on change,
  bisect the Julian-day bracket on the sign index until the interval is
  ≤ 60 seconds. Do not assume longitude is monotonic inside a bracket —
  stations reverse it; the sign comparison is the predicate.
- Complexity: ~1,100 samples per slow body per 15 years; four bodies ≈ 4,400
  ephemeris calls plus ~15 bisection steps per event. Target under 3 seconds on
  the CI machine.
- Locking: each `swe.calc_ut` acquires `_SWE_LOCK`; the scan never holds it
  across samples, so other callers interleave.
- Sade Sati spans are built as disjoint segments from the phase at `start_date`
  plus each Saturn crossing; a phase already active at the range edge yields a
  span starting at that edge with `starts_before_range=true`, and one still
  active at `end_date` gets `ends_after_range=true`. Same-phase spans separated
  by an **off** gap of `merge_gap_days` or less are merged; cross-phase
  excursions stay separate. `end` is the day before the next change, and all
  day counts are inclusive calendar days.
- Ingress instants convert UTC → supplied timezone for the local `date`;
  UTC→local conversion never lands in a DST gap. `end_date` is inclusive for
  scans; the internal sample bound is `end_date + 1 day`.

## 9. Schemas

Add `TRANSIT_INGRESSES_SCHEMA`, `SADE_SATI_TIMELINE_SCHEMA`, and
`GOCHARA_SCHEMA` to `dashaflow.schemas`, registered in `_SCHEMAS` under
`"transit_ingresses"`, `"sade_sati_timeline"`, `"gochara"`. Required keys
match the outputs above, including `starts_before_range`, `ends_after_range`,
`active_at_start`, `active_at_end`, `gap_days`, and `in_phase_days`; nested
planet/event objects are typed as objects, consistent with the existing schema
style.

## 10. MCP surface (rishi-ai-mcp)

Three tools, each a thin wrapper with `try/except` → `_raise(e)`:

| Tool | Arguments |
|---|---|
| `get_transit_ingresses_tool` | dob, time, lat, lon, timezone, start_date, end_date, bodies=None |
| `get_sade_sati_timeline_tool` | dob, time, lat, lon, timezone, start_date, end_date, merge_gap_days=180 |
| `get_gochara_tool` | dob, time, lat, lon, timezone, transit_date |

Docstrings list the output keys, the meaning of `direction`, `interruptions`,
`weighted_verdict`, and the SAV-vs-BAV limitation. No `detail` knob: payloads
are already compact. Tool count becomes 12. `system_prompt.md` gains a short
"timing questions" paragraph routing *when/period* questions to these tools and
keeping `cast_transit_chart` for a single-date snapshot. `pyproject.toml` floor
becomes `dashaflow>=1.4.0,<2.0.0`.

## 11. Testing (TDD order)

Engine, new `tests/test_transit_workbench.py`:

1. Ingress self-consistency: for every event, the body's sign one minute before
   and one minute after differs and matches `from_sign`/`to_sign`.
2. Events are chronological and a body cannot ingress to the sign it just left
   without an intermediate event.
3. Saturn 2022–2025 includes at least one `direction="retrograde"` ingress
   (the Capricorn/Aquarius loop).
4. Known anchors: Saturn enters sidereal Aquarius on 2023-01-17 (assert the
   local date is 2023-01-16..2023-01-18) and sidereal Pisces on 2025-03-29.
5. Ketu events mirror Rahu six signs away at the same instants.
6. Range cap, reversed range, unknown body, Moon body, and malformed dates all
   raise `InvalidInputError`.
7. Sade Sati for the demo chart (Moon Scorpio), 2010-01-01..2022-01-01:
   spans are exactly rising 2011-11-15..2014-11-01 (days 1083, gap_days 80,
   interruptions 1), peak 2014-11-02..2017-01-25, setting 2017-01-26..2017-06-20,
   peak echo 2017-06-21..2017-10-25, setting 2017-10-26..2020-01-23;
   `active_at_start` and `active_at_end` are false.
8. `merge_gap_days=0` splits the 2012 off gap into two rising spans, and the
   2017 peak echo remains a separate span under both settings.
9. Clipped range: a query covering only 2016 yields a peak span with
   `starts_before_range=true` and `ends_after_range=true`; a query starting
   inside the rise yields `starts_before_range=true` and `active_at_start=true`.
10. Gochara: SAV total is 337; Jupiter in Cancer for the demo chart reports 9th
    from Moon, `sav_points=19`, `weighted_verdict="mixed"`; a favourable house
    with above-average SAV yields `favorable`; unfavourable + below yields
    `unfavorable`.
11. Schema validation passes for each output when `jsonschema` is installed
    (skip otherwise), matching existing schema-test style.

MCP: tool count 12; each tool returns the engine shape; `ToolError` mapping for
a bad date; `HH:MM[:SS]` still accepted.

Existing 358 engine tests and 33 MCP tests stay green.

## 12. Docs and release

- README: three rows in the API table plus a short "Transit timing" section with
  the gochara rule table and the retrograde caveat.
- CHANGELOG `[Unreleased]` → 1.4.0 on release.
- Version bump `_version.py` 1.4.0; MCP `__version__` 1.4.0.
- Same flow as 1.3.0: PR → full CI matrix → merge → tag → publish → `pypi`
  environment approval → clean-venv verify. Engine first, then MCP.

## 13. Build order

1. `transit.py` ingress core + `get_transit_ingresses` + tests.
2. Sade Sati timeline + tests.
3. Gochara + table + tests.
4. Schemas, exports, README, CHANGELOG.
5. Release dashaflow 1.4.0.
6. MCP tools + tests + system_prompt + dependency floor + release 1.4.0.

## 14. Judgment calls (defaults chosen, not facts)

- Gochara favourable-house table, including Rahu/Ketu at 3, 6, 11.
- SAV weighting rather than the transiting planet's BAV (research-note
  commitment; BAV noted as future refinement).
- `merge_gap_days=180` default and the `interruptions` counter.
- The favorable/mixed/unfavorable mapping at the SAV average.

If any of these is wrong for the tradition you follow, say which and it changes
the outputs, not the structure.

## 15. Left to the builder

- Helper names, logging lines, type annotations.
- Exact bisection stopping tolerance (target ≤ 60 seconds).
- Test date anchors beyond the Saturn/Pisces anchor, chosen for determinism.
- Whether to share a small `_transit_longitude` helper with `calculate_transit`
  (preferred: yes, without changing `calculate_transit`'s behavior).
