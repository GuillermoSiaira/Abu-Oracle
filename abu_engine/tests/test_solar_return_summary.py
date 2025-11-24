"""
test_solar_return_summary.py
Unit tests for Solar Return summary generation module.
Validates summarize_solar_return() output format and is_near_birthday() logic.
"""

import pytest
from datetime import datetime, timezone
from core.solar_return_summary import (
    summarize_solar_return,
    is_near_birthday,
    get_chart_ruler,
    format_degree_position,
    compute_house_emphasis,
    select_main_aspect,
)


class TestSolarReturnSummary:
    """Test suite for Solar Return summary generation."""

    def test_summarize_solar_return_output_keys(self):
        """Verify summarize_solar_return returns dict with all required keys."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        assert isinstance(result, dict), "Result must be a dictionary"
        assert "location" in result, "Missing 'location' key"
        assert "datetime" in result, "Missing 'datetime' key"
        assert "ascendant" in result, "Missing 'ascendant' key"
        assert "ruler" in result, "Missing 'ruler' key"
        assert "house_emphasis" in result, "Missing 'house_emphasis' key"
        assert "main_aspect" in result, "Missing 'main_aspect' key"
        assert "score_summary" in result, "Missing 'score_summary' key"
        assert "summary" in result, "Missing 'summary' key"

    def test_summarize_solar_return_location_format(self):
        """Verify location field is properly formatted string."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        assert isinstance(result["location"], str), "Location must be a string"
        assert "40.71" in result["location"], "Location should contain latitude"
        assert "-74.01" in result["location"], "Location should contain longitude"

    def test_summarize_solar_return_datetime_format(self):
        """Verify datetime field is ISO 8601 formatted string."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        assert isinstance(result["datetime"], str), "Datetime must be a string"
        # Parse to validate ISO format
        parsed = datetime.fromisoformat(result["datetime"].replace("Z", "+00:00"))
        assert parsed.year == 2024, "Solar Return year should match requested year"

    def test_summarize_solar_return_ascendant_structure(self):
        """Verify ascendant field contains sign and position."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        assert isinstance(result["ascendant"], dict), "Ascendant must be a dictionary"
        assert "sign" in result["ascendant"], "Ascendant missing 'sign' key"
        assert "position" in result["ascendant"], "Ascendant missing 'position' key"

    def test_summarize_solar_return_ruler_format(self):
        """Verify ruler field is a string (planet name)."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        assert isinstance(result["ruler"], str), "Ruler must be a string"
        assert len(result["ruler"]) > 0, "Ruler should not be empty"

    def test_summarize_solar_return_house_emphasis(self):
        """Verify house_emphasis is a list of 1-2 integers."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        assert isinstance(result["house_emphasis"], list), "House emphasis must be a list"
        assert len(result["house_emphasis"]) <= 2, "House emphasis should have at most 2 houses"
        for house in result["house_emphasis"]:
            assert isinstance(house, int), "House numbers must be integers"
            assert 1 <= house <= 12, "House numbers must be between 1 and 12"

    def test_summarize_solar_return_main_aspect(self):
        """Verify main_aspect is either None or dict with required keys."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        if result["main_aspect"] is not None:
            assert isinstance(result["main_aspect"], dict), "Main aspect must be a dict when present"
            assert "type" in result["main_aspect"], "Main aspect missing 'type' key"
            assert "p1" in result["main_aspect"], "Main aspect missing 'p1' key"
            assert "p2" in result["main_aspect"], "Main aspect missing 'p2' key"

    def test_summarize_solar_return_score_summary(self):
        """Verify score_summary field has expected structure."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        assert isinstance(result["score_summary"], dict), "Score summary must be a dictionary"
        # Check for at least one score field present
        assert len(result["score_summary"]) > 0, "Score summary should not be empty"

    def test_summarize_solar_return_summary_text(self):
        """Verify summary field is a non-empty string."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = summarize_solar_return(birth_dt, 40.7128, -74.0060, year=2024, lang="es")

        assert isinstance(result["summary"], str), "Summary must be a string"
        assert len(result["summary"]) > 0, "Summary should not be empty"


class TestIsNearBirthday:
    """Test suite for birthday proximity detection."""

    def test_is_near_birthday_same_day(self):
        """Birthday should be detected on the exact same day."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        current_dt = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert is_near_birthday(birth_dt, current_dt, window_days=30) is True

    def test_is_near_birthday_within_window(self):
        """Birthday should be detected within 30-day window."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        # 20 days before
        current_dt = datetime(2024, 2, 24, 12, 0, 0, tzinfo=timezone.utc)
        assert is_near_birthday(birth_dt, current_dt, window_days=30) is True

        # 20 days after
        current_dt = datetime(2024, 4, 4, 12, 0, 0, tzinfo=timezone.utc)
        assert is_near_birthday(birth_dt, current_dt, window_days=30) is True

    def test_is_near_birthday_outside_window(self):
        """Birthday should not be detected outside 30-day window."""
        birth_dt = datetime(1990, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        # 40 days before
        current_dt = datetime(2024, 2, 4, 12, 0, 0, tzinfo=timezone.utc)
        assert is_near_birthday(birth_dt, current_dt, window_days=30) is False

        # 40 days after
        current_dt = datetime(2024, 4, 24, 12, 0, 0, tzinfo=timezone.utc)
        assert is_near_birthday(birth_dt, current_dt, window_days=30) is False

    def test_is_near_birthday_year_wrap_before(self):
        """Test year wrap: current date in December, birthday in January."""
        birth_dt = datetime(1990, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        current_dt = datetime(2024, 12, 25, 12, 0, 0, tzinfo=timezone.utc)
        # 21 days before Jan 15 (Dec 25 → Jan 15)
        assert is_near_birthday(birth_dt, current_dt, window_days=30) is True

    def test_is_near_birthday_year_wrap_after(self):
        """Test year wrap: current date in January, birthday in December."""
        birth_dt = datetime(1990, 12, 25, 12, 0, 0, tzinfo=timezone.utc)
        current_dt = datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        # 16 days after Dec 25 (Dec 25 → Jan 10)
        assert is_near_birthday(birth_dt, current_dt, window_days=30) is True

    def test_is_near_birthday_year_wrap_outside_window(self):
        """Test year wrap outside window."""
        birth_dt = datetime(1990, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        current_dt = datetime(2024, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
        # 75 days before Jan 15 (Nov 1 → Jan 15)
        assert is_near_birthday(birth_dt, current_dt, window_days=30) is False


class TestHelperFunctions:
    """Test suite for individual helper functions."""

    def test_get_chart_ruler(self):
        """Verify get_chart_ruler returns correct traditional ruler."""
        assert get_chart_ruler("Aries") == "Mars"
        assert get_chart_ruler("Taurus") == "Venus"
        assert get_chart_ruler("Gemini") == "Mercury"
        assert get_chart_ruler("Cancer") == "Moon"
        assert get_chart_ruler("Leo") == "Sun"
        assert get_chart_ruler("Virgo") == "Mercury"
        assert get_chart_ruler("Libra") == "Venus"
        assert get_chart_ruler("Scorpio") == "Mars"
        assert get_chart_ruler("Sagittarius") == "Jupiter"
        assert get_chart_ruler("Capricorn") == "Saturn"
        assert get_chart_ruler("Aquarius") == "Saturn"
        assert get_chart_ruler("Pisces") == "Jupiter"
        assert get_chart_ruler("Unknown") == "Unknown"

    def test_format_degree_position(self):
        """Verify format_degree_position returns correct sign and degree."""
        # Aries 0°
        result = format_degree_position(0.0)
        assert "Aries" in result and "0°" in result

        # Taurus 15°
        result = format_degree_position(45.0)
        assert "Taurus" in result and "15°" in result

        # Pisces 29°
        result = format_degree_position(359.0)
        assert "Pisces" in result and "29°" in result

    def test_compute_house_emphasis_empty(self):
        """Verify compute_house_emphasis handles empty planet list."""
        result = compute_house_emphasis([])
        assert result == [], "Empty planet list should return empty emphasis"

    def test_compute_house_emphasis_single_house(self):
        """Verify compute_house_emphasis with all planets in one house."""
        planets = [
            {"name": "Sun", "house": 1},
            {"name": "Moon", "house": 1},
            {"name": "Mercury", "house": 1},
        ]
        result = compute_house_emphasis(planets)
        assert result == [1], "Should return only house 1"

    def test_compute_house_emphasis_two_houses(self):
        """Verify compute_house_emphasis with planets in multiple houses."""
        planets = [
            {"name": "Sun", "house": 1},
            {"name": "Moon", "house": 1},
            {"name": "Mercury", "house": 7},
            {"name": "Venus", "house": 7},
        ]
        result = compute_house_emphasis(planets)
        assert len(result) == 2, "Should return two houses"
        assert 1 in result and 7 in result, "Should return houses 1 and 7"

    def test_select_main_aspect_none(self):
        """Verify select_main_aspect returns None when no aspects."""
        result = select_main_aspect([], {})
        assert result is None, "Empty aspect list should return None"

    def test_select_main_aspect_prioritizes_sun_benefic(self):
        """Verify select_main_aspect prioritizes Sun with Jupiter/Venus."""
        aspects = [
            {"type": "trine", "p1": "Sun", "p2": "Jupiter", "orb": 2.0},
            {"type": "square", "p1": "Mars", "p2": "Saturn", "orb": 1.0},
        ]
        planets = {"Sun": {}, "Jupiter": {}, "Mars": {}, "Saturn": {}}
        result = select_main_aspect(aspects, planets)
        assert result is not None, "Should find Sun-Jupiter trine"
        assert result["p1"] == "Sun" and result["p2"] == "Jupiter", "Should select Sun-Jupiter"

    def test_select_main_aspect_falls_back(self):
        """Verify select_main_aspect falls back to first aspect when no priority match."""
        aspects = [
            {"type": "square", "p1": "Mars", "p2": "Saturn", "orb": 1.0},
        ]
        planets = {"Mars": {}, "Saturn": {}}
        result = select_main_aspect(aspects, planets)
        assert result is not None, "Should return first aspect as fallback"
        assert result["type"] == "square", "Should return Mars-Saturn square"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
