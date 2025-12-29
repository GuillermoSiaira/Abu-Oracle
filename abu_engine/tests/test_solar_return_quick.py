"""
Quick validation test for Solar Return endpoint.
Tests structure and basic functionality without heavy calculations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test that all required modules can be imported."""
    print("=== Testing Imports ===")
    
    from abu_engine.core.chart import find_solar_return, solar_return_chart
    from abu_engine.main import app
    print("✓ All imports successful\n")
    assert find_solar_return is not None
    assert solar_return_chart is not None
    assert app is not None


def test_endpoint_exists():
    """Test that the solar return endpoint is registered."""
    print("=== Testing Endpoint Registration ===")
    
    from abu_engine.main import app
    
    routes = [route.path for route in app.routes]
    
    assert "/api/astro/solar-return" in routes, "Solar Return endpoint not found in routes"
    print("✓ Solar Return endpoint registered")
    print(f"  All routes: {[r for r in routes if '/api/' in r]}\n")


def test_function_signature():
    """Test that solar_return_chart has correct signature."""
    print("=== Testing Function Signature ===")
    
    from abu_engine.core.chart import solar_return_chart
    import inspect
    
    sig = inspect.signature(solar_return_chart)
    params = list(sig.parameters.keys())
    
    expected = ['birth_date', 'lat', 'lon', 'year']
    
    print(f"Function parameters: {params}")
    
    assert all(p in params for p in expected), f"Missing expected parameters. Expected: {expected}"
    print("✓ Function signature correct\n")


if __name__ == "__main__":
    print("Starting quick Solar Return validation...\n")
    
    try:
        test_imports()
        test_endpoint_exists()
        test_function_signature()
        
        print("=" * 60)
        print("✓ All quick validations passed!")
        print("  Solar Return endpoint is ready to use.")
        print("=" * 60)
    except AssertionError as e:
        print("=" * 60)
        print(f"✗ Validation failed: {e}")
        print("=" * 60)
        sys.exit(1)
