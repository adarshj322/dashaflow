---
description: Dating & General Relationships Analysis Workflow
---
# Relationship Analysis Workflow

For dating, romance, and general relationship analysis (pre-marriage or non-marital):

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart` for the native.
2. **Compatibility (only if BOTH people's birth details are provided)**: Call `calculate_compatibility` for the full compatibility report with 8 Ashtakoot kutas (36 pts) plus additional factors: Mahendra, Stree Deergha, Vedha, Rajju, SexEnergy, and Kuja Dosha analysis. Even in non-marital contexts this reveals magnetic attraction (Yoni, Graha Maitri, SexEnergy) and emotional compatibility (Tara, Nadi). If only the native's details are provided, skip this step and analyze romantic prospects from the chart alone.
3. **Darakaraka**: From `jaimini_karakas`, identify the Darakaraka (the second-lowest degree planet) — it reveals the soul-type the native is drawn to romantically.
4. **Romance (5th House)**: Analyze the 5th house and its lord — romance, courtship, infatuation, and emotional joy. Check `dignity` and `shadbala.percentage` of the 5th lord.
5. **Partnership (7th House)**: Analyze the 7th house for depth of commitment and long-term potential.
6. **Karaka**: Analyze Venus (love and attraction) and Moon (emotional needs and attachment style).
7. **Friction Points**: Check the 6th house (conflicts/breakups) and the 12th house for secret or hidden relationship dynamics.
8. **Timing**: Evaluate current Dashas and transits regarding romantic activations — Jupiter/Venus Dasha periods, and transits over the 5th/7th houses with their `sav_points`.
9. **Upapada Lagna (UL)**: From `upapada`, check the UL sign and its lord — this indicates the nature and circumstances of the partner. The 2nd from UL shows whether the relationship can sustain.
10. **Dara Pada (A7)**: From `arudha_padas`, check A7 — the worldly perception and social standing of the partner.
11. **Karakamsha**: From `karakamsha`, check the 7th sign from the Karakamsha for additional partner indications and relationship inclinations.
12. **Bhava Chalit**: Compare the 5th and 7th lord whole-sign houses with `bhava_chalit` placements — if a lord shifts bhavas, the romantic/partnership promise may manifest differently than the Rashi chart suggests.
13. **Avasthas**: Check `avasthas` for Venus and the 7th lord — Yuva = full romantic delivery; Bala/Mrita = diminished capacity for love expression.
14. **Synthesize**: Detail their romantic tendencies, attachment style, type of partner they attract, and the current relationship weather.
