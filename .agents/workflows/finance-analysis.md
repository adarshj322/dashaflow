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
6. **Yogas**: Look specifically for Dhana Yogas (lords of 1, 2, 5, 9, 11 in mutual connection) and Daridra Yogas (poverty-causing combinations) in the `yogas` array.
7. **Ashtakavarga — Wealth Houses**: Check `ashtakavarga.sarvashtakavarga` points for the 2nd, 9th, and 11th signs. High SAV points (≥ 30) in these signs indicate financial abundance; low points (< 25) indicate struggle.
8. **Timing**: Analyze active Dashas invoking the 2nd/11th lords, Jupiter, or Amatyakaraka. Check Jupiter transits through wealth houses using `sav_points` to judge quality.
9. **Synthesize**: Give a direct reading on wealth accumulation potential, spending patterns, and key financial growth or restriction periods.
