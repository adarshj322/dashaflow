---
description: Marriage & Spouse Analysis Workflow
---
# Marriage Analysis Workflow

When performing a marriage analysis, execute the following steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart` for the native.
2. **Compatibility (only if BOTH people's birth details are provided)**: Call `calculate_compatibility` for the full compatibility report. This now returns:
   - **8 Ashtakoot kutas** (36 pts): Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi
   - **Additional kutas**: Mahendra (longevity), Stree Deergha (prosperity), Vedha (affliction), Rajju (marital durability), BadConstellations (inauspicious padas), LagnaHouse7 (ascendant cross-check), SexEnergy (physical compatibility)
   - **Exception logic**: Nadi dosha mitigated by Bhakoot+Rajju; Rajju mitigated by GrahaMaitri+Bhakoot+Tara+Mahendra
   - **Kuja Dosha**: Mars/Saturn/Rahu/Ketu/Sun in houses 2,4,7,8,12 with dignity-based scoring and compatibility match
   - Scores above 18/36 are acceptable; above 28/36 is excellent. If only the native's details are available, skip this step.
3. **Kuja Dosha (Manglik)**: From the compatibility output, review `kuja_dosha.male` and `kuja_dosha.female` scores and the `compatibility` verdict. A mismatch where one partner has severe Manglik dosha and the other has none is a significant concern.
4. **Darakaraka (Spouse Soul)**: From `jaimini_karakas`, identify the Darakaraka — the planet with the second-lowest degree. Its sign, house, and dignity indicate the nature of the spouse.
5. **7th House (Partnership)**:
   - Analyze the 7th house and its lord (dignity, `shadbala.percentage`, placement, aspects).
   - Check for malefics (Saturn, Mars, Rahu, Ketu, Sun) placed in or aspecting the 7th.
6. **Karaka**: Analyze Venus (for males) or Jupiter (for females) — their dignity and Shadbala strength determine the quality of marital life.
7. **D9 (Navamsha)**: Cross-reference the 7th lord, Venus/Jupiter, and Darakaraka in the `d9_sign` chart. D9 reveals the actual reality of married life, not just the promise in D1. Also check `d2_sign` (Hora) for wealth in marriage.
8. **Timing**: Analyze active Dashas (all 5 levels: Maha → Antar → Pratyantar → Sukshma → Prana) of the 7th lord, Darakaraka, and Venus/Jupiter. Check transits (Jupiter over 7th house/lord, Venus activation) and their `sav_points`.
9. **Muhurtha (if planning wedding date)**: Use `check_muhurtha` with activity `marriage` to evaluate proposed wedding dates for Panchang purity and marriage-specific doshas (Sagraha, Shashtashta, Bhrigupta Shatka, Kujaasthama).
10. **Synthesize**: Deliver an honest reading on marital timing, nature of the spouse, and potential challenges or blessings. Always pair difficult findings with Sattvic remedies.
11. **Upapada Lagna (UL)**: From `upapada`, check the UL sign and its lord — this indicates the nature and circumstances of the spouse. The 2nd from UL indicates marriage sustenance; malefics there threaten continuity.
12. **Dara Pada (A7)**: From `arudha_padas`, check A7 (Dara Pada) — the worldly perception and social standing of the spouse.
13. **Karakamsha**: From `karakamsha`, check planets in the Karakamsha sign and the 7th from Karakamsha for additional spouse indications.
14. **Bhava Chalit**: Compare the 7th lord's whole-sign house with `bhava_chalit` placement — if it shifts to the 6th or 8th in Chalit, the marriage promise is weakened despite D1 placement.
15. **Gandanta & Kaal Sarpa**: If the 7th lord or Venus/Jupiter is in `gandanta`, marriage carries karmic intensity. If `kaal_sarpa.active`, nodal karma dominates all life areas including marriage.
