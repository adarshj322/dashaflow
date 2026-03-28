# RishiAI — Vedic Astrology MCP Server

A Vedic astrology engine exposed as an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server, built on the **Swiss Ephemeris** with **Sidereal Lahiri** ayanamsha. Designed to power AI astrologer agents (like the included **RishiAI** persona) with astronomically precise chart data rooted in *Brihat Parashara Hora Shastra* (BPHS).

## Features

- **Natal Chart Casting** — Ascendant (Lagna), all nine Vedic grahas (Sun through Ketu), whole-sign houses, nakshatras with padas, and planetary dignities
- **Divisional Charts** — D3, D4, D7, D9, D10, D12, D24, D30, D60 sign placements for every planet and the Lagna
- **Planetary Strength** — Dignity classification, combustion detection (BPHS orbs), retrograde status, Digbala (directional strength), and **Shadbala** (six-fold mathematical strength as Rupas and % of required strength)
- **Jaimini Karakas** — All 7 Karakas by degree (Atmakaraka, Amatyakaraka, Bhratrukaraka, Matrukaraka, Putrakaraka, Gnatikaraka, Darakaraka)
- **Ashtakavarga** — Sarvashtakavarga (SAV) and Bhinnashtakavarga (BAV) points per sign for all 7 classical planets
- **BPHS Aspects** — Standard 7th-house aspects for all planets, plus special aspects for Mars (4th/8th), Jupiter (5th/9th), and Saturn (3rd/10th)
- **Vimshottari Dasha** — Full 120-year Mahadasha timeline, with active Mahadasha, Antardasha, and Pratyantardasha for any query date
- **Yoga Detection** — Pancha Mahapurusha, Gajakesari, Budhaditya, Chandra-Mangal, Kemadruma, Adhi Yoga, Raj Yoga, Viparita Raj Yoga, and Neecha Bhanga Raja Yoga
- **Panchang** — Birth Tithi, Vara (weekday lord), Nakshatra, Panchang Yoga, and Karana
- **Transit Overlay** — Current planetary positions mapped to natal houses (from Lagna and Moon), SAV transit points, Sade Sati detection with phase, and Rahu-Ketu transit axis
- **Ashtakoot Compatibility** — 36-point matchmaking (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi)

## Architecture

```
mcp_server.py              MCP entry point — exposes 3 tools
  └── vedic_calculator.py  Core engine — Swiss Ephemeris computations & chart assembly
        ├── constants.py   Zodiac signs, sign lords, nakshatras, dasha years, dignity tables
        ├── nakshatra.py   Nakshatra lookup from longitude
        ├── panchang.py    Tithi, Vara, Yoga, Karana calculations
        ├── yoga.py        Yoga detection logic
        ├── dasha.py       Vimshottari Dasha period computation
        ├── dignity.py     Dignity, combustion, digbala, compound relationships
        ├── ashtakavarga.py SAV & BAV calculations
        ├── jaimini.py     7-Karaka calculation by degree
        ├── shadbala.py    Six-fold planetary strength (Shadbala)
        └── matchmaking.py 36-point Ashtakoot compatibility

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
cd Astrology_script_antigrqavity

pip install swisseph pytz mcp
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

**Returns:** JSON with `metadata`, `panchang`, `lagna` (with D3–D60 signs), `planets` (with dignity, combustion, Shadbala, Jaimini karakas, all Varga signs, aspects), `dashas`, `yogas`, `ashtakavarga`, `jaimini_karakas`, `shadbala`.

### `cast_transit_chart`

Calculates planetary transits overlaid on a natal chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| `transit_date` | string | Date to compute transits — `"YYYY-MM-DD"` |
| `natal_chart_json` | string | Full JSON output from `cast_vedic_chart` |
| `timezone` | string | Optional — defaults to `"Asia/Kolkata"` |

**Returns:** JSON with transit `planets` (sign, degree, nakshatra, `sav_points`, house from Lagna/Moon), `sade_sati` status and phase, and `rahu_ketu_axis`.

### `calculate_compatibility`

Calculates traditional 36-point Ashtakoot compatibility. Person 1 = Male, Person 2 = Female.

| Parameter | Type | Description |
|-----------|------|-------------|
| `dob1`, `time1`, `lat1`, `lon1`, `tz1` | various | Birth details for Person 1 (Male) |
| `dob2`, `time2`, `lat2`, `lon2`, `tz2` | various | Birth details for Person 2 (Female) |

**Returns:** Score breakdown (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi) and total out of 36.

## RishiAI Agent Setup (Antigravity)

The `.agents/` directory configures the **RishiAI** persona for the [Antigravity](https://antigravity.sh) AI coding assistant:

- **`rules/rishi-ai.md`** (`trigger: always_on`) — the persistent persona and tool reference loaded on every message.
- **`workflows/`** — topic-specific analysis workflows invoked by typing `/workflow-name` in chat (e.g., `/career-analysis`).

## Ayanamsha

All calculations use the **Lahiri (Chitrapaksha)** ayanamsha, the official standard of the Indian government and the most widely used system in Vedic astrology.

## References

- *Brihat Parashara Hora Shastra* — foundational text for Vedic astrology
- [Swiss Ephemeris](https://www.astro.com/swisseph/) — high-precision astronomical computation library
- [Model Context Protocol](https://modelcontextprotocol.io/) — open protocol for AI tool integration

## License

This project is for personal and educational use.
