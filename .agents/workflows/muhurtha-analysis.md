---
description: Muhurtha (Electional Astrology) — Picking Auspicious Times
---
# Muhurtha Analysis Workflow

When helping the user pick an auspicious time for an activity, follow these steps:

1. **Fetch Muhurtha Data**: Call `check_muhurtha` with the activity type, proposed date/time, and location. Supported activities: `marriage`, `travel`, `business`, `education`, `house_entry`, `medical`. The tool automatically evaluates Panchang purity, nakshatra suitability, activity-specific rules, and returns a verdict with score.
2. **Also Fetch Natal Chart (if birth details provided)**: Call `cast_vedic_chart` for the native and `cast_transit_chart` for the proposed date.
3. **Interpret Muhurtha Results**: Read the `check_muhurtha` output:
   - `verdict`: "auspicious" / "mixed_favorable" / "mixed" / "inauspicious"
   - `positive_factors` and `negative_factors`: specific reasons for/against the time
   - `marriage_doshas` (marriage only): Sagraha, Shashtashta, Bhrigupta Shatka, Kujaasthama checks
   - `panchang_suddhi`: tithi/vara/nakshatra/yoga/karana assessment
4. **Tarabala** (if native's birth data available): The transit Moon's nakshatra counted from the native's birth nakshatra must NOT fall in the 3rd (Vipat), 5th (Pratyak), or 7th (Vadha) Tara.
5. **Chandrabala** (if native's birth data available): The transit Moon must NOT be in the 6th, 8th, or 12th house from the native's birth Moon sign.
6. **Lagna Shuddhi**: Check transit chart — avoid malefics in Lagna and the 8th house at the proposed time.
7. **Gandanta Moon**: If the transit Moon at the proposed time falls in `gandanta` (within 3°20' of Cancer→Leo, Scorpio→Sagittarius, or Pisces→Aries boundaries), the muhurtha is karmically risky — avoid for auspicious beginnings.
8. **Kaal Sarpa**: If the transit chart at the proposed time shows `kaal_sarpa.active`, all planets hemmed between Rahu-Ketu — the elected time carries heavy nodal karma and should generally be avoided for new ventures.
9. **Synthesize**: Combine the `check_muhurtha` score/verdict with your Tarabala/Chandrabala/Lagna analysis. Recommend the best time windows within the user's proposed date range. If inauspicious, suggest alternatives with clear reasoning.
