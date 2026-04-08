# DashaFlow

[![PyPI version](https://img.shields.io/pypi/v/dashaflow)](https://pypi.org/project/dashaflow/)
[![CI](https://github.com/adarshj322/dashaflow/actions/workflows/ci.yml/badge.svg)](https://github.com/adarshj322/dashaflow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/dashaflow)](https://pypi.org/project/dashaflow/)

A Vedic astrology calculation engine for Python, built on the **Swiss Ephemeris** with **Sidereal Lahiri** ayanamsha. Rooted in *Brihat Parashara Hora Shastra* (BPHS) and B.V. Raman's *Hindu Predictive Astrology*.

```bash
pip install dashaflow
```

## Quick Start

```python
import dashaflow

# Cast a natal chart
chart = dashaflow.cast_chart("1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")

print(chart["lagna"]["sign"])              # "Leo"
print(chart["planets"]["Moon"]["nakshatra"])  # "Ashwini"
print(chart["planets"]["Jupiter"]["dignity"]) # "exalted"
print(chart["dashas"]["maha"]["planet"])      # Current Mahadasha lord
print(chart["yogas"])                         # Detected yogas

# Transits
transit = dashaflow.cast_transit(
    "2026-03-29", "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata"
)
print(transit["sade_sati"])

# Compatibility (Person 1 = Male, Person 2 = Female)
compat = dashaflow.calculate_compatibility(
    "1990-04-15", "14:30", 28.61, 77.21, "Asia/Kolkata",
    "1992-08-20", "09:15", 19.07, 72.87, "Asia/Kolkata",
)
print(f"Score: {compat['total']}/36")

# Muhurtha (electional astrology)
muhurtha = dashaflow.check_muhurtha("marriage", "2026-11-15", "10:30", 28.61, 77.21, "Asia/Kolkata")
print(muhurtha["verdict"])  # "auspicious" / "mixed" / "inauspicious"

# Career analysis
career = dashaflow.analyze_career("1990-04-15", "14:30", 28.61, 77.21, "Asia/Kolkata")
print(career["career_themes"])
```

## API

### Top-Level Functions

| Function | Description |
|---|---|
| `cast_chart(dob, time, lat, lon, timezone, query_date=None, ephe_path='')` | Complete natal chart — planets, dashas, yogas, ashtakavarga, shadbala, vargas, and more |
| `cast_transit(transit_date, dob_str, time_str, lat, lon, timezone="Asia/Kolkata")` | Planetary transits overlaid on natal chart with SAV points, Sade Sati, Rahu-Ketu axis |
| `calculate_compatibility(dob1, time1, lat1, lon1, tz1, dob2, time2, lat2, lon2, tz2)` | 36-point Ashtakoot + extended kutas + Kuja Dosha |
| `check_muhurtha(activity, date, time, lat, lon, timezone)` | Electional astrology for 6 activity types |
| `analyze_career(dob, time, lat, lon, timezone)` | D10 Dashamsha career analysis with theme recommendations |

### Sub-Module Access

```python
from dashaflow.dasha import calculate_dashas
from dashaflow.matchmaking import calculate_ashtakoot
from dashaflow.shadbala import calculate_shadbala
from dashaflow.jaimini import calculate_jaimini_karakas, calculate_arudha_padas
from dashaflow.yoga import detect_yogas, detect_kaal_sarpa
from dashaflow.ashtakavarga import calculate_ashtakavarga
```

### `cast_chart()` Returns

| Key | Description |
|---|---|
| `metadata` | DOB, time, coordinates, ayanamsha (Lahiri), query date |
| `panchang` | Tithi, Vara, Nakshatra, Yoga, Karana |
| `lagna` | Ascendant sign, degree, nakshatra, pada, D2–D60 signs |
| `planets` | Per planet: sign, degree, house, nakshatra, pada, dignity, combustion, retrograde, digbala, aspects, 14 varga signs |
| `dashas` | 5 levels: Maha, Antar, Pratyantar, Sukshma, Prana + 120-year timeline |
| `yogas` | 24 types detected with forming planets and descriptions |
| `ashtakavarga` | SAV, BAV, Prashtara (source-level bindus) |
| `jaimini_karakas` | 7 Karakas by degree (Atmakaraka through Darakaraka) |
| `shadbala` | Six-fold strength in Rupas + percentage + Ishta/Kashta Phala |
| `bhava_chalit` | Equal-house Bhava Chalit with planet placements per bhava |
| `avasthas` | Planetary age-states: Bala, Kumara, Yuva, Vriddha, Mrita |
| `kaal_sarpa` | Kaal Sarpa Dosha detection (full/partial, ascending/descending) |
| `graha_yuddha` | Planetary war — pairs within 1° with winner/loser |
| `gandanta` | Planets at water-fire sign boundaries (karmic knots) |
| `arudha_padas` | All 12 Arudha Padas (A1–A12) with BPHS exception rule |
| `upapada` | Upapada Lagna (A12) with lord and 2nd from UL |
| `karakamsha` | AK in Navamsha, Ishta Devata, planets in Karakamsha |

## Features

- **Natal Chart** — Lagna, 9 grahas, whole-sign houses, nakshatras with padas, dignities
- **14 Divisional Charts** — D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D60
- **Planetary Strength** — Dignity (B.V. Raman), combustion (BPHS orbs), Digbala, Shadbala (6-fold), Ishta/Kashta Phala
- **BPHS Aspects** — 7th for all, special aspects for Mars (4th/8th), Jupiter (5th/9th), Saturn (3rd/10th)
- **Vimshottari Dasha** — 5 levels (Maha → Antar → Pratyantar → Sukshma → Prana), 120-year timeline
- **24 Yoga Types** — Pancha Mahapurusha, Gajakesari, Budhaditya, Raj Yoga, Neecha Bhanga, Parivartana, Dhana, and more
- **Ashtakavarga** — SAV, BAV, Prashtara (source-level bindu contributions)
- **Jaimini** — 7 Karakas, Arudha Padas (A1–A12), Upapada Lagna, Karakamsha
- **Compatibility** — 8 Ashtakoot kutas (36 pts) + Mahendra, Stree Deergha, Vedha, Rajju, Kuja Dosha
- **Muhurtha** — 6 activity types with Panchang Suddhi and marriage doshas
- **Career** — D10 analysis with planet-career significations and domain recommendations
- **Bhava Chalit** — Equal-house chart from Lagna midpoint
- **Avasthas** — 5 planetary age-states per BPHS
- **Kaal Sarpa, Graha Yuddha, Gandanta** — Dosha and junction detection

## Architecture

```
dashaflow/
├── __init__.py         Public API (5 functions)
├── vedic_calculator.py Core engine — Swiss Ephemeris computations
├── constants.py        Zodiac, nakshatras, dignity tables
├── nakshatra.py        Nakshatra lookup from longitude
├── panchang.py         Tithi, Vara, Yoga, Karana
├── yoga.py             24 yoga types + Kaal Sarpa, Graha Yuddha, Gandanta
├── dasha.py            Vimshottari Dasha (5 levels)
├── dignity.py          Dignity, combustion, digbala
├── ashtakavarga.py     SAV, BAV, Prashtara
├── jaimini.py          Karakas, Arudha Padas, Upapada, Karakamsha
├── shadbala.py         Six-fold strength + Ishta/Kashta Phala
├── matchmaking.py      16-factor compatibility + Kuja Dosha
├── muhurtha.py         Electional astrology
└── career.py           D10 career analysis
```

## Ayanamsha

All calculations use **Lahiri (Chitrapaksha)** — the official standard of the Indian government and the most widely used system in Vedic astrology.

## Extended Ephemeris

The bundled Swiss Ephemeris files cover ~1800–2400 AD. For historical or far-future charts, download additional `.se1` files from [astro.com](https://www.astro.com/swisseph/) and pass the path:

```python
chart = dashaflow.cast_chart("1200-03-10", "12:00", 28.61, 77.21, "Asia/Kolkata",
                              ephe_path="/path/to/extended/ephemeris")
```

## References

- *Brihat Parashara Hora Shastra* — foundational text for Vedic astrology
- *Hindu Predictive Astrology* — B.V. Raman
- [Swiss Ephemeris](https://www.astro.com/swisseph/) — high-precision astronomical computation

## License

MIT

