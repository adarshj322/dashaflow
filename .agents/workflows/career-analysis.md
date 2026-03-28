---
description: Career & Profession Analysis Workflow
---
# Career Analysis Workflow

When performing a career analysis, execute the following steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` and `cast_transit_chart`.
2. **Amatyakaraka (Career Soul)**: From `jaimini_karakas`, identify the Amatyakaraka — it is the primary planet guiding career direction. Check its sign, house, dignity, and strength in Shadbala.
3. **Lagna & Core Nature**: Assess the Lagna and Lord to understand the native's baseline drive and work style.
4. **10th House (Karma/Profession)**:
   - Analyze the 10th house from Lagna and Moon.
   - Analyze the placement, dignity, Shadbala strength, and aspects of the 10th lord.
5. **Karaka**: Analyze Saturn (natural significator of work/discipline) and Sun (authority/status/fame). Check their `dignity` and `shadbala.percentage`.
6. **D10 (Dashamsha)**: Cross-reference the 10th lord, Lagna lord, and Amatyakaraka in the `d10_sign` chart for actual career manifestation.
7. **Wealth from Work**: Briefly check the 6th house (daily work/service), 2nd house (accumulated wealth), and 11th house (liquid income and gains).
8. **Timing**: Analyze the current Dasha lord's connection to the 10th house. Check Saturn and Jupiter transits (`house_from_lagna`) and their `sav_points` for activation quality.
9. **Synthesize**: Provide a brutal, constructive interpretation of career trajectory, likely professions, authority dynamics, and key timing windows.
