# RishiAI — Vedic Astrology MCP Server

A Vedic astrology engine exposed as an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server, built on the **Swiss Ephemeris** with **Sidereal Lahiri** ayanamsha. Designed to power AI astrologer agents (like the included **RishiAI** persona) with astronomically precise chart data rooted in *Brihat Parashara Hora Shastra* (BPHS) and B.V. Raman's *Hindu Predictive Astrology*.

## Features

- **Natal Chart Casting** — Ascendant (Lagna), all nine Vedic grahas (Sun through Ketu), whole-sign houses, nakshatras with padas, and planetary dignities
- **14 Divisional Charts** — D2 (Hora), D3, D4, D7, D9 (Navamsha), D10 (Dashamsha), D12, D16 (Shodashamsha), D20 (Vimshamsha), D24, D27 (Bhamsha), D30, D40 (Akshavedamsha), D60 sign placements for every planet and the Lagna
- **Planetary Strength** — Dignity classification (B.V. Raman aligned), combustion detection (BPHS orbs), retrograde status, Digbala (directional strength), **Shadbala** (six-fold mathematical strength with enhanced Saptavargaja, Paksha, Ayana, Chesta, and Drik balas), and **Ishta/Kashta Phala** (auspicious/inauspicious potential per planet)
- **Jaimini Karakas** — All 7 Karakas by degree (Atmakaraka, Amatyakaraka, Bhratrukaraka, Matrukaraka, Putrakaraka, Gnatikaraka, Darakaraka)
- **Ashtakavarga** — Sarvashtakavarga (SAV), Bhinnashtakavarga (BAV), and **Prashtara Ashtakavarga** (source-level bindu contributions showing which planet contributed to which sign)
- **BPHS Aspects** — Standard 7th-house aspects for all planets, plus special aspects for Mars (4th/8th), Jupiter (5th/9th), and Saturn (3rd/10th) with weighted partial aspects
- **Vimshottari Dasha (5 levels)** — Full 120-year Mahadasha timeline, with active Mahadasha, Antardasha, Pratyantardasha, **Sukshma**, and **Prana** dasha for any query date
- **24 Yoga Types** — Pancha Mahapurusha (5), Gajakesari, Budhaditya, Chandra-Mangal, Kemadruma, Adhi Yoga, Raj Yoga (dual lordship + conjunction), Viparita Raj Yoga, Neecha Bhanga Raja Yoga, Parivartana (Maha/Khala/Dainya), Dhana Yoga, Sunapha/Anapha/Durudhura, Amala, Saraswati, Lakshmi, Veshi/Voshi/Ubhayachari
- **Panchang** — Birth Tithi, Vara (weekday lord), Nakshatra, Panchang Yoga, and Karana
- **Transit Overlay** — Current planetary positions mapped to natal houses (from Lagna and Moon), SAV transit points, Sade Sati detection with phase, and Rahu-Ketu transit axis
- **16-Factor Compatibility** — 8 traditional Ashtakoot kutas (36 pts) + Mahendra, Stree Deergha, Vedha, Rajju, BadConstellations, LagnaHouse7, SexEnergy, and **Kuja Dosha** (Manglik) analysis with dignity-based scoring and exception logic
- **Muhurtha (Electional Astrology)** — Panchang Suddhi checks, activity-specific rules for 6 domains (marriage, travel, business, education, house_entry, medical), marriage doshas (Sagraha, Shashtashta, Bhrigupta Shatka, Kujaasthama)
- **Career Analysis** — D10 Dashamsha career analysis with planet-career significations, sign-career domains, 10th house analysis, and career theme recommendations
- **Bhava Chalit Chart** — Equal-house Bhava Chalit with cusps from Lagna midpoint, showing which planets shift bhavas compared to whole-sign houses
- **Planetary Avasthas** — Five age-states per BPHS (Bala, Kumara, Yuva, Vriddha, Mrita) with odd/even sign reversal, indicating each planet's capacity to deliver results
- **Kaal Sarpa Dosha** — Full and partial Kaal Sarpa detection with ascending/descending type classification and Rahu-Ketu axis reporting
- **Graha Yuddha (Planetary War)** — Detection of true planets within 1° longitude, reporting winner, loser, and separation
- **Gandanta Detection** — Identifies planets and Lagna within 3°20' of water-fire sign boundaries (karmic knot junctions)
- **Arudha Padas** — All 12 Arudha Padas (A1–A12) with BPHS exception rule (same-sign/7th → 10th shift). Key padas: A1 (worldly image), A7 (spouse), A10 (career reputation)
- **Upapada Lagna** — A12 calculation with lord and 2nd-from-UL for marriage analysis
- **Karakamsha Analysis** — Atmakaraka in Navamsha with house from Lagna, Ishta Devata detection (12th from Karakamsha), and planets in Karakamsha sign

## Architecture

```
mcp_server.py              MCP entry point — exposes 5 tools
  └── vedic_calculator.py  Core engine — Swiss Ephemeris computations & chart assembly
        ├── constants.py   Zodiac signs, sign lords, nakshatras, dasha years, dignity tables
        ├── nakshatra.py   Nakshatra lookup from longitude
        ├── panchang.py    Tithi, Vara, Yoga, Karana calculations
        ├── yoga.py        24 yoga detection types + Kaal Sarpa, Graha Yuddha, Gandanta
        ├── dasha.py       Vimshottari Dasha (5 levels: Maha→Antar→Pratyantar→Sukshma→Prana)
        ├── dignity.py     Dignity, combustion, digbala, compound relationships
        ├── ashtakavarga.py SAV, BAV & Prashtara Ashtakavarga
        ├── jaimini.py     7-Karaka calculation + Arudha Padas + Upapada + Karakamsha
        ├── shadbala.py    Six-fold planetary strength + Ishta/Kashta Phala
        ├── matchmaking.py 16-factor compatibility + Kuja Dosha
        ├── muhurtha.py    Electional astrology (6 activity types)
        └── career.py      D10 Dashamsha career analysis

.agents/
  ├── rules/rishi-ai.md       RishiAI persona — always-on system rule
  └── workflows/              Slash-command workflows
        ├── full-reading.md          /full-reading
        ├── career-analysis.md       /career-analysis
        ├── marriage-analysis.md     /marriage-analysis
        ├── relationship-analysis.md /relationship-analysis
        ├── children-analysis.md     /children-analysis
        ├── finance-analysis.md      /finance-analysis
        ├── health-analysis.md       /health-analysis
        ├── education-analysis.md    /education-analysis
        ├── spiritual-analysis.md    /spiritual-analysis
        ├── muhurtha-analysis.md     /muhurtha-analysis
        ├── physicalIntimacy-analysis.md /physicalIntimacy-analysis
        └── geopolitics-analysis.md  /geopolitics-analysis
```

## Prerequisites

- **Python 3.10+**
- **Swiss Ephemeris data files** — The `swisseph` package includes bundled ephemeris files. For extended date ranges, download additional files from [astro.com](https://www.astro.com/swisseph/).

## Installation

```bash
git clone <repo-url>
cd Astrology_script

pip install -r requirements.txt
# or manually:
pip install pyswisseph pytz mcp
```

## MCP Tools

### `cast_vedic_chart`

Generates a complete Vedic natal chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| `dob` | string | Date of birth — `"YYYY-MM-DD"` |
| `time` | string | Time of birth — `"HH:MM"` (24-hour) |
| `lat` | float | Birth latitude (e.g. `28.6139` for Delhi) |
| `lon` | float | Birth longitude (e.g. `77.2090` for Delhi) |
| `timezone` | string | IANA timezone (e.g. `"Asia/Kolkata"`) |
| `query_date` | string | Optional — date for Dasha lookup, defaults to today |

**Returns:** JSON with `metadata`, `panchang`, `lagna` (with D2–D60 signs), `planets` (with dignity, combustion, Shadbala, all 14 Varga signs, aspects), `dashas` (5 levels: Maha/Antar/Pratyantar/Sukshma/Prana + timeline), `yogas` (24 types), `ashtakavarga` (SAV + BAV + Prashtara), `jaimini_karakas`, `shadbala` (with Ishta/Kashta Phala), `bhava_chalit` (equal-house Chalit), `avasthas` (5 age-states), `kaal_sarpa`, `graha_yuddha`, `gandanta`, `arudha_padas` (A1–A12), `upapada`, `karakamsha`.

### `cast_transit_chart`

Calculates planetary transits overlaid on a natal chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| `transit_date` | string | Date to compute transits — `"YYYY-MM-DD"` |
| `natal_chart_json` | string | Full JSON output from `cast_vedic_chart` |
| `timezone` | string | Optional — defaults to `"Asia/Kolkata"` |

**Returns:** JSON with transit `planets` (sign, degree, nakshatra, `sav_points`, house from Lagna/Moon), `sade_sati` status and phase, and `rahu_ketu_axis`.

### `calculate_compatibility`

Calculates 16-factor compatibility + Kuja Dosha. Person 1 = Male, Person 2 = Female.

| Parameter | Type | Description |
|-----------|------|-------------|
| `dob1`, `time1`, `lat1`, `lon1`, `tz1` | various | Birth details for Person 1 (Male) |
| `dob2`, `time2`, `lat2`, `lon2`, `tz2` | various | Birth details for Person 2 (Female) |

**Returns:** 8 Ashtakoot kutas (36 pts: Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi), additional kutas (Mahendra, Stree Deergha, Vedha, Rajju, BadConstellations, LagnaHouse7, SexEnergy), exception logic, and Kuja Dosha analysis with per-person scores and compatibility verdict.

### `check_muhurtha`

Evaluates whether a date/time is auspicious for a specific activity (electional astrology).

| Parameter | Type | Description |
|-----------|------|-------------|
| `activity` | string | One of: `marriage`, `travel`, `business`, `education`, `house_entry`, `medical` |
| `date` | string | Date to evaluate — `"YYYY-MM-DD"` |
| `time` | string | Time to evaluate — `"HH:MM"` (24-hour) |
| `lat` | float | Location latitude |
| `lon` | float | Location longitude |
| `timezone` | string | IANA timezone string |

**Returns:** JSON with `verdict` (auspicious/mixed_favorable/mixed/inauspicious), `score`, `positive_factors`, `negative_factors`, `panchang_suddhi`, and `marriage_doshas` (for marriage activity).

### `analyze_career_chart`

Analyzes career potential using the 10th house, D10 Dashamsha, and planetary significations.

| Parameter | Type | Description |
|-----------|------|-------------|
| `dob` | string | Date of birth — `"YYYY-MM-DD"` |
| `time` | string | Time of birth — `"HH:MM"` (24-hour) |
| `lat` | float | Birth latitude |
| `lon` | float | Birth longitude |
| `timezone` | string | IANA timezone string |

**Returns:** JSON with `tenth_house` info, `d10_indicators` (planet-by-planet D10 analysis), `career_themes` (ranked career domains), and `strength_factors`.

## RishiAI Agent Setup

The `.agents/` directory configures the **RishiAI** persona for AI coding assistants (Antigravity, VS Code Copilot, etc.):

- **`rules/rishi-ai.md`** (`trigger: always_on`) — the persistent persona and tool reference loaded on every message. Documents all 5 MCP tools, their parameters and return schemas, and the interpretation methodology.
- **`workflows/`** — 12 topic-specific analysis workflows invoked via slash commands (e.g., `/career-analysis`, `/muhurtha-analysis`).

The `.cursor/rules/rishi-ai.mdc` file mirrors the same rules for Cursor IDE users.

## Ayanamsha

All calculations use the **Lahiri (Chitrapaksha)** ayanamsha, the official standard of the Indian government and the most widely used system in Vedic astrology.

## References

- *Brihat Parashara Hora Shastra* — foundational text for Vedic astrology
- [Swiss Ephemeris](https://www.astro.com/swisseph/) — high-precision astronomical computation library
- [Model Context Protocol](https://modelcontextprotocol.io/) — open protocol for AI tool integration

## License

This project is for personal and educational use.
