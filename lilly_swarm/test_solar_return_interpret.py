"""
Quick test for Solar Return interpretation endpoint.
"""

import sys
from pathlib import Path

# Add project root to path
parent = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent))

def test_imports():
    """Test that all imports work."""
    try:
        from lilly_engine.core.solar_return import (
            interpret_solar_return,
            Element,
            Mode,
            SIGN_ATTRIBUTES,
            RELOCATION_CITIES,
            find_favorable_locations,
            get_sign_element
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_sign_attributes():
    """Test sign attribute lookup."""
    try:
        from lilly_engine.core.solar_return import get_sign_element, Element
        
        assert get_sign_element("Aries") == Element.FIRE
        assert get_sign_element("Cancer") == Element.WATER
        assert get_sign_element("Libra") == Element.AIR
        assert get_sign_element("Capricorn") == Element.EARTH
        
        print("✓ Sign attributes working correctly")
        return True
    except Exception as e:
        print(f"✗ Sign attributes test failed: {e}")
        return False


def test_relocation_cities():
    """Test city database."""
    try:
        from lilly_engine.core.solar_return import RELOCATION_CITIES, Element
        
        assert len(RELOCATION_CITIES) > 0
        assert "Lisbon" in RELOCATION_CITIES
        assert RELOCATION_CITIES["Lisbon"]["element"] == Element.WATER
        
        print(f"✓ City database loaded ({len(RELOCATION_CITIES)} cities)")
        return True
    except Exception as e:
        print(f"✗ City database test failed: {e}")
        return False


def test_favorable_locations():
    """Test location finder."""
    try:
        from lilly_engine.core.solar_return import find_favorable_locations, Element
        
        locations = find_favorable_locations(
            natal_asc_sign="Cancer",
            current_element=Element.WATER,
            max_results=3
        )
        
        assert len(locations) > 0
        assert len(locations) <= 3
        assert all("city" in loc for loc in locations)
        assert all("element" in loc for loc in locations)
        
        print(f"✓ Location finder working ({len(locations)} recommendations)")
        return True
    except Exception as e:
        print(f"✗ Location finder test failed: {e}")
        return False


def test_interpret_function():
    """Test the main interpret_solar_return function."""
    try:
        from lilly_engine.core.solar_return import interpret_solar_return
        
        # Sample natal chart
        natal_chart = {
            "planets": [
                {"name": "Sun", "sign": "Cancer", "longitude": 120.5}
            ]
        }
        
        # Sample solar return chart
        solar_chart = {
            "planets": [
                {"name": "Sun", "sign": "Cancer", "longitude": 120.1}
            ]
        }
        
        result = interpret_solar_return(natal_chart, solar_chart, language="es")
        
        assert "best_locations" in result
        assert "reasoning" in result
        assert "astro_metadata" in result
        assert "natal_ascendant" in result
        assert "solar_ascendant" in result
        assert result["astro_metadata"]["source"] == "heuristic"
        assert result["astro_metadata"]["language"] == "es"
        
        print("✓ interpret_solar_return function working")
        print(f"  Best locations: {result['best_locations'][:3]}")
        return True
    except Exception as e:
        print(f"✗ interpret_solar_return test failed: {e}")
        return False


def test_endpoint_registration():
    """Test that the endpoint is registered in FastAPI."""
    try:
        from lilly_engine.main import app
        
        routes = [route.path for route in app.routes]
        assert "/api/ai/solar-return" in routes
        
        print("✓ Solar Return endpoint registered")
        return True
    except Exception as e:
        print(f"✗ Endpoint registration test failed: {e}")
        return False


def test_multilingual():
    """Test multilingual support."""
    try:
        from lilly_engine.core.solar_return import interpret_solar_return
        
        natal_chart = {
            "planets": [{"name": "Sun", "sign": "Leo", "longitude": 150.0}]
        }
        solar_chart = {
            "planets": [{"name": "Sun", "sign": "Leo", "longitude": 150.0}]
        }
        
        languages = ["es", "en", "pt", "fr"]
        for lang in languages:
            result = interpret_solar_return(natal_chart, solar_chart, language=lang)
            assert result["astro_metadata"]["language"] == lang
            assert len(result["reasoning"]) > 0
        
        print(f"✓ Multilingual support working ({len(languages)} languages)")
        return True
    except Exception as e:
        print(f"✗ Multilingual test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n=== Solar Return Interpretation Tests ===\n")
    
    tests = [
        test_imports,
        test_sign_attributes,
        test_relocation_cities,
        test_favorable_locations,
        test_interpret_function,
        test_endpoint_registration,
        test_multilingual,
    ]
    
    results = [test() for test in tests]
    
    print(f"\n=== Results: {sum(results)}/{len(results)} tests passed ===\n")
    
    if all(results):
        print("✓ All tests passed! Solar Return interpretation ready.\n")
    else:
        print("✗ Some tests failed. Check output above.\n")
        sys.exit(1)
