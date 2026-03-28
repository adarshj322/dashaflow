---
description: Children & Progeny Analysis Workflow
---
# Children Analysis Workflow

When analyzing children/progeny matters, follow these steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart`.
2. **5th House (Putra Bhava)**: Analyze the 5th house from Lagna and Moon — sign, occupants, aspects.
3. **5th Lord**: Check the placement, dignity, and strength of the 5th lord. Is it combust? Retrograde? Afflicted?
4. **Putrakaraka (Jupiter)**: Assess Jupiter's dignity, house, and aspects. Jupiter is the natural significator of children.
5. **Jaimini Putrakaraka**: Check the Chara Putrakaraka (from `jaimini_karakas` data) — its sign, house, and D9 placement.
6. **D7 (Saptamsha)**: Cross-reference the 5th lord, Jupiter, and Lagna lord positions in the D7 divisional chart for deeper insights on:
   - Number and gender of children
   - Timing of children
   - Relationship with children
7. **Beeja/Kshetra Sphuta**: For males, check the Beeja Sphuta (Sun + Venus + Jupiter longitudes mod 360). For females, check the Kshetra Sphuta (Moon + Mars + Jupiter longitudes mod 360). The resulting sign and its lord indicate fertility potential.
8. **Timing**: Analyze the Dasha/Antardasha (all 5 levels: Maha → Antar → Pratyantar → Sukshma → Prana) of the 5th lord, Jupiter, and Putrakaraka for timing of childbirth. Check Jupiter and Saturn transits over the 5th house.
9. **Bhava Chalit**: Compare the 5th lord's whole-sign house with `bhava_chalit` placement — if it shifts to the 4th or 6th in Chalit, the progeny promise may weaken or delay.
10. **Avasthas**: Check `avasthas` for the 5th lord and Jupiter — Yuva = full fertility/progeny capacity; Bala/Mrita = diminished delivery regardless of dignity.
11. **Gandanta**: If the 5th lord or Jupiter is in `gandanta`, childbirth may carry karmic intensity or complications at water-fire sign boundaries.
12. **Synthesize**: Provide a clear reading on fertility, number of children, timing, and the native's relationship with their children.
