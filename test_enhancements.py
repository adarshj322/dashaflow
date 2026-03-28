import json
from vedic_calculator import calculate_vedic_chart, calculate_transit
from mcp_server import calculate_compatibility

def run_tests():
    print("=== Testing Natal Chart (D7, D12, D60, Ashtakavarga) ===")
    chart1 = calculate_vedic_chart("1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")
    
    # Assert new Vargas are present
    assert "d7_sign" in chart1["lagna"], "D7 missing from Lagna"
    assert "d60_sign" in chart1["planets"]["Sun"], "D60 missing from Sun"
    
    # Assert Ashtakavarga
    assert "ashtakavarga" in chart1, "Ashtakavarga missing from chart"
    assert chart1["ashtakavarga"]["total_bindus"] == 337, f"Total Bindus must be 337, got {chart1['ashtakavarga']['total_bindus']}"
    
    print("Natal Enhancements: PASS ✅")
    
    print("\n=== Testing Transit (SAV Points) ===")
    transit = calculate_transit("2026-02-28", chart1)
    
    assert "sav_points" in transit["planets"]["Saturn"], "SAV points missing in transit Saturn"
    print("Transit Enhancements: PASS ✅")
    
    print("\n=== Testing Compatibility (Ashtakoot) ===")
    # Using a dummy second person for match
    chart2 = calculate_vedic_chart("1992-08-20", "10:15", 28.6139, 77.2090, "Asia/Kolkata")
    
    compat_json = calculate_compatibility(
        "1990-04-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata",
        "1992-08-20", "10:15", 28.6139, 77.2090, "Asia/Kolkata"
    )
    compat = json.loads(compat_json)
    
    assert "total_score" in compat, "total_score missing from compatibility"
    assert "scores" in compat, "scores breakdown missing"
    assert compat["max_score"] == 36.0, "max score is not 36"
    
    print(f"Match Score: {compat['total_score']} / 36")
    print("Matchmaking Enhancement: PASS ✅")

if __name__ == "__main__":
    run_tests()
