"""Simple in-memory + disk-friendly caching helpers."""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable


class TTLCache:
    """Very small thread-unsafe TTL cache for single-process use."""

    def __init__(self, ttl_seconds: int = 120):
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        ts, value = item
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)

    def clear(self) -> None:
        self._store.clear()


# Global cache instance (one per process)
_default_cache = TTLCache(ttl_seconds=120)


def cached(ttl: int | None = None) -> Callable:
    """Decorator for simple function result caching."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"{fn.__name__}:{args}:{sorted(kwargs.items())}"
            cache = _default_cache
            if ttl is not None:
                # temporary override not fully supported; use default for simplicity
                pass
            hit = cache.get(key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper

    return decorator


def get_cache() -> TTLCache:
    return _default_cache
