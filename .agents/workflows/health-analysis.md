---
description: Health & Vitality Analysis Workflow
---
# Health Analysis Workflow

When performing a health analysis, execute the following steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart`.
2. **Vitality (Lagna complex)**: Assess the Lagna, Lagna lord (dignity + `shadbala.percentage`), and the Sun (natural karaka for vitality and prana). A weakened Lagna lord or combust Sun indicates reduced constitutional strength.
3. **Acute Illness (6th House)**: Analyze the 6th house, its lord, and planets placed there. This shows the nature of diseases the native is susceptible to and their immune response.
4. **Chronic & Deep Issues (8th House)**: The 8th house governs chronic, sudden, or deep-seated health crises, surgeries, and longevity challenges.
5. **Trimshamsha (D30)**: Cross-reference the key afflicted planets in the `d30_sign` chart. D30 is the primary divisional chart for diseases and misfortunes — it reveals the type and root cause of health vulnerabilities.
6. **Hospitalization (12th House)**: Check the 12th house for bed confinement, hospitalization, and recovery from illness.
7. **Affliction Check**: Identify any planet with low `shadbala.percentage` (<80%), `is_combust: true`, or `dignity: "debilitated"` — these planets signal the body systems they govern are under stress.
8. **Timing**: Check if the current Dasha belongs to the 6th, 8th, or 12th lord, or a Maraka (2nd/7th lord). Check Saturn and Rahu transits over the Lagna or Moon using `sav_points` to judge severity.
9. **Synthesize**: Provide guidance on physical vulnerabilities, body systems at risk, and suggest Sattvic lifestyle/dietary changes based on elemental imbalances. Do NOT give medical diagnoses.
