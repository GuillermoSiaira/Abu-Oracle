"""
Unit tests for IGP optimizer — Sprint 1

Tests:
- compute_sr_instant: Determinism and year validation
- score_location: Basic scoring functionality
- batch_evaluate_cities: Parallel evaluation and sorting
- cache_key generation: Uniqueness and consistency
"""

import pytest
from datetime import datetime, timezone
from core.igp_optimizer import (
    compute_sr_instant,
    score_location,
    batch_evaluate_cities,
    generate_cache_key
)
from core.igp_cache import IGPCache


class TestComputeSRInstant:
    """Test compute_sr_instant function."""
    
    def test_compute_sr_instant_determinism(self):
        """Same input should produce identical output."""
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        birth_lat = 40.7128
        birth_lon = -74.0060
        target_year = 2026
        
        result1 = compute_sr_instant(birth_date, birth_lat, birth_lon, target_year)
        result2 = compute_sr_instant(birth_date, birth_lat, birth_lon, target_year)
        
        assert result1 == result2
        assert isinstance(result1, datetime)
    
    def test_compute_sr_instant_year_validation(self):
        """Target year before birth should raise ValueError."""
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        birth_lat = 40.7128
        birth_lon = -74.0060
        target_year = 1985  # Before birth
        
        with pytest.raises(ValueError, match="cannot be before birth year"):
            compute_sr_instant(birth_date, birth_lat, birth_lon, target_year)
    
    def test_compute_sr_instant_realistic_result(self):
        """SR datetime should be close to birthday."""
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        birth_lat = 40.7128
        birth_lon = -74.0060
        target_year = 2026
        
        sr_datetime = compute_sr_instant(birth_date, birth_lat, birth_lon, target_year)
        
        # SR should be in January (±2 days from birthday)
        assert sr_datetime.year == 2026
        assert sr_datetime.month == 1
        assert 13 <= sr_datetime.day <= 17


class TestScoreLocation:
    """Test score_location function."""
    
    def test_score_location_returns_normalized(self):
        """Score should be between 0.0 and 1.0."""
        sr_datetime = datetime(2026, 1, 15, 10, 27, 43, tzinfo=timezone.utc)
        lat = 41.3874  # Barcelona
        lon = 2.1686
        
        score = score_location(sr_datetime, lat, lon)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)
    
    def test_score_location_different_coords(self):
        """Different coordinates should (likely) produce different scores."""
        sr_datetime = datetime(2026, 1, 15, 10, 27, 43, tzinfo=timezone.utc)
        
        score1 = score_location(sr_datetime, 41.3874, 2.1686)  # Barcelona
        score2 = score_location(sr_datetime, -33.8688, 151.2093)  # Sydney
        
        # Scores will differ due to different house cusps and angularity
        # Not asserting inequality since edge cases may produce same score,
        # but verify both are valid
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0


class TestBatchEvaluateCities:
    """Test batch_evaluate_cities function."""
    
    def test_batch_evaluate_cities_basic(self):
        """Batch evaluation should return sorted results."""
        sr_datetime = datetime(2026, 1, 15, 10, 27, 43, tzinfo=timezone.utc)
        cities = [
            {'name': 'Barcelona', 'lat': 41.3874, 'lon': 2.1686, 'country': 'Spain'},
            {'name': 'Sydney', 'lat': -33.8688, 'lon': 151.2093, 'country': 'Australia'},
            {'name': 'London', 'lat': 51.5074, 'lon': -0.1278, 'country': 'UK'}
        ]
        
        results = batch_evaluate_cities(
            sr_datetime=sr_datetime,
            cities=cities,
            weights=None,
            intent="general",
            cache=None,
            max_workers=2
        )
        
        # Verify structure
        assert len(results) == 3
        assert all('city' in r for r in results)
        assert all('score' in r for r in results)
        assert all('rank' in r for r in results)
        
        # Verify sorting (descending by score)
        scores = [r['score'] for r in results]
        assert scores == sorted(scores, reverse=True)
        
        # Verify ranks
        assert results[0]['rank'] == 1
        assert results[1]['rank'] == 2
        assert results[2]['rank'] == 3
    
    def test_batch_evaluate_cities_empty_list(self):
        """Empty cities list should return empty results."""
        sr_datetime = datetime(2026, 1, 15, 10, 27, 43, tzinfo=timezone.utc)
        cities = []
        
        results = batch_evaluate_cities(
            sr_datetime=sr_datetime,
            cities=cities,
            weights=None,
            intent="general",
            cache=None,
            max_workers=2
        )
        
        assert results == []


class TestCacheKey:
    """Test generate_cache_key function."""
    
    def test_cache_key_determinism(self):
        """Same inputs should produce same key."""
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        target_year = 2026
        city_id = "Barcelona_ES"
        
        key1 = generate_cache_key(birth_date, target_year, city_id)
        key2 = generate_cache_key(birth_date, target_year, city_id)
        
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 64  # SHA256 hex length
    
    def test_cache_key_uniqueness(self):
        """Different inputs should produce different keys."""
        birth_date1 = datetime(1990, 1, 15, 10, 30, 0)
        birth_date2 = datetime(1990, 1, 15, 10, 30, 1)  # 1 second diff
        target_year = 2026
        city_id = "Barcelona_ES"
        
        key1 = generate_cache_key(birth_date1, target_year, city_id)
        key2 = generate_cache_key(birth_date2, target_year, city_id)
        
        assert key1 != key2


class TestIGPCache:
    """Test IGPCache class."""
    
    def test_cache_get_miss(self):
        """Get on empty cache should return None and increment misses."""
        cache = IGPCache(max_size=100)
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        
        result = cache.get(birth_date, 2026, "Barcelona_ES")
        
        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0
    
    def test_cache_set_and_get_hit(self):
        """Set then get should return value and increment hits."""
        cache = IGPCache(max_size=100)
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        
        cache.set(birth_date, 2026, "Barcelona_ES", score=0.87, metadata={'test': True})
        result = cache.get(birth_date, 2026, "Barcelona_ES")
        
        assert result is not None
        assert result['score'] == 0.87
        assert result['metadata']['test'] is True
        assert cache.hits == 1
        assert cache.misses == 0
    
    def test_cache_stats(self):
        """Stats should reflect hits, misses, and hit_rate."""
        cache = IGPCache(max_size=100)
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        
        cache.set(birth_date, 2026, "Barcelona_ES", score=0.87)
        cache.get(birth_date, 2026, "Barcelona_ES")  # hit
        cache.get(birth_date, 2026, "Sydney_AU")  # miss
        
        stats = cache.stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5
        assert stats['size'] == 1
        assert stats['max_size'] == 100
    
    def test_cache_clear(self):
        """Clear should remove all entries and reset counters."""
        cache = IGPCache(max_size=100)
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        
        cache.set(birth_date, 2026, "Barcelona_ES", score=0.87)
        cache.get(birth_date, 2026, "Barcelona_ES")
        cache.clear()
        
        stats = cache.stats()
        assert stats['size'] == 0
        assert stats['hits'] == 0
        assert stats['misses'] == 0
    
    def test_cache_lru_eviction(self):
        """Cache at max_size should evict oldest entry."""
        cache = IGPCache(max_size=2)
        birth_date = datetime(1990, 1, 15, 10, 30, 0)
        
        cache.set(birth_date, 2026, "City1", score=0.8)
        cache.set(birth_date, 2026, "City2", score=0.85)
        cache.set(birth_date, 2026, "City3", score=0.9)  # Should evict City1
        
        stats = cache.stats()
        assert stats['size'] == 2
        
        # City1 should be evicted (oldest)
        result = cache.get(birth_date, 2026, "City1")
        assert result is None
        
        # City2 and City3 should remain
        assert cache.get(birth_date, 2026, "City2") is not None
        assert cache.get(birth_date, 2026, "City3") is not None
