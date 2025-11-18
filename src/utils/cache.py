"""Simple caching system for Notion data."""
import json
import time
from pathlib import Path
from typing import Any, Optional
from functools import wraps

from .config import settings
from .logger import setup_logger

logger = setup_logger(__name__)


class SimpleCache:
    """Simple in-memory and disk cache with TTL support."""

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: int = 3600):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for disk cache.
            default_ttl: Default time-to-live in seconds (default: 1 hour).
        """
        self.cache_dir = cache_dir or settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

        # In-memory cache: {key: (value, expiry_time)}
        self._memory_cache = {}

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Create safe filename from key
        safe_key = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str, use_disk: bool = True) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key.
            use_disk: Whether to check disk cache if not in memory.

        Returns:
            Cached value or None if not found/expired.
        """
        # Check memory cache first
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]

            if time.time() < expiry:
                logger.debug(f"Cache hit (memory): {key}")
                return value
            else:
                # Expired
                del self._memory_cache[key]
                logger.debug(f"Cache expired (memory): {key}")

        # Check disk cache
        if use_disk:
            cache_file = self._get_cache_file(key)

            if cache_file.exists():
                try:
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)

                    expiry = cache_data.get("expiry", 0)
                    if time.time() < expiry:
                        value = cache_data.get("value")
                        # Store in memory for faster access
                        self._memory_cache[key] = (value, expiry)
                        logger.debug(f"Cache hit (disk): {key}")
                        return value
                    else:
                        # Expired
                        cache_file.unlink()
                        logger.debug(f"Cache expired (disk): {key}")

                except Exception as e:
                    logger.warning(f"Error reading cache file: {e}")

        logger.debug(f"Cache miss: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None, use_disk: bool = True):
        """
        Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (None = use default).
            use_disk: Whether to also save to disk.
        """
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl

        # Store in memory
        self._memory_cache[key] = (value, expiry)

        # Store on disk
        if use_disk:
            cache_file = self._get_cache_file(key)

            try:
                cache_data = {
                    "value": value,
                    "expiry": expiry,
                    "created_at": time.time()
                }

                with open(cache_file, "w") as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)

                logger.debug(f"Cache set (disk): {key} (TTL: {ttl}s)")

            except Exception as e:
                logger.warning(f"Error writing cache file: {e}")

        logger.debug(f"Cache set (memory): {key} (TTL: {ttl}s)")

    def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key.
        """
        # Remove from memory
        if key in self._memory_cache:
            del self._memory_cache[key]

        # Remove from disk
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            cache_file.unlink()

        logger.debug(f"Cache deleted: {key}")

    def clear(self):
        """Clear all cache."""
        # Clear memory
        self._memory_cache.clear()

        # Clear disk
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

        logger.info("Cache cleared")

    def cleanup_expired(self):
        """Remove expired entries from disk cache."""
        now = time.time()
        removed = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                expiry = cache_data.get("expiry", 0)
                if now >= expiry:
                    cache_file.unlink()
                    removed += 1

            except Exception as e:
                logger.warning(f"Error checking cache file {cache_file}: {e}")

        if removed > 0:
            logger.info(f"Cleaned up {removed} expired cache entries")


# Global cache instance
_global_cache = None


def get_cache() -> SimpleCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = SimpleCache()
    return _global_cache


def cached(ttl: int = 3600, use_disk: bool = True):
    """
    Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds.
        use_disk: Whether to use disk cache.

    Usage:
        @cached(ttl=600)
        def expensive_function(arg1, arg2):
            # ...
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__module__}.{func.__name__}:{str(args)}:{str(kwargs)}"

            cache = get_cache()

            # Try to get from cache
            result = cache.get(cache_key, use_disk=use_disk)

            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl, use_disk=use_disk)

            return result

        return wrapper

    return decorator
