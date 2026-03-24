"""
IGP (Predictive Geographic Intelligence) Optimizer — Sprint 1
Batch evaluation of cities for optimal Solar Return relocation.

Provides:
- compute_sr_instant: Calculate exact SR datetime from birth data
- score_location: Score a single lat/lon for SR quality
- batch_evaluate_cities: Parallel evaluation of multiple cities
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import hashlib

try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:
    SWE_AVAILABLE = False

from core.solar_return import find_solar_return_time
from core.chart import solar_return_chart
from core.solar_return_ranking import score_solar_return_location


def compute_sr_instant(
    birth_date: datetime,
    birth_lat: float,
    birth_lon: float,
    target_year: int
) -> datetime:
    """
    Compute the exact Solar Return datetime (UTC) for a given year.
    
    Args:
        birth_date: Natal birth datetime (UTC)
        birth_lat: Birth latitude (decimal degrees)
        birth_lon: Birth longitude (decimal degrees)
        target_year: Year for the Solar Return
    
    Returns:
        datetime: Exact SR moment in UTC
    
    Raises:
        ImportError: If pyswisseph not available
        ValueError: If target_year is before birth year
    """
    if not SWE_AVAILABLE:
        raise ImportError("pyswisseph is required for IGP calculations")
    
    if target_year < birth_date.year:
        raise ValueError(f"Target year {target_year} cannot be before birth year {birth_date.year}")
    
    # Get natal Sun longitude
    jd_birth = swe.julday(
        birth_date.year, birth_date.month, birth_date.day,
        birth_date.hour + birth_date.minute / 60.0 + birth_date.second / 3600.0
    )
    sun_pos, _ = swe.calc_ut(jd_birth, swe.SUN)
    natal_sun_longitude = sun_pos[0]
    
    # Find exact SR moment
    sr_datetime = find_solar_return_time(birth_date, natal_sun_longitude, target_year)
    # Ensure UTC-aware datetime
    if sr_datetime.tzinfo is None:
        sr_datetime = sr_datetime.replace(tzinfo=timezone.utc)
    else:
        # Normalize to UTC if it's not already
        try:
            sr_datetime = sr_datetime.astimezone(timezone.utc)
        except Exception:
            sr_datetime = sr_datetime.replace(tzinfo=timezone.utc)
    return sr_datetime


def score_location(
    sr_datetime: datetime,
    lat: float,
    lon: float,
    weights: Optional[Dict[str, float]] = None,
    intent: str = "general"
) -> float:
    """
    Score a single geographic location for SR quality.
    
    Args:
        sr_datetime: Exact SR moment (UTC)
        lat: Latitude of location (decimal degrees)
        lon: Longitude of location (decimal degrees)
        weights: Optional weight overrides (future: from weights.json)
        intent: Scoring intent (general|health|career|relationships|creative)
    
    Returns:
        float: Normalized score (0.0–1.0)
    
    Notes:
        - Reuses existing score_solar_return_location from solar_return_ranking.py
        - Intent-based weighting deferred to Sprint 2
        - Weights.json integration deferred to Sprint 2
    """
    # For Sprint 1: use existing scoring function with dummy city name
    # TODO Sprint 2: refactor score_solar_return_location to accept weights + intent
    result = score_solar_return_location(
        birth_date=sr_datetime,  # Pass SR datetime as birth (hack for MVP)
        city_name=f"Location_{lat:.2f}_{lon:.2f}",
        city_lat=lat,
        city_lon=lon,
        year=None  # Already at SR moment
    )
    
    # Normalize total_score to 0–1 range (assuming max ~100 from ranking logic)
    normalized_score = min(result['total_score'] / 100.0, 1.0)
    
    return normalized_score


def _evaluate_city_worker(args: Tuple) -> Dict[str, Any]:
    """
    Worker function for parallel city evaluation.
    
    Args:
        args: Tuple of (sr_datetime, city_data, weights, intent, cache)
    
    Returns:
        Dict with city, lat, lon, score, rank (placeholder), cache_hit flag
    """
    sr_datetime, city_data, weights, intent, cache = args
    
    city_name = city_data['name']
    lat = city_data['lat']
    lon = city_data['lon']
    country = city_data.get('country', 'Unknown')
    
    # Generate cache key using SR datetime + location
    cache_key = f"{sr_datetime.isoformat()}_{lat:.4f}_{lon:.4f}"
    
    # Check cache first
    cached_score = None
    if cache is not None:
        cached_score = cache.get(cache_key)
    
    if cached_score is not None:
        score = cached_score
        cache_hit = True
    else:
        # Score the location
        score = score_location(sr_datetime, lat, lon, weights, intent)
        cache_hit = False
        
        # Store in cache for future use
        if cache is not None:
            cache.set(cache_key, score)
    
    return {
        'city': city_name,
        'country': country,
        'lat': lat,
        'lon': lon,
        'score': score,
        'rank': 0,  # Will be assigned after sorting
        'cache_hit': cache_hit
    }


def batch_evaluate_cities(
    sr_datetime: datetime,
    cities: List[Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
    intent: str = "general",
    cache: Optional[Any] = None,
    max_workers: int = 8
) -> List[Dict[str, Any]]:
    """
    Evaluate multiple cities in parallel for SR quality.
    
    Args:
        sr_datetime: Exact SR moment (UTC)
        cities: List of city dicts with keys: name, lat, lon, country (optional)
        weights: Optional weight overrides
        intent: Scoring intent
        cache: Optional cache instance (igp_cache.IGPCache)
        max_workers: Number of parallel workers (default: 8)
    
    Returns:
        List of scored city dicts, sorted by score (descending)
    
    Notes:
        - Uses ProcessPoolExecutor for CPU-bound scoring
        - Cache is checked before scoring; results stored after computation
        - Returns all evaluated cities; caller filters top-N
    """
    # Prepare worker arguments.
    # IMPORTANT: Do not pass the cache instance into subprocesses — many cache
    # implementations include thread locks that are not picklable. For now,
    # disable cross-process cache usage by passing None. Per-process caching or
    # an external/shared cache can be introduced later.
    worker_args = [
        (sr_datetime, city, weights, intent, None)
        for city in cities
    ]
    
    results = []
    cache_hits = 0
    
    # Parallel evaluation
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_evaluate_city_worker, args): args for args in worker_args}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                if result.get('cache_hit'):
                    cache_hits += 1
                results.append(result)
            except Exception as exc:
                # Log error but continue with remaining cities
                city_data = futures[future][1]
                print(f"[IGP] Error evaluating {city_data['name']}: {exc}")
    
    # Log cache performance (disabled for cross-process usage)
    if cache is not None and len(results) > 0 and cache_hits > 0:
        hit_rate = (cache_hits / len(results)) * 100
        print(f"[IGP] Cache: {cache_hits}/{len(results)} hits ({hit_rate:.1f}%)")
    
    # Sort by score (descending) with deterministic tiebreaker by city name
    results.sort(key=lambda x: (-x['score'], x['city']))
    
    # Assign ranks
    for idx, result in enumerate(results, start=1):
        result['rank'] = idx
    
    return results


def generate_cache_key(birth_date: datetime, target_year: int, city_id: str) -> str:
    """
    Generate deterministic cache key for IGP evaluations.
    
    Args:
        birth_date: Natal birth datetime
        target_year: SR year
        city_id: Unique city identifier (e.g., "Barcelona_ES" or lat_lon hash)
    
    Returns:
        str: SHA256 hash of key components
    """
    key_string = f"{birth_date.isoformat()}_{target_year}_{city_id}"
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


def load_cities_dataset(dataset_path: str = "cities.json") -> List[Dict[str, Any]]:
    """
    Load cities dataset from JSON file.
    
    Args:
        dataset_path: Path to cities.json (relative to abu_engine root)
    
    Returns:
        List of city dicts with keys: name, country, lat, lon, population (optional)
    
    Raises:
        FileNotFoundError: If dataset file missing
        json.JSONDecodeError: If dataset malformed
    
    Notes:
        - Expected format: [{"name": "Barcelona", "country": "Spain", "lat": 41.3874, "lon": 2.1686}, ...]
        - For Sprint 1: accepts existing RELOCATION_CITIES or external JSON
    """
    import os
    
    # Try absolute path first, then relative to module
    if not os.path.isabs(dataset_path):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        dataset_path = os.path.join(module_dir, "..", dataset_path)
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        cities = json.load(f)
    
    # Validate structure
    required_keys = {'name', 'lat', 'lon'}
    for city in cities:
        if not required_keys.issubset(city.keys()):
            raise ValueError(f"City missing required keys {required_keys}: {city}")
    
    return cities


# Sprint 1 deliverables checklist:
# ✅ compute_sr_instant: Calculates exact SR datetime
# ✅ score_location: Scores single lat/lon
# ✅ batch_evaluate_cities: Parallel city evaluation with ProcessPoolExecutor
# ✅ generate_cache_key: Deterministic cache key generation
# ✅ load_cities_dataset: JSON dataset loader with validation
# 🔄 Cache integration: Deferred to igp_cache.py module
# 🔄 Intent-based weighting: Deferred to Sprint 2
# 🔄 Weights.json integration: Deferred to Sprint 2
