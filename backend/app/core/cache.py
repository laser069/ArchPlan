"""
Response caching utilities for performance optimization.
"""
import hashlib
import json
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

# In-memory cache store
_cache: Dict[str, tuple[Any, datetime]] = {}

# Cache TTL in seconds
DEFAULT_TTL_SECONDS = 3600  # 1 hour
CONSTRAINT_CACHE_TTL = 1800  # 30 minutes
ARCHITECTURE_CACHE_TTL = 3600  # 1 hour


def _generate_cache_key(data: Dict[str, Any]) -> str:
    """Generate a cache key from request data."""
    # Create a canonical representation
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve value from cache if not expired.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found or expired
    """
    if key not in _cache:
        return None
    
    value, expiry = _cache[key]
    
    if datetime.now() > expiry:
        # Cache expired, remove it
        del _cache[key]
        return None
    
    return value


def cache_set(key: str, value: Any, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
    """
    Store value in cache with TTL.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl_seconds: Time to live in seconds
    """
    expiry = datetime.now() + timedelta(seconds=ttl_seconds)
    _cache[key] = (value, expiry)


def cache_constraint_extraction(query: str, constraints: Dict[str, Any]) -> str:
    """
    Cache extracted constraints from a query.
    
    Args:
        query: Original query
        constraints: Extracted constraints
        
    Returns:
        Cache key
    """
    cache_key = f"constraints:{_generate_cache_key({'query': query})}"
    cache_set(cache_key, constraints, CONSTRAINT_CACHE_TTL)
    return cache_key


def get_cached_constraints(query: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached constraints for a query.
    
    Args:
        query: Original query
        
    Returns:
        Cached constraints or None
    """
    cache_key = f"constraints:{_generate_cache_key({'query': query})}"
    return cache_get(cache_key)


def cache_architecture(request_data: Dict[str, Any], response: Dict[str, Any]) -> str:
    """
    Cache generated architecture.
    
    Args:
        request_data: Request that generated the architecture
        response: Generated architecture response
        
    Returns:
        Cache key
    """
    cache_key = f"architecture:{_generate_cache_key(request_data)}"
    cache_set(cache_key, response, ARCHITECTURE_CACHE_TTL)
    return cache_key


def get_cached_architecture(request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached architecture for a request.
    
    Args:
        request_data: Request to look up
        
    Returns:
        Cached architecture or None
    """
    cache_key = f"architecture:{_generate_cache_key(request_data)}"
    return cache_get(cache_key)


def cache_clear() -> None:
    """Clear all cache entries."""
    global _cache
    _cache = {}


def cache_cleanup() -> int:
    """
    Remove expired cache entries.
    
    Returns:
        Number of entries removed
    """
    expired_keys = []
    
    for key, (value, expiry) in _cache.items():
        if datetime.now() > expiry:
            expired_keys.append(key)
    
    for key in expired_keys:
        del _cache[key]
    
    return len(expired_keys)


def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    total_entries = len(_cache)
    
    # Clean expired entries
    cleanup_count = cache_cleanup()
    
    return {
        "total_entries": total_entries - cleanup_count,
        "expired_cleaned": cleanup_count,
        "memory_usage": "Not available",
    }
