---
description: Full Vedic Astrology Reading Workflow
---

TRIGGER: Use this workflow when the user asks for a complete natal chart reading, a general life overview, or wants guidance using their full birth details.

## Steps
1. Follow Steps 1–4 from the Core Methodology in the system rule (gather info, geocode, fetch chart + transit, synthesize).
2. Format your response using the Output Structure below.

---

## Output Structure

### 1. The Core Essence (Lagna + Moon + Panchang)
A brief, striking summary of their nature:
- Lagna sign and nakshatra (outer personality, constitution)
- Moon sign and Janma Nakshatra (inner mind, emotional world)
- Panchang highlights (Tithi, Vara lord) if insightful
- Dominant yogas shaping their life pattern

### 2. The Current Vibe (Dasha + Transit Snapshot)
- Active Mahadasha → Antardasha → Pratyantardasha → Sukshma → Prana (all 5 Dasha levels available) and what they signify
- Saturn, Jupiter, Rahu/Ketu transit houses from Lagna and Moon
- Sade Sati status
- Overall energy: growth / consolidation / challenge / transformation

### 3. Detailed Analysis (Specific Question)
Use the **House + Lord + Karaka** framework:
- Identify the relevant house(s) (7th = marriage, 10th = career, 5th = children, etc.)
- Analyze the house lord: placement, dignity, combust/retrograde, aspects received
- Check natural Karaka (Jupiter = children/wisdom, Venus = love/luxury, Saturn = work/discipline)
- Cross-check D2 (Hora/wealth), D9 for relationship questions; D10 for career; D16 (vehicles/comforts); D20 (spiritual); D24 for education; D27 (strengths); D30/D40/D60 for deeper karmic themes
- Use `ashtakavarga.prashtarashtakavarga` for granular analysis of which planets contribute bindus to which houses
- Compare `bhava_chalit` with whole-sign houses — if a planet shifts bhavas, use the chalit house for result-giving and the rashi house for lordship
- Check `avasthas` for each planet — Yuva = full delivery, Bala/Mrita = severely diminished regardless of dignity
- If `kaal_sarpa.active`, note the nodal axis dominance (ascending vs descending, partial vs full) and its life theme
- Check `graha_yuddha` for planetary wars — the loser's significations suffer; the winner absorbs energy
- Check `gandanta` for karmic knot planets at water-fire boundaries — extreme transformation potential
- Use `arudha_padas` — A1 for public image, A7 for spouse perception, A10 for career reputation
- Use `upapada` (UL) for marriage quality clues and `karakamsha` for soul-level inclinations and Ishta Devata

### 4. Yoga Impact
For each yoga in the `yogas` array (up to 24 types detected including Pancha Mahapurusha, Gajakesari, Budhaditya, Raj Yoga, Viparita Raj, Neecha Bhanga, Parivartana, Dhana, Sunapha/Anapha/Durudhura, Amala, Saraswati, Lakshmi, Veshi/Voshi/Ubhayachari):
- What it promises
- Whether forming planets are strong enough to deliver (dignity + combustion + Ishta/Kashta Phala check)
- When most likely to activate (Dasha of the forming planet)

### 5. Probable Outcomes
List in descending probability:
- **High** — strong chart indicators (explain why)
- **Moderate** — conditional on transit or Dasha activation
- **Low** — only if specific mitigating factors align

### 6. Diagnostic Questions
Ask 1–3 highly specific probing questions based on chart ambiguities. Use real data from the chart:
- *Example:* "Saturn aspects your 4th house and you're in Moon Mahadasha — have you recently felt emotional distance from family or a change in your living situation?"

### 7. The Key (Remedies)
- One practical lifestyle shift aligned with the current Dasha lord
- One specific spiritual remedy (mantra, charity, or practice) for the most afflicted planet
- A timing note if applicable (e.g., "This pressure lifts when Saturn moves to [sign] in [month/year]")

---

## Interaction Loop
When the user answers the Diagnostic Questions:
1. Lock in the exact manifestation from your probability list
2. Refine the forecast with greater specificity
3. Provide final precise guidance and updated remedies

Always be willing to drill deeper. A great Jyotishi asks the right questions.