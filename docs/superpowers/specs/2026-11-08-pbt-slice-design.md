# PBT slice — five structural properties (short design)

## Intent and why

Prove no birth moment produces a structurally broken chart. The 1.5.0 gold
corpus pins three known charts right; this slice asserts five structural
rules across thousands of random inputs (dates, places, variants), so a
future engine edit cannot silently ship a flipped dasha lord, gapped
timeline, or variant mix-up for an untested instant.

## Goals

- Five Hypothesis properties, ~20–30 examples each (per the research's
  efficiency prescription), in one new file `tests/test_properties.py`:
  1. SAV always totals 337 (any date/place/variant).
  2. Inter-variant shift equals the ayanamsha difference (±0.001°).
  3. Dasha integrity: contiguous timeline, correct opening lord for the
     Moon's nakshatra, segments line up.
  4. Determinism: same inputs, identical chart.
  5. Sensitivity honesty: never "robust" when a ±4-min move flips lagna
     or pada.
- Hypothesis as a test-only extra; engine stays dependency-lean.
- Any property failure triaged as engine bug (fix + regression test) or
  over-strict rule (fix the property); properties are never deleted to
  silence a failure.

## Non-goals

- Coverage bands, eval gates, token CI (row 9 items) — deferred.
- New runtime behavior; production code changes only if a property finds
  a real bug.
- Semantic correctness (right yoga per BPHS) — still owned by the gold
  corpus and domain review.

## Anti-goals

- Flaky suite: bounded examples, no wall-clock dependence, explicit
  deadlines disabled where engine timing varies.
- Slowing the suite materially: slice must stay under ~1 min locally.

## Constraints

- Python 3.10+, pytest, ruff (E,F,W,I,UP,B; `strict=` on zips).
- Additive only: one test file + test-dependency declaration.
- Full gate stays `pytest tests/` + `ruff check src tests`.

## Approaches

- **A. Small slice (picked):** the five properties above. Cheap, fast,
  covers every structural dimension 1.5.0 made variant-dependent.
- **B. Full PBT + coverage bands:** what the research sketched
  (~5+ properties, max-examples tuning, 75–85% bands). More assurance,
  more triage and suite time — oversized for a quiet engine.
- **C. Status quo:** corpus + 434 examples only. Zero cost, keeps the
  "untested instant" blind spot.

## Decided

- Hypothesis via the test extra (`.[test]`), never imported by
  `src/dashaflow`.
- Failing property ⇒ engine fix or property fix, recorded in the commit
  message; deletion is not a resolution.

## Left to the builder

- Exact strategies (date ranges, lat/lon bounds, variant sampling).
- Per-property tolerances (confirm against the 0.05°/1-day ladder
  where applicable).
- Whether properties share one birth-input strategy helper.
