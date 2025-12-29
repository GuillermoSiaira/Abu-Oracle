"""
Test Solar Return Ranking endpoint.
Validates Persian/Hellenistic scoring, city ordering, and fallback behavior.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.solar_return_ranking import (
    rank_solar_return_locations,
    score_solar_return_location,
    RELOCATION_CITIES
)


def test_ranking_structure():
    """Test that ranking returns correct structure with all required fields."""
    print("=== Testing Ranking Structure ===")
    
    birth_date = datetime(1990, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
    result = rank_solar_return_locations(birth_date, year=2025, city_names=["London", "Singapore"], top_n=2)
    
    # Validate top-level structure
    assert "top_recommendations" in result
    assert "rankings" in result
    assert "criteria" in result
    assert "cities_analyzed" in result
    assert "year" in result
    
    assert result["year"] == 2025
    assert result["cities_analyzed"] == 2
    assert len(result["top_recommendations"]) == 2
    assert len(result["rankings"]) == 2
    
    # Validate ranking entry structure
    ranking = result["rankings"][0]
    assert "city" in ranking
    assert "coordinates" in ranking
    assert "total_score" in ranking
    assert "breakdown" in ranking
    assert "chart_summary" in ranking
    
    # Validate breakdown structure
    breakdown = ranking["breakdown"]
    assert "dignities" in breakdown
    assert "angularity" in breakdown
    assert "solar_conditions" in breakdown
    assert "aspects_reception" in breakdown
    assert "sect" in breakdown
    
    print(f"✓ Structure valid for {result['cities_analyzed']} cities")
    print(f"  Top: {result['top_recommendations']}")
    print()


def test_ranking_order():
    """Test that cities are ranked in descending score order."""
    print("=== Testing Ranking Order ===")
    
    birth_date = datetime(1985, 3, 15, 8, 30, 0, tzinfo=timezone.utc)
    result = rank_solar_return_locations(
        birth_date, 
        year=2024, 
        city_names=["London", "Singapore", "Buenos Aires"],
        top_n=3
    )
    
    rankings = result["rankings"]
    scores = [r["total_score"] for r in rankings]
    
    print(f"Scores: {scores}")
    
    # Verify descending order
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1], f"Rankings not in order: {scores[i]} < {scores[i+1]}"
    
    # Top recommendations should match the first N cities
    top_cities = [r["city"] for r in rankings[:3]]
    assert result["top_recommendations"] == top_cities
    
    print(f"✓ Rankings correctly ordered (descending)")
    print()


def test_all_cities_default():
    """Test that omitting city_names uses all 16 predefined cities."""
    print("=== Testing Default All Cities ===")
    
    birth_date = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = rank_solar_return_locations(birth_date, year=2025, top_n=5)
    
    assert result["cities_analyzed"] == 16, f"Expected 16 cities, got {result['cities_analyzed']}"
    assert len(result["rankings"]) == 16
    assert len(result["top_recommendations"]) == 5
    
    # All cities should be from the predefined set
    city_names = {r["city"] for r in result["rankings"]}
    expected_cities = set(RELOCATION_CITIES.keys())
    assert city_names == expected_cities
    
    print(f"✓ All 16 cities analyzed")
    print(f"  Top 5: {result['top_recommendations']}")
    print()


def test_score_components():
    """Test that each score component contributes to total."""
    print("=== Testing Score Components ===")
    
    birth_date = datetime(1978, 7, 5, 21, 15, 0, tzinfo=timezone.utc)
    city_name = "Singapore"
    city_data = RELOCATION_CITIES[city_name]
    
    result = score_solar_return_location(
        birth_date,
        city_name,
        city_data["lat"],
        city_data["lon"],
        year=2025
    )
    
    breakdown = result["breakdown"]
    
    # Extract component scores
    dig_score = breakdown["dignities"]["total"]
    ang_score = breakdown["angularity"]["total"]
    sol_score = breakdown["solar_conditions"]["total"]
    rec_score = breakdown["aspects_reception"]["total"]
    sec_score = breakdown["sect"]["total"]
    
    computed_total = dig_score + ang_score + sol_score + rec_score + sec_score
    
    print(f"City: {city_name}")
    print(f"  Dignities: {dig_score}")
    print(f"  Angularity: {ang_score}")
    print(f"  Solar: {sol_score}")
    print(f"  Reception: {rec_score}")
    print(f"  Sect: {sec_score}")
    print(f"  Computed total: {computed_total}")
    print(f"  Reported total: {result['total_score']}")
    
    # Allow small floating-point tolerance
    assert abs(result["total_score"] - computed_total) < 0.01, \
        f"Total score mismatch: {result['total_score']} != {computed_total}"
    
    print(f"✓ Score components sum correctly")
    print()


def test_chart_summary():
    """Test that chart summary includes ASC, MC, and SR datetime."""
    print("=== Testing Chart Summary ===")
    
    birth_date = datetime(1995, 11, 22, 18, 0, 0, tzinfo=timezone.utc)
    result = rank_solar_return_locations(
        birth_date,
        year=2025,
        city_names=["London"],
        top_n=1
    )
    
    chart_summary = result["rankings"][0]["chart_summary"]
    
    assert "asc_sign" in chart_summary
    assert "mc_sign" in chart_summary
    assert "solar_return_datetime" in chart_summary
    
    # Validate signs are valid zodiac signs
    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    assert chart_summary["asc_sign"] in zodiac_signs
    assert chart_summary["mc_sign"] in zodiac_signs
    
    # SR datetime should be close to birthday
    sr_dt = datetime.fromisoformat(chart_summary["solar_return_datetime"].replace("+00:00", ""))
    assert sr_dt.month == birth_date.month
    assert abs(sr_dt.day - birth_date.day) <= 2
    
    print(f"✓ Chart summary valid")
    print(f"  ASC: {chart_summary['asc_sign']}")
    print(f"  MC: {chart_summary['mc_sign']}")
    print(f"  SR: {chart_summary['solar_return_datetime']}")
    print()


def test_invalid_city_handling():
    """Test that invalid city names are skipped gracefully."""
    print("=== Testing Invalid City Handling ===")
    
    birth_date = datetime(1990, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # Mix valid and invalid cities
    result = rank_solar_return_locations(
        birth_date,
        year=2025,
        city_names=["London", "InvalidCity", "Singapore"],
        top_n=3
    )
    
    # Should only process valid cities
    assert result["cities_analyzed"] == 2, f"Expected 2 valid cities, got {result['cities_analyzed']}"
    
    city_names = {r["city"] for r in result["rankings"]}
    assert city_names == {"London", "Singapore"}
    assert "InvalidCity" not in city_names
    
    print(f"✓ Invalid cities skipped gracefully")
    print(f"  Valid cities processed: {list(city_names)}")
    print()


if __name__ == "__main__":
    print("Starting Solar Return Ranking tests...\n")
    
    try:
        test_ranking_structure()
        test_ranking_order()
        test_all_cities_default()
        test_score_components()
        test_chart_summary()
        test_invalid_city_handling()
        
        print("=" * 60)
        print("✓ All Solar Return Ranking tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
