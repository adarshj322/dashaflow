---
description: Dating & General Relationships Analysis Workflow
---
# Relationship Analysis Workflow

For dating, romance, and general relationship analysis (pre-marriage or non-marital):

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart` for the native.
2. **Compatibility (only if BOTH people's birth details are provided)**: Call `calculate_compatibility` for the 36-point Ashtakoot score. Even in non-marital contexts this reveals magnetic attraction (Yoni, Graha Maitri) and emotional compatibility (Tara, Nadi). If only the native's details are provided, skip this step and analyze romantic prospects from the chart alone.
3. **Darakaraka**: From `jaimini_karakas`, identify the Darakaraka (the second-lowest degree planet) — it reveals the soul-type the native is drawn to romantically.
4. **Romance (5th House)**: Analyze the 5th house and its lord — romance, courtship, infatuation, and emotional joy. Check `dignity` and `shadbala.percentage` of the 5th lord.
5. **Partnership (7th House)**: Analyze the 7th house for depth of commitment and long-term potential.
6. **Karaka**: Analyze Venus (love and attraction) and Moon (emotional needs and attachment style).
7. **Friction Points**: Check the 6th house (conflicts/breakups) and the 12th house for secret or hidden relationship dynamics.
8. **Timing**: Evaluate current Dashas and transits regarding romantic activations — Jupiter/Venus Dasha periods, and transits over the 5th/7th houses with their `sav_points`.
9. **Synthesize**: Detail their romantic tendencies, attachment style, type of partner they attract, and the current relationship weather.
