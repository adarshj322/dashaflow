---
description: Muhurtha (Electional Astrology) — Picking Auspicious Times
---
# Muhurtha Analysis Workflow

When helping the user pick an auspicious time for an activity, follow these steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` for the native. Call `cast_transit_chart` for the proposed date.
2. **Panchanga Shuddhi (Five-limb Purity)**: Verify the transit date's Panchang:
   - **Tithi**: Avoid Rikta Tithis (4, 9, 14). Nanda (1, 6, 11) and Purna (5, 10, 15) are best.
   - **Vara**: Match the weekday lord to the activity (e.g., Thursday/Jupiter for education, Friday/Venus for marriage).
   - **Nakshatra**: Avoid Bharani, Krittika, Ardra, Ashlesha, Jyeshtha, Moola for most activities. Fixed stars for permanent works, movable for travel.
   - **Yoga**: Avoid Vishkambha, Atiganda, Shula, Ganda, Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti.
   - **Karana**: Avoid Vishti (Bhadra) Karana entirely.
3. **Tarabala**: The transit Moon's nakshatra counted from the native's birth nakshatra must NOT fall in the 3rd (Vipat), 5th (Pratyak), or 7th (Vadha) Tara.
4. **Chandrabala**: The transit Moon must NOT be in the 6th, 8th, or 12th house from the native's birth Moon sign.
5. **Lagna Shuddhi**: The ascendant at the proposed time should be strong — avoid malefics in Lagna and the 8th house.
6. **Activity-Specific Rules**: Apply rules specific to the activity type (marriage, travel, business start, surgery, etc.).
7. **Synthesize**: Recommend the best time windows within the user's proposed date range. If the date is inauspicious, suggest alternatives with clear reasoning.
