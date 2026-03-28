"""
Test Phase 2 Enhancements:
1. Jaimini Karakas
2. Shadbala
3. D24, D30, fixed D60
4. Fixed Vashya in matchmaking
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vedic_calculator import calculate_vedic_chart
from matchmaking import calculate_ashtakoot

# --- Test natal chart with all Phase 2 features ---
print("=== Testing Phase 2: Natal Chart ===")
chart = calculate_vedic_chart("1999-10-22", "04:20", 11.7480, 75.4890, "Asia/Kolkata")

# Test Jaimini Karakas
assert "jaimini_karakas" in chart, "Missing jaimini_karakas!"
karakas = chart["jaimini_karakas"]
assert "Atmakaraka" in karakas, "No Atmakaraka found!"
assert "Darakaraka" in karakas, "No Darakaraka found!"
ak = karakas["Atmakaraka"]
print(f"  Atmakaraka: {ak['planet']} at {ak['degree']}° in {ak['sign']}")
print(f"  Darakaraka: {karakas['Darakaraka']['planet']}")
# Verify degree ordering (AK must have highest degree)
ak_deg = ak["degree"]
dk_deg = karakas["Darakaraka"]["degree"]
assert ak_deg >= dk_deg, f"AK degree ({ak_deg}) must be >= DK degree ({dk_deg})"
print("  Jaimini Karakas: PASS ✅")

# Test Shadbala
assert "shadbala" in chart, "Missing shadbala!"
shadbala = chart["shadbala"]
assert len(shadbala) == 7, f"Expected 7 planets in Shadbala, got {len(shadbala)}"
for planet, data in shadbala.items():
    assert "total_rupas" in data, f"Missing total_rupas for {planet}"
    assert "is_strong" in data, f"Missing is_strong for {planet}"
    assert "strength_ratio" in data, f"Missing strength_ratio for {planet}"
    print(f"  {planet}: {data['total_rupas']} Rupas (required: {data['required_rupas']}) {'💪' if data['is_strong'] else '⚠️'}")
print("  Shadbala: PASS ✅")

# Test D24 and D30 in planets
sun = chart["planets"]["Sun"]
assert "d24_sign" in sun, "Missing d24_sign in planet data!"
assert "d30_sign" in sun, "Missing d30_sign in planet data!"
print(f"  Sun D24={sun['d24_sign']}, D30={sun['d30_sign']}")
print("  D24/D30: PASS ✅")

# Test D24 and D30 in lagna
assert "d24_sign" in chart["lagna"], "Missing d24_sign in lagna!"
assert "d30_sign" in chart["lagna"], "Missing d30_sign in lagna!"
print(f"  Lagna D24={chart['lagna']['d24_sign']}, D30={chart['lagna']['d30_sign']}")
print("  Lagna D24/D30: PASS ✅")

# --- Test Matchmaking with fixed Vashya ---
print("\n=== Testing Phase 2: Fixed Vashya Matchmaking ===")
# Leo (Vanachara) vs Aries (Chatushpada) — should score 0 (wild eats quadruped)
match_result = calculate_ashtakoot(120.0, 10.0)  # Leo Moon vs Aries Moon
vashya_score = match_result["scores"]["Vashya"]
print(f"  Leo vs Aries Vashya: {vashya_score} (expected 0.0)")
assert vashya_score == 0.0, f"Vashya should be 0.0 for Leo vs Aries, got {vashya_score}"

# Same sign should still be 2
match_same = calculate_ashtakoot(10.0, 15.0)  # Both Aries Moon
vashya_same = match_same["scores"]["Vashya"]
assert vashya_same == 2.0, f"Same-sign Vashya should be 2.0, got {vashya_same}"
print(f"  Same-sign Vashya: {vashya_same} (expected 2.0)")
print("  Fixed Vashya: PASS ✅")

print("\n🎉 ALL PHASE 2 TESTS PASSED! 🎉")
