---
description: Finance & Wealth Analysis Workflow
---
# Finance Analysis Workflow

When performing a finance analysis, execute the following steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart`.
2. **Amatyakaraka**: From `jaimini_karakas`, identify the Amatyakaraka. Its strength indicates the native's earning power and financial direction.
3. **Wealth Triangle**:
   - **2nd House**: Accumulated wealth, savings, family inheritance. Check lord's `dignity` and `shadbala.percentage`.
   - **11th House**: Liquid gains, profits, recurring income. Check lord's strength.
   - **9th House**: Fortune, luck, and past-life prosperity. A strong 9th lord amplifies all wealth indicators.
4. **Jupiter (Karaka)**: Natural significator of wealth and abundance. Check its `dignity`, `shadbala.percentage`, house placement, and aspects.
5. **Losses & Fluctuations**: Check the 12th house (expenses, hidden losses) and 8th house (sudden shocks, debts, other people's money).
6. **Yogas**: Look specifically for **Dhana Yogas** in the `yogas` array — the engine now detects specific Dhana Yoga combinations (lords of 1, 2, 5, 9, 11 in mutual connection). Also check for Lakshmi Yoga (Venus strong + 9th lord in Kendra/Trikona) and Saraswati Yoga. Check for Daridra Yogas (poverty-causing combinations).
7. **Ashtakavarga — Wealth Houses**: Check `ashtakavarga.sarvashtakavarga` points for the 2nd, 9th, and 11th signs. High SAV points (≥ 30) indicate financial abundance; < 25 = struggle. Use `ashtakavarga.prashtarashtakavarga` for granular analysis — see which specific planets contribute bindus to wealth-house signs.
8. **Ishta/Kashta Phala**: Check `shadbala.ishta_kashta_phala` for wealth-related planets (Jupiter, 2nd/11th lords). High Ishta Phala = auspicious results; high Kashta Phala = obstacles.
9. **Timing**: Analyze active Dashas (all 5 levels: Maha → Antar → Pratyantar → Sukshma → Prana) invoking the 2nd/11th lords, Jupiter, or Amatyakaraka. Check Jupiter transits through wealth houses using `sav_points` to judge quality.
10. **Arudha Padas**: From `arudha_padas`, check A1 (Arudha Lagna) — the native's perceived wealth and social status. Also check A11 (Labha Pada) for gains/income reputation. Planets aspecting A1 shape the financial image others see.
11. **Bhava Chalit**: Compare the 2nd and 11th lord whole-sign houses with `bhava_chalit` placements — if wealth lords shift bhavas in Chalit, the source or nature of income may differ from Rashi expectations.
12. **Avasthas**: Check `avasthas` for Jupiter, 2nd lord, and 11th lord — Yuva = full wealth-giving capacity; Mrita = severely diminished financial delivery.
13. **Synthesize**: Give a direct reading on wealth accumulation potential, spending patterns, and key financial growth or restriction periods.
