"""
Cache Manager for TripPlanner
==============================

Implements smart caching to minimize API calls and respect rate limits.

Features:
- File-based caching (no Redis dependency)
- TTL (Time To Live) support
- Automatic cache cleanup
- Rate limit tracking
- Cache statistics

Cache Strategy:
- Weather data: 3 hours (weather doesn't change frequently)
- Google Places data: 24 hours (place info is relatively static)
- User preferences: 1 hour (allow updates to propagate)
- Reviews/insights: 12 hours (reviews don't change often)
"""

import json
import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching with TTL and rate limiting"""

    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Create subdirectories for different cache types
        (self.cache_dir / "weather").mkdir(exist_ok=True)
        (self.cache_dir / "places").mkdir(exist_ok=True)
        (self.cache_dir / "memory").mkdir(exist_ok=True)
        (self.cache_dir / "routes").mkdir(exist_ok=True)

        # Rate limit tracking
        self.rate_limits_file = self.cache_dir / "rate_limits.json"
        self.rate_limits = self._load_rate_limits()

        # Cache TTL settings (in seconds)
        self.ttl_config = {
            "weather": 3 * 60 * 60,      # 3 hours
            "places": 24 * 60 * 60,      # 24 hours
            "restaurants": 12 * 60 * 60, # 12 hours
            "reviews": 12 * 60 * 60,     # 12 hours
            "memory": 1 * 60 * 60,       # 1 hour
            "routes": 6 * 60 * 60,       # 6 hours
            "default": 1 * 60 * 60       # 1 hour default
        }

        # API call limits (per hour)
        self.api_limits = {
            "weather": {"limit": 60, "period": 3600},      # 60 calls/hour
            "google_places": {"limit": 100, "period": 3600}, # 100 calls/hour
            "google_maps": {"limit": 100, "period": 3600},   # 100 calls/hour
        }

        logger.info(f"Cache manager initialized at {self.cache_dir}")

    def _load_rate_limits(self) -> Dict:
        """Load rate limit tracking from file"""
        if self.rate_limits_file.exists():
            try:
                with open(self.rate_limits_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load rate limits: {e}")
        return {}

    def _save_rate_limits(self):
        """Save rate limit tracking to file"""
        try:
            with open(self.rate_limits_file, 'w') as f:
                json.dump(self.rate_limits, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save rate limits: {e}")

    def _generate_cache_key(self, category: str, **kwargs) -> str:
        """
        Generate a unique cache key from parameters

        Args:
            category: Cache category (weather, places, etc.)
            **kwargs: Parameters to hash into the key

        Returns:
            Cache key string
        """
        # Sort kwargs for consistent hashing
        sorted_params = sorted(kwargs.items())
        param_str = json.dumps(sorted_params, sort_keys=True)
        hash_digest = hashlib.md5(param_str.encode()).hexdigest()
        return f"{category}_{hash_digest}"

    def _get_cache_path(self, category: str, cache_key: str) -> Path:
        """Get the file path for a cache entry"""
        return self.cache_dir / category / f"{cache_key}.json"

    def get(self, category: str, **kwargs) -> Optional[Any]:
        """
        Get cached data if available and not expired

        Args:
            category: Cache category
            **kwargs: Parameters used to generate cache key

        Returns:
            Cached data or None if not found/expired
        """
        cache_key = self._generate_cache_key(category, **kwargs)
        cache_path = self._get_cache_path(category, cache_key)

        if not cache_path.exists():
            logger.debug(f"Cache miss: {category} - {kwargs}")
            return None

        try:
            with open(cache_path, 'r') as f:
                cache_entry = json.load(f)

            # Check if expired
            ttl = self.ttl_config.get(category, self.ttl_config["default"])
            cached_time = cache_entry.get("cached_at", 0)
            current_time = time.time()

            if current_time - cached_time > ttl:
                logger.debug(f"Cache expired: {category} - {kwargs}")
                # Delete expired cache
                cache_path.unlink()
                return None

            logger.info(f"Cache hit: {category} - {kwargs}")
            return cache_entry.get("data")

        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None

    def set(self, category: str, data: Any, **kwargs):
        """
        Cache data with current timestamp

        Args:
            category: Cache category
            data: Data to cache
            **kwargs: Parameters used to generate cache key
        """
        cache_key = self._generate_cache_key(category, **kwargs)
        cache_path = self._get_cache_path(category, cache_key)

        cache_entry = {
            "cached_at": time.time(),
            "category": category,
            "params": kwargs,
            "data": data
        }

        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            logger.info(f"Cached: {category} - {kwargs}")
        except Exception as e:
            logger.error(f"Error writing cache: {e}")

    def check_rate_limit(self, api_name: str) -> bool:
        """
        Check if API call is within rate limit

        Args:
            api_name: Name of the API (weather, google_places, etc.)

        Returns:
            True if call is allowed, False if rate limit exceeded
        """
        if api_name not in self.api_limits:
            return True  # No limit configured

        limit_config = self.api_limits[api_name]
        current_time = time.time()

        # Initialize if not exists
        if api_name not in self.rate_limits:
            self.rate_limits[api_name] = {
                "calls": [],
                "total_calls": 0
            }

        # Remove old calls outside the time window
        period = limit_config["period"]
        self.rate_limits[api_name]["calls"] = [
            call_time for call_time in self.rate_limits[api_name]["calls"]
            if current_time - call_time < period
        ]

        # Check if under limit
        call_count = len(self.rate_limits[api_name]["calls"])
        if call_count >= limit_config["limit"]:
            logger.warning(
                f"Rate limit exceeded for {api_name}: "
                f"{call_count}/{limit_config['limit']} calls in last {period}s"
            )
            return False

        return True

    def record_api_call(self, api_name: str):
        """
        Record an API call for rate limiting

        Args:
            api_name: Name of the API
        """
        if api_name not in self.rate_limits:
            self.rate_limits[api_name] = {
                "calls": [],
                "total_calls": 0
            }

        current_time = time.time()
        self.rate_limits[api_name]["calls"].append(current_time)
        self.rate_limits[api_name]["total_calls"] += 1

        logger.debug(f"API call recorded: {api_name}")
        self._save_rate_limits()

    def get_rate_limit_status(self, api_name: str) -> Dict:
        """
        Get current rate limit status for an API

        Args:
            api_name: Name of the API

        Returns:
            Dictionary with rate limit status
        """
        if api_name not in self.api_limits:
            return {"status": "no_limit"}

        if api_name not in self.rate_limits:
            return {
                "status": "ok",
                "calls_used": 0,
                "calls_remaining": self.api_limits[api_name]["limit"],
                "limit": self.api_limits[api_name]["limit"],
                "reset_in": self.api_limits[api_name]["period"]
            }

        limit_config = self.api_limits[api_name]
        current_time = time.time()
        period = limit_config["period"]

        # Count recent calls
        recent_calls = [
            call_time for call_time in self.rate_limits[api_name]["calls"]
            if current_time - call_time < period
        ]

        calls_used = len(recent_calls)
        calls_remaining = limit_config["limit"] - calls_used

        # Calculate reset time
        if recent_calls:
            oldest_call = min(recent_calls)
            reset_in = int(period - (current_time - oldest_call))
        else:
            reset_in = period

        return {
            "status": "ok" if calls_remaining > 0 else "limit_exceeded",
            "calls_used": calls_used,
            "calls_remaining": max(0, calls_remaining),
            "limit": limit_config["limit"],
            "reset_in": reset_in,
            "total_calls": self.rate_limits[api_name].get("total_calls", 0)
        }

    def clear_category(self, category: str):
        """Clear all cache entries in a category"""
        category_path = self.cache_dir / category
        if category_path.exists():
            for cache_file in category_path.glob("*.json"):
                cache_file.unlink()
            logger.info(f"Cleared cache category: {category}")

    def clear_all(self):
        """Clear all cache entries"""
        for category_path in self.cache_dir.iterdir():
            if category_path.is_dir():
                for cache_file in category_path.glob("*.json"):
                    cache_file.unlink()
        logger.info("Cleared all cache")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {
            "categories": {},
            "total_entries": 0,
            "total_size_bytes": 0,
            "rate_limits": {}
        }

        for category_path in self.cache_dir.iterdir():
            if category_path.is_dir() and category_path.name != "__pycache__":
                cache_files = list(category_path.glob("*.json"))
                category_name = category_path.name

                size_bytes = sum(f.stat().st_size for f in cache_files)

                stats["categories"][category_name] = {
                    "entries": len(cache_files),
                    "size_bytes": size_bytes,
                    "size_kb": round(size_bytes / 1024, 2)
                }

                stats["total_entries"] += len(cache_files)
                stats["total_size_bytes"] += size_bytes

        stats["total_size_kb"] = round(stats["total_size_bytes"] / 1024, 2)

        # Add rate limit stats
        for api_name in self.api_limits.keys():
            stats["rate_limits"][api_name] = self.get_rate_limit_status(api_name)

        return stats

    def cleanup_expired(self):
        """Remove all expired cache entries"""
        current_time = time.time()
        removed_count = 0

        for category_path in self.cache_dir.iterdir():
            if not category_path.is_dir() or category_path.name == "__pycache__":
                continue

            category_name = category_path.name
            ttl = self.ttl_config.get(category_name, self.ttl_config["default"])

            for cache_file in category_path.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        cache_entry = json.load(f)

                    cached_time = cache_entry.get("cached_at", 0)
                    if current_time - cached_time > ttl:
                        cache_file.unlink()
                        removed_count += 1
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")

        logger.info(f"Cleaned up {removed_count} expired cache entries")
        return removed_count


# Global cache manager instance
cache_manager = CacheManager()


# Decorator for automatic caching
def cached(category: str, ttl: Optional[int] = None):
    """
    Decorator to automatically cache function results

    Args:
        category: Cache category
        ttl: Time to live in seconds (optional, uses default if not provided)

    Example:
        @cached("weather", ttl=3600)
        def get_weather(city: str):
            return fetch_weather_from_api(city)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cache_params = {"args": args, "kwargs": kwargs}
            cached_result = cache_manager.get(category, **cache_params)

            if cached_result is not None:
                return cached_result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(category, result, **cache_params)

            return result

        return wrapper
    return decorator


# Helper function for API calls with rate limiting
def rate_limited_api_call(api_name: str, func, *args, **kwargs):
    """
    Execute an API call with rate limit checking

    Args:
        api_name: Name of the API for rate limiting
        func: Function to call
        *args, **kwargs: Arguments to pass to the function

    Returns:
        Function result or raises exception if rate limited

    Raises:
        Exception: If rate limit is exceeded
    """
    if not cache_manager.check_rate_limit(api_name):
        status = cache_manager.get_rate_limit_status(api_name)
        raise Exception(
            f"Rate limit exceeded for {api_name}. "
            f"Used {status['calls_used']}/{status['limit']} calls. "
            f"Resets in {status['reset_in']} seconds."
        )

    # Record the call
    cache_manager.record_api_call(api_name)

    # Execute the function
    return func(*args, **kwargs)


if __name__ == "__main__":
    # Example usage
    print("Cache Manager - Example Usage")
    print("=" * 50)

    # Get cache stats
    stats = cache_manager.get_cache_stats()
    print("\nCache Statistics:")
    print(json.dumps(stats, indent=2))

    # Test caching
    print("\n\nTesting cache operations...")

    # Cache weather data
    weather_data = {"temp": 28, "condition": "sunny"}
    cache_manager.set("weather", weather_data, city="Delhi", days=3)
    print("✅ Cached weather data for Delhi")

    # Retrieve from cache
    cached_weather = cache_manager.get("weather", city="Delhi", days=3)
    print(f"✅ Retrieved from cache: {cached_weather}")

    # Test rate limiting
    print("\n\nTesting rate limits...")
    for i in range(5):
        if cache_manager.check_rate_limit("weather"):
            cache_manager.record_api_call("weather")
            print(f"✅ API call {i+1} allowed")
        else:
            print(f"❌ API call {i+1} blocked by rate limit")

    # Show rate limit status
    status = cache_manager.get_rate_limit_status("weather")
    print(f"\nRate Limit Status: {json.dumps(status, indent=2)}")

    print("\n" + "=" * 50)
    print("Cache manager ready for use!")
