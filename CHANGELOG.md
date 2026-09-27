# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Vimshopaka Bala (Shad-Varga 20-point strength with bands) wired into every chart.
- Sodhita Ashtakavarga (Trikona + Ekadhipatya reductions) with Sodhya Pinda per planet.
- Yogini Dasha (36-year cycle, Maha/Antar/Pratyantar + timeline).
- Chara Dasha (Jaimini sign-to-lord method, verified against K.N. Rao's published Bachchan sequence).
## [1.2.0] - 2026-09-10

### Added
- Error taxonomy (`dashaflow.errors`: `DashaFlowError`, `InvalidInputError`, `EphemerisError`, `CalculationError`; input errors remain `ValueError`-compatible).
- Structured logging (`logging` module loggers; debug timings, Moshier-fallback warnings, best-effort fallback notes).
- Output-contract gate on every chart (required keys, planet fields, SAV=337 invariant) + provenance metadata (`dashaflow_version`, `swe_version`, `ephemeris`, `ephemeris_accuracy`, `computed_at_utc`).
- Production tests (`tests/test_production.py`): taxonomy, thread-safety (8-way concurrency), determinism, ephemeris-range flagging, JSON-serializability.
- `py.typed` marker (PEP 561); CI lint job (ruff F/E9) + wheel build check asserting `py.typed` ships.
- Strict input validation (impossible calendar dates, non-numeric/NaN lat-lon, query/transit dates, ephe_path) with `tests/test_validation.py`.
- Edge-case tests (`tests/test_edgecases.py`) for dasha bounds, Kemadruma Bhanga, Kaal Sarpa longitudes, Graha Yuddha latitude winner, Jaimini ties, Ashtakavarga errors.
- `pyproject.toml` test extra (`.[test]`), pytest/ruff config; pip-cached CI; documented simplifications in README Limitations.

### Changed
- Vimshottari Dasha uses sidereal year (365.2563d) with full-precision sub-period boundaries (date-only strings preserved).
- Kemadruma Yoga now applies classical cancellation; Raj Yoga adds aspect-sambandha; Neecha Bhanga adds aspect cancellation; Mahapurusha/Gajakesari annotate retro/combust weakness.
- Kaal Sarpa uses absolute longitudes (BVR reference test updated to Partial/Moon-outside); Graha Yuddha winner uses ecliptic latitude with brightness fallback.
- `vedic_calculator` refactored: table-driven vargas, shared Ketu synthesis, `_compute_raw_planets`/`_enrich_planets` helpers, locked Swiss Ephemeris config, typed helpers, concise `__main__` demo.
- Panchang Vara mapping verified (J2000 Saturday check) with float epsilon guards; Jaimini docstring corrected to 7-karaka with deterministic tie-break; Ashtakavarga raises ValueError on bad/missing inputs.
- Removed stale root duplicates (`test_comprehensive.py`, `test_enhancements.py`, `test_phase2.py`); fixed README `total_score` key.
- Thread-safety is now real: the whole Swiss Ephemeris section (configure → compute), including the Panchang sunrise correction (`set_topo`/`rise_trans`), runs under one process-wide lock; concurrent charts verified in tests.
- Dasha sub-periods tile exact parent spans (rounded display `days` no longer used for tiling), closing boundary gaps where no level resolved.
- Ambiguous/nonexistent local times (DST transitions, date-line skips) now raise `InvalidInputError` instead of silently resolving via `is_dst=False`.
- `planets_for_yoga` now carries `is_retrograde`, so Mahapurusha weakness notes can actually fire.
- Removed dead imports flagged by ruff across library modules.

### Fixed
- D30 Trimshamsha returns the BPHS fixed sign per segment (was the lord's first own sign — wrong in 5 of 10 segments).
- Shadbala Saptavargaja now scores Panchadha-Maitri grades (`great_friend`/`great_enemy` were falling through to neutral).
- Chesta Bala direct-motion scale now matches its spec (0→45, avg→30, 2x→15).
- Dasha balance and Jaimini karaka ordering use full-precision degrees (no rounding-induced flips); Mooltrikona boundaries checked on precise degrees.
- Unhashable `activity` and non-string dates now raise `InvalidInputError` instead of leaking `TypeError`; empty `query_date_str` is rejected rather than silently meaning today.
- Custom `ephe_path` is re-applied around the Panchang correction so a concurrent transit call cannot downgrade it.
- Low-level matchmaking/muhurtha/career helpers validate shapes (`InvalidInputError`) or ignore mistyped nesting instead of raising `KeyError`/`AttributeError`/`TypeError`.
- Contract gate additionally checks planet degree ranges, ayanamsha finiteness, and entry types.
- Omitted `query_date` defaults to today at noon (stable within a day); README quickstart now uses verified Delhi values and documents all four muhurtha verdicts.
- Muhurtha no longer penalizes missing weekday/Moon-sign signals and no longer fabricates Sagraha Dosha without a Moon position; misspelled lagna signs raise instead of scoring "not ideal".
- Kuja Dosha rejects partial entries and out-of-range houses/signs instead of scoring false zeros; absent planets still score nothing, while present-but-malformed entries raise; contract gate tolerates the 30.0 display-rounding sliver.
- Jaimini karaka lookup uses lazy `degree_precise` fallback and maps non-dict entries to `ValueError`.
- CI/packaging: pinned build floor, version-tolerant gates in both workflows, least-privilege publish test job, `.[dev]` installs, clean builds.

## [1.1.0] - 2026-04-08

### Added
- Added test case coverage for `cast_transit` return structure.

### Changed
- Refactored `cast_transit` to accept birth parameters (`dob_str`, `time_str`, `lat`, `lon`, `timezone`) directly instead of requiring a pre-calculated `natal_chart` input.

## [1.0.0] - 2026-03-31

### Added
- Complete natal chart casting with Swiss Ephemeris (Sidereal Lahiri)
- Vimshottari Dasha system (Maha through Prana, 5 levels)
- Transit overlay with Ashtakavarga scoring
- Ashtakoot compatibility matching (36-point system with Kuja Dosha)
- Muhurtha evaluation for 6 activity types
- D10 Dashamsha career analysis
- 24 yoga detection types including Pancha Mahapurusha and Raj Yoga
- Shadbala six-fold strength with Ishta/Kashta Phala
- Jaimini Karakas (7 Chara Karakas by degree)
- Bhava Chalit equal-house system
- Arudha Padas (A1–A12), Upapada, and Karakamsha
- Kaal Sarpa, Graha Yuddha, and Gandanta detection
- Planetary Avasthas (BPHS age-states)
- Sarvashtakavarga, Bhinnashtakavarga, and Prashtara Ashtakavarga
- Divisional charts: D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D60

[1.2.0]: https://github.com/adarshj322/dashaflow/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/adarshj322/dashaflow/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/adarshj322/dashaflow/releases/tag/v1.0.0
