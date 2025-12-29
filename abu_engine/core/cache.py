"""Lightweight in-memory caching utilities with TTL and LRU semantics.

Provides thread-safe caches for:
 - Ephemeris planetary positions (rounded to 1 minute + lat/lon key)
 - Current Firdaria period (birth date + query day)

Uses simple dict + OrderedDict structure to avoid external dependencies.
TTL default: 12 hours.
Verbose logging activated when environment variable ABU_VERBOSE=1.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
import os
import logging
from typing import Any, Dict, Tuple

TTL_HOURS = 12
TTL = timedelta(hours=TTL_HOURS)

VERBOSE = os.getenv("ABU_VERBOSE", "0") == "1"


def _log(msg: str):
    if VERBOSE:
        logging.info(f"[Cache] {msg}")


@dataclass
class CacheItem:
    value: Any
    timestamp: datetime


class TTLCache:
    """Simple LRU + TTL cache.

    Not super optimized but adequate for small key sets.
    """

    def __init__(self, maxsize: int = 512, ttl: timedelta = TTL):
        self.maxsize = maxsize
        self.ttl = ttl
        self._data: OrderedDict[Tuple[Any, ...], CacheItem] = OrderedDict()
        self._lock = Lock()

    def get(self, key: Tuple[Any, ...]):
        now = datetime.now(timezone.utc)
        with self._lock:
            item = self._data.get(key)
            if item is None:
                _log(f"MISS {key}")
                return None
            # TTL check
            if now - item.timestamp > self.ttl:
                _log(f"EXPIRED {key}")
                try:
                    del self._data[key]
                except KeyError:
                    pass
                return None
            # Move to end (LRU)
            self._data.move_to_end(key)
            _log(f"HIT {key}")
            return item.value

    def set(self, key: Tuple[Any, ...], value: Any):
        now = datetime.now(timezone.utc)
        with self._lock:
            if key in self._data:
                # overwrite + move to end
                self._data[key] = CacheItem(value=value, timestamp=now)
                self._data.move_to_end(key)
            else:
                self._data[key] = CacheItem(value=value, timestamp=now)
                self._data.move_to_end(key)
                if len(self._data) > self.maxsize:
                    # pop oldest
                    oldest_key, _ = self._data.popitem(last=False)
                    _log(f"EVICT {oldest_key}")


# Instantiate caches
ephemeris_cache = TTLCache(maxsize=1024)
firdaria_cache = TTLCache(maxsize=1024)


def cache_ephemeris_positions(dt: datetime, lat: float, lon: float, compute_fn):
    """Cache wrapper for planetary positions.

    Key uses datetime rounded to minute + lat/lon (even though planetary longitudes
    are independent of observer lat/lon, houses may later use location so keep them).
    """
    # ensure timezone aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    rounded = dt.replace(second=0, microsecond=0)
    key = (rounded.isoformat(), round(lat, 4), round(lon, 4))
    cached = ephemeris_cache.get(key)
    if cached is not None:
        return cached
    value = compute_fn()
    ephemeris_cache.set(key, value)
    return value


def cache_firdaria(birth_date: datetime, query_date: datetime, is_diurnal: bool, compute_fn):
    """Cache wrapper for current firdaria period.

    Key uses birth date (date only) + query date (date only) + diurnal flag.
    """
    if birth_date.tzinfo is None:
        birth_date = birth_date.replace(tzinfo=timezone.utc)
    if query_date.tzinfo is None:
        query_date = query_date.replace(tzinfo=timezone.utc)
    key = (birth_date.date().isoformat(), query_date.date().isoformat(), bool(is_diurnal))
    cached = firdaria_cache.get(key)
    if cached is not None:
        return cached
    value = compute_fn()
    firdaria_cache.set(key, value)
    return value
