---
description: Career & Profession Analysis Workflow
---
# Career Analysis Workflow

When performing a career analysis, execute the following steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart`. Also call `analyze_career_chart` (same birth params) to get the D10-based career analysis with career themes, domain recommendations, and strength factors.
2. **Amatyakaraka (Career Soul)**: From `jaimini_karakas`, identify the Amatyakaraka — it is the primary planet guiding career direction. Check its sign, house, dignity, and strength in Shadbala. Cross-reference with `analyze_career_chart` output's `career_themes`.
3. **Lagna & Core Nature**: Assess the Lagna and Lord to understand the native's baseline drive and work style.
4. **10th House (Karma/Profession)**:
   - Analyze the 10th house from Lagna and Moon using both the natal chart and `analyze_career_chart` → `tenth_house` data.
   - Analyze the placement, dignity, Shadbala strength, and aspects of the 10th lord.
   - Check `shadbala.ishta_kashta_phala` for the 10th lord — high Ishta Phala confirms career-giving capacity.
5. **Karaka**: Analyze Saturn (natural significator of work/discipline) and Sun (authority/status/fame). Check their `dignity` and `shadbala.percentage`.
6. **D10 (Dashamsha)**: Use `analyze_career_chart` → `d10_indicators` for planet-by-planet D10 sign placements and their career domain significations. Cross-reference the 10th lord, Lagna lord, and Amatyakaraka in D10.
7. **Career Domains**: Merge the `career_themes` from `analyze_career_chart` (derived from planet significations and sign domains) with your own House-Lord-Karaka synthesis to recommend specific career fields.
8. **Wealth from Work**: Briefly check the 6th house (daily work/service), 2nd house (accumulated wealth), and 11th house (liquid income and gains). Use `ashtakavarga.prashtarashtakavarga` for granular SAV contribution analysis on wealth houses.
9. **Timing**: Analyze the current Dasha lord's connection to the 10th house. Use all 5 dasha levels (Maha → Antar → Pratyantar → Sukshma → Prana) for precise timing. Check Saturn and Jupiter transits (`house_from_lagna`) and their `sav_points` for activation quality.
10. **Synthesize**: Provide a brutal, constructive interpretation of career trajectory, likely professions, authority dynamics, and key timing windows. Reference the `strength_factors` from `analyze_career_chart` to support your conclusions.
11. **Arudha Padas**: From `arudha_padas`, check A1 (Arudha Lagna) for public image that drives career perception, and A10 (Karma Pada) for career reputation. Planets aspecting A10 shape the native's professional standing.
12. **Bhava Chalit**: Compare the 10th lord's whole-sign house with `bhava_chalit` placement — if it shifts bhavas in Chalit, the career expression may differ from the Rashi promise.
13. **Avasthas**: Check `avasthas` for the 10th lord and Amatyakaraka — Yuva state = full career capacity; Bala/Mrita = diminished professional delivery.
14. **Karakamsha**: From `karakamsha`, planets in the Karakamsha sign reveal the soul's deepest professional and worldly inclinations alongside the D10 analysis.
