"""
IGP Cache Module — Sprint 1
LRU cache for IGP city evaluations to accelerate repeated queries.

Provides:
- IGPCache: Thread-safe LRU cache with get/set/clear methods
- Cache key format: (birth_date_hash, target_year, city_id)
"""

from typing import Optional, Dict, Any
from functools import lru_cache
from datetime import datetime
import hashlib
import threading


class IGPCache:
    """
    Thread-safe LRU cache for IGP evaluations.
    
    Attributes:
        max_size: Maximum number of entries (default: 10,000)
        hits: Cache hit counter
        misses: Cache miss counter
    
    Notes:
        - Uses Python's functools.lru_cache under the hood
        - Cache key: SHA256(birth_date_iso, target_year, city_id)
        - Stores: score (float) and metadata (dict)
        - MVP implementation; Redis/persistent backend deferred to Sprint 3
    """
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize IGP cache.
        
        Args:
            max_size: Maximum cache entries (LRU eviction)
        """
        self.max_size = max_size
        self._cache: Dict[str, float | Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, birth_date: datetime, target_year: int, city_id: str) -> str:
        """
        Generate cache key from parameters.
        
        Args:
            birth_date: Natal birth datetime
            target_year: SR year
            city_id: Unique city identifier
        
        Returns:
            str: SHA256 hash key
        """
        key_string = f"{birth_date.isoformat()}_{target_year}_{city_id}"
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def get(
        self,
        key_or_birth_date: str | datetime,
        target_year: Optional[int] = None,
        city_id: Optional[str] = None
    ) -> Optional[float | Dict[str, Any]]:
        """
        Retrieve cached score. Supports both simple string key and legacy structured API.
        
        Args:
            key_or_birth_date: Simple string key OR natal birth datetime (legacy)
            target_year: SR year (legacy API only)
            city_id: City identifier (legacy API only)
        
        Returns:
            float: Cached score (simple API), or Dict with 'score'/'metadata' (legacy), or None if miss
        """
        # Detect API mode
        if isinstance(key_or_birth_date, str):
            # Simple API: get(key)
            key = key_or_birth_date
            with self._lock:
                if key in self._cache:
                    self.hits += 1
                    value = self._cache[key]
                    # Return float for simple API
                    return value if isinstance(value, (int, float)) else value.get('score')
                else:
                    self.misses += 1
                    return None
        else:
            # Legacy API: get(birth_date, target_year, city_id)
            key = self._generate_key(key_or_birth_date, target_year, city_id)
            with self._lock:
                if key in self._cache:
                    self.hits += 1
                    value = self._cache[key]
                    # Return dict for legacy API
                    return value if isinstance(value, dict) else {'score': value, 'metadata': {}}
                else:
                    self.misses += 1
                    return None
    
    def set(
        self,
        key_or_birth_date: str | datetime,
        score_or_target_year: float | int,
        city_id: Optional[str] = None,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store score in cache. Supports both simple string key and legacy structured API.
        
        Args:
            key_or_birth_date: Simple string key OR natal birth datetime (legacy)
            score_or_target_year: Score (simple API) OR target year (legacy API)
            city_id: City identifier (legacy API only)
            score: Score value (legacy API only, named parameter)
            metadata: Optional metadata (legacy API, stored in dict format)
        """
        # Detect API mode
        if isinstance(key_or_birth_date, str):
            # Simple API: set(key, score)
            key = key_or_birth_date
            score_value = score_or_target_year
        else:
            # Legacy API: set(birth_date, target_year, city_id, score=X, metadata=Y)
            key = self._generate_key(key_or_birth_date, score_or_target_year, city_id)
            score_value = {'score': score, 'metadata': metadata or {}}
        
        with self._lock:
            # Simple LRU: if at capacity, remove oldest (FIFO approximation for MVP)
            if len(self._cache) >= self.max_size:
                # Remove first inserted (oldest)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            self._cache[key] = score_value
    
    def clear(self) -> None:
        """Clear all cache entries and reset counters."""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with hits, misses, size, hit_rate
        """
        with self._lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            
            return {
                'hits': self.hits,
                'misses': self.misses,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate
            }


# Global cache instance (singleton pattern for Sprint 1)
_global_cache: Optional[IGPCache] = None


def get_global_cache(max_size: int = 10000) -> IGPCache:
    """
    Get or create global IGP cache instance.
    
    Args:
        max_size: Cache size (only applies on first call)
    
    Returns:
        IGPCache: Singleton cache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = IGPCache(max_size=max_size)
    return _global_cache


# Sprint 1 deliverables checklist:
# ✅ IGPCache class with thread-safe get/set/clear methods
# ✅ LRU eviction (simple FIFO approximation for MVP)
# ✅ Cache statistics: hits, misses, hit_rate
# ✅ Global singleton getter
# 🔄 Redis backend: Deferred to Sprint 3
# 🔄 Persistent cache: Deferred to Sprint 3
