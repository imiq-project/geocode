"""
Thread-safe TTL in-memory cache for geocoding results.
No external dependency — drop-in for Redis later if needed.
"""

import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Optional


class GeoCache:
    """
    LRU cache with per-entry TTL.

    - maxsize: max number of entries before oldest are evicted
    - ttl: seconds before an entry is considered stale
    """

    def __init__(self, maxsize: int = 2000, ttl: int = 3600):
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                return None
            value, expires_at = self._store[key]
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            # Move to end (LRU)
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            expires_at = time.monotonic() + self._ttl
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, expires_at)
            if len(self._store) > self._maxsize:
                self._store.popitem(last=False)  # Evict oldest

    def size(self) -> int:
        with self._lock:
            return len(self._store)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()