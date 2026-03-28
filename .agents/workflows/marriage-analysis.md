---
description: Marriage & Spouse Analysis Workflow
---
# Marriage Analysis Workflow

When performing a marriage analysis, execute the following steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart` for the native.
2. **Compatibility (only if BOTH people's birth details are provided)**: Call `calculate_compatibility` for the 36-point Ashtakoot score (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi). Scores above 18/36 are acceptable; above 28/36 is excellent. If only the native's details are available, skip this step entirely and analyze marriage prospects from the chart alone.
3. **Darakaraka (Spouse Soul)**: From `jaimini_karakas`, identify the Darakaraka — the planet with the second-lowest degree. Its sign, house, and dignity indicate the nature of the spouse.
4. **7th House (Partnership)**:
   - Analyze the 7th house and its lord (dignity, `shadbala.percentage`, placement, aspects).
   - Check for malefics (Saturn, Mars, Rahu, Ketu, Sun) placed in or aspecting the 7th.
5. **Karaka**: Analyze Venus (for males) or Jupiter (for females) — their dignity and Shadbala strength determine the quality of marital life.
6. **D9 (Navamsha)**: Cross-reference the 7th lord, Venus/Jupiter, and Darakaraka in the `d9_sign` chart. D9 reveals the actual reality of married life, not just the promise in D1.
7. **Timing**: Analyze active Dashas of the 7th lord, Darakaraka, and Venus/Jupiter. Check transits (Jupiter over 7th house/lord, Venus activation) and their `sav_points`.
8. **Synthesize**: Deliver an honest reading on marital timing, nature of the spouse, and potential challenges or blessings. Always pair difficult findings with Sattvic remedies.
