# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/).

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

[1.1.0]: https://github.com/adarshj322/dashaflow/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/adarshj322/dashaflow/releases/tag/v1.0.0
