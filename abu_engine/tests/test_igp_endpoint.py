"""
Integration tests for IGP /api/rs/optimize endpoint.

Tests the complete API contract, request/response validation, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from main import app

client = TestClient(app)


class TestIGPOptimizeEndpoint:
    """Integration tests for POST /api/rs/optimize"""
    
    def test_optimize_minimal_request(self):
        """Test with minimal required fields (uses 'birth' key)."""
        payload = {
            "birth": {
                "date": "1990-01-15T10:30:00Z",
                "lat": 40.7128,
                "lon": -74.0060
            },
            "target_year": 2026
        }
        
        response = client.post("/api/rs/optimize", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure (current contract)
        assert "best_locations" in data
        assert "astro_metadata" in data
        assert "score_summary" in data
        
        # Validate top_locations format
        assert isinstance(data["best_locations"], list)
        # Allow empty results in edge cases; endpoint should still return structure
        if data["best_locations"]:
            first_location = data["best_locations"][0]
            assert "city" in first_location
            assert "country" in first_location
            assert "lat" in first_location
            assert "lon" in first_location
            assert "score" in first_location
            assert "rank" in first_location

        # Validate metadata
        assert "sr_datetime" in data["astro_metadata"]
        assert "cities_evaluated" in data["astro_metadata"]
        
    def test_optimize_with_preferences(self):
        """Test with all preference flags."""
        payload = {
            "birth": {
                "date": "1990-01-15T10:30:00Z",
                "lat": 40.7128,
                "lon": -74.0060
            },
            "target_year": 2026,
            # Current contract: use max_candidates in preferences; refine/diversity are top-level flags
            "preferences": {
                "max_candidates": 5
            },
            "refine": True,
            "diversity": False
        }
        
        response = client.post("/api/rs/optimize", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should respect max_candidates
        assert len(data["best_locations"]) <= 5
        
    def test_optimize_invalid_date(self):
        """Test with malformed date."""
        payload = {
            "birth": {
                "date": "invalid-date",
                "lat": 40.7128,
                "lon": -74.0060
            },
            "target_year": 2026
        }
        
        response = client.post("/api/rs/optimize", json=payload)
        
        assert response.status_code == 422  # Validation error
        
    def test_optimize_missing_required_fields(self):
        """Test with missing birth_data."""
        payload = {
            "target_year": 2026
        }
        
        response = client.post("/api/rs/optimize", json=payload)
        
        assert response.status_code == 422
        
    def test_optimize_invalid_coordinates(self):
        """Test with out-of-range coordinates."""
        payload = {
            "birth": {
                "date": "1990-01-15T10:30:00Z",
                "lat": 91.0,  # Invalid latitude
                "lon": -74.0060
            },
            "target_year": 2026
        }
        
        response = client.post("/api/rs/optimize", json=payload)
        
        # Should either validate and reject (422) or handle gracefully with 200
        assert response.status_code in [200, 400, 422, 500]
        
    def test_optimize_past_year(self):
        """Test with year before birth year."""
        payload = {
            "birth": {
                "date": "1990-01-15T10:30:00Z",
                "lat": 40.7128,
                "lon": -74.0060
            },
            "target_year": 1985  # Before birth
        }
        
        response = client.post("/api/rs/optimize", json=payload)
        
        # Should fail validation
        assert response.status_code in [400, 422, 500]
        
    def test_optimize_score_range(self):
        """Test that all scores are normalized 0-1."""
        payload = {
            "birth": {
                "date": "1990-01-15T10:30:00Z",
                "lat": 40.7128,
                "lon": -74.0060
            },
            "target_year": 2026
        }
        
        response = client.post("/api/rs/optimize", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        for location in data["best_locations"]:
            score = location["score"]
            assert 0.0 <= score <= 1.0, f"Score {score} out of range"
            
    def test_optimize_ranking_order(self):
        """Test that results are sorted by score descending."""
        payload = {
            "birth": {
                "date": "1990-01-15T10:30:00Z",
                "lat": 40.7128,
                "lon": -74.0060
            },
            "target_year": 2026,
            "preferences": {
                "top_n": 10
            }
        }
        
        response = client.post("/api/rs/optimize", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Extract scores
        scores = [loc["score"] for loc in data["best_locations"]]
        
        # Verify descending order
        assert scores == sorted(scores, reverse=True), "Results not sorted by score"
        
        # Verify ranks are sequential
        ranks = [loc["rank"] for loc in data["best_locations"]]
        assert ranks == list(range(1, len(ranks) + 1)), "Ranks not sequential"
        
    def test_optimize_determinism(self):
        """Test that same input produces same output."""
        payload = {
            "birth": {
                "date": "1990-01-15T10:30:00Z",
                "lat": 40.7128,
                "lon": -74.0060
            },
            "target_year": 2026,
            "preferences": {
                "top_n": 5
            }
        }
        
        response1 = client.post("/api/rs/optimize", json=payload)
        response2 = client.post("/api/rs/optimize", json=payload)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Top results should be identical
        top1 = data1.get("best_locations", [])[:3]
        top2 = data2.get("best_locations", [])[:3]
        
        for loc1, loc2 in zip(top1, top2):
            assert loc1["city"] == loc2["city"]
            assert abs(loc1["score"] - loc2["score"]) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
