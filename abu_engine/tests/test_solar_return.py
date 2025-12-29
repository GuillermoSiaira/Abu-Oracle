"""
Test Solar Return endpoint calculation.
Verifies accurate Sun return time finding and chart generation.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from abu_engine.core.chart import find_solar_return, solar_return_chart, normalize_lon

def test_find_solar_return():
    """Test finding exact solar return datetime."""
    print("=== Testing Solar Return Time Calculation ===")
    
    # Test case: birth date July 5, 1990 at noon
    birth_date = datetime(1990, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
    lat, lon = 40.7128, -74.0060  # New York
    
    # Find solar return for 2025
    sr_datetime = find_solar_return(birth_date, lat, lon, year=2025)
    
    print(f"Birth date: {birth_date}")
    print(f"Solar Return 2025: {sr_datetime}")
    print(f"Difference from birthday: {sr_datetime.day - birth_date.day} days, {sr_datetime.hour - birth_date.hour} hours")
    
    # Verify it's close to the birthday
    assert sr_datetime.month == birth_date.month, "Solar return should be in same month"
    assert abs(sr_datetime.day - birth_date.day) <= 2, "Solar return should be within 2 days of birthday"
    
    print("✓ Solar return time found successfully\n")


def test_solar_return_accuracy():
    """Test that the found solar return actually has Sun at natal position."""
    print("=== Testing Solar Return Accuracy ===")
    
    from skyfield.api import load
    from abu_engine.core.chart import EphemerisSingleton
    
    birth_date = datetime(1985, 3, 15, 8, 30, 0, tzinfo=timezone.utc)
    lat, lon = 51.5074, -0.1278  # London
    
    # Get ephemeris
    planets = EphemerisSingleton()
    ts = load.timescale()
    earth = planets['earth']
    sun = planets['sun']
    
    # Get natal Sun longitude
    t_birth = ts.from_datetime(birth_date)
    natal_pos = earth.at(t_birth).observe(sun)
    _, natal_lon, _ = natal_pos.ecliptic_latlon()
    natal_lon_norm = normalize_lon(natal_lon.degrees)
    
    # Find solar return for 2024
    sr_datetime = find_solar_return(birth_date, lat, lon, year=2024)
    
    # Get Sun position at solar return time
    t_sr = ts.from_datetime(sr_datetime)
    sr_pos = earth.at(t_sr).observe(sun)
    _, sr_lon, _ = sr_pos.ecliptic_latlon()
    sr_lon_norm = normalize_lon(sr_lon.degrees)
    
    # Calculate difference
    diff = abs(sr_lon_norm - natal_lon_norm)
    if diff > 180:
        diff = 360 - diff
    
    print(f"Natal Sun longitude: {natal_lon_norm:.4f}°")
    print(f"Solar Return Sun longitude: {sr_lon_norm:.4f}°")
    print(f"Difference: {diff:.4f}°")
    
    assert diff < 0.01, f"Sun should return to natal position within 0.01°, got {diff}°"
    
    print("✓ Solar return Sun position matches natal position\n")


def test_solar_return_chart():
    """Test full solar return chart generation."""
    print("=== Testing Solar Return Chart Generation ===")
    
    birth_date = datetime(1995, 11, 22, 18, 0, 0, tzinfo=timezone.utc)
    lat, lon = -23.5505, -46.6333  # São Paulo
    year = 2025
    
    result = solar_return_chart(birth_date, lat, lon, year)
    
    print(f"Solar Return Chart for {year}:")
    print(f"  SR Datetime: {result['solar_return_datetime']}")
    print(f"  Birth Date: {result['birth_date']}")
    print(f"  Location: {result['location']}")
    print(f"  Planets: {len(result['planets'])} found")
    print(f"  Aspects: {len(result['aspects'])} found")
    print(f"  Score: {result['score_summary']['total_score']} ({result['score_summary']['interpretation']})")
    
    # Verify structure
    assert 'solar_return_datetime' in result
    assert 'planets' in result
    assert 'aspects' in result
    assert 'score_summary' in result
    assert len(result['planets']) >= 7  # At least 7 planets
    assert result['year'] == year
    
    # Verify Sun is present
    sun_found = any(p['name'] == 'Sun' for p in result['planets'])
    assert sun_found, "Sun should be in planets list"
    
    print("✓ Solar return chart generated successfully\n")


def test_multiple_years():
    """Test solar returns for multiple consecutive years."""
    print("=== Testing Multiple Years ===")
    
    birth_date = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    lat, lon = 0.0, 0.0  # Equator, prime meridian
    
    years = [2023, 2024, 2025]
    previous_sr = None
    
    for year in years:
        sr_datetime = find_solar_return(birth_date, lat, lon, year)
        print(f"{year}: {sr_datetime}")
        # For births near year boundaries (e.g., Jan 1 in UTC), the SR can fall on Dec 31 UTC
        assert abs(sr_datetime.year - year) <= 1, (
            f"Solar return should be around target year {year}, got {sr_datetime.year}"
        )
        if previous_sr:
            days_diff = (sr_datetime - previous_sr).days
            assert 364 <= days_diff <= 366, (
                f"Solar returns should be ~365 days apart, got {days_diff}"
            )
        previous_sr = sr_datetime
    
    print("✓ Multiple year solar returns calculated correctly\n")


if __name__ == "__main__":
    print("Starting Solar Return endpoint tests...\n")
    
    try:
        test_find_solar_return()
        test_solar_return_accuracy()
        test_solar_return_chart()
        test_multiple_years()
        
        print("=" * 60)
        print("✓ All Solar Return tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
