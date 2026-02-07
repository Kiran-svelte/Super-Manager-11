"""
Caching Layer Module
====================

Multi-tier caching system supporting:
- In-memory caching (LRU)
- Redis caching
- Distributed caching patterns
- Cache invalidation strategies

Author: Super Manager
Version: 1.0.0
"""

import os
import json
import time
import hashlib
import threading
import asyncio
from typing import Any, Optional, Callable, Dict, List, TypeVar
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# In-Memory LRU Cache
# =============================================================================

class LRUCache:
    """
    Thread-safe LRU cache with TTL support
    
    Features:
    - O(1) get/set operations
    - Automatic expiration
    - Size limits
    - Hit/miss statistics
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._expiry: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            
            # Check expiration
            if key in self._expiry and time.time() > self._expiry[key]:
                self._delete(key)
                self._misses += 1
                return default
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache with optional TTL"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    # Remove least recently used
                    oldest = next(iter(self._cache))
                    self._delete(oldest)
            
            self._cache[key] = value
            
            ttl = ttl if ttl is not None else self.default_ttl
            if ttl > 0:
                self._expiry[key] = time.time() + ttl
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            return self._delete(key)
    
    def _delete(self, key: str) -> bool:
        """Internal delete (caller must hold lock)"""
        if key in self._cache:
            del self._cache[key]
            self._expiry.pop(key, None)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()
            self._hits = 0
            self._misses = 0
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        with self._lock:
            now = time.time()
            expired = [k for k, v in self._expiry.items() if now > v]
            for key in expired:
                self._delete(key)
            return len(expired)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
                "expiring_entries": len(self._expiry)
            }


# =============================================================================
# Redis Cache Wrapper
# =============================================================================

class RedisCache:
    """
    Redis cache wrapper with connection pooling
    
    Features:
    - Connection pooling
    - Automatic serialization
    - Cluster support
    - Graceful fallback
    """
    
    def __init__(self, url: str = None, prefix: str = "supermanager:"):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.prefix = prefix
        self._client = None
        self._available = False
        self._init_client()
    
    def _init_client(self):
        """Initialize Redis client"""
        try:
            import redis
            self._client = redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self._client.ping()
            self._available = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache: {e}")
            self._available = False
    
    @property
    def available(self) -> bool:
        """Check if Redis is available"""
        return self._available
    
    def _key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.prefix}{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis"""
        if not self._available:
            return default
        
        try:
            value = self._client.get(self._key(key))
            if value is None:
                return default
            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in Redis with TTL"""
        if not self._available:
            return False
        
        try:
            serialized = json.dumps(value)
            if ttl > 0:
                self._client.setex(self._key(key), ttl, serialized)
            else:
                self._client.set(self._key(key), serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self._available:
            return False
        
        try:
            return self._client.delete(self._key(key)) > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._available:
            return 0
        
        try:
            keys = self._client.keys(self._key(pattern))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete_pattern error: {e}")
            return 0
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        if not self._available:
            return 0
        
        try:
            return self._client.incrby(self._key(key), amount)
        except Exception as e:
            logger.error(f"Redis incr error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        if not self._available:
            return {"available": False}
        
        try:
            info = self._client.info()
            return {
                "available": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "total_connections_received": info.get("total_connections_received", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# =============================================================================
# Multi-Tier Cache
# =============================================================================

class MultiTierCache:
    """
    Multi-tier caching with L1 (memory) and L2 (Redis) layers
    
    Strategy:
    1. Check L1 (memory) first - fastest
    2. If miss, check L2 (Redis)
    3. If L2 hit, populate L1
    4. On write, write-through to both layers
    """
    
    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_ttl: int = 60,
        l2_ttl: int = 300,
        redis_url: str = None
    ):
        self.l1 = LRUCache(max_size=l1_max_size, default_ttl=l1_ttl)
        self.l2 = RedisCache(url=redis_url)
        self.l2_ttl = l2_ttl
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (L1 -> L2)"""
        # Try L1 first
        value = self.l1.get(key)
        if value is not None:
            return value
        
        # Try L2
        if self.l2.available:
            value = self.l2.get(key)
            if value is not None:
                # Populate L1
                self.l1.set(key, value)
                return value
        
        return default
    
    def set(self, key: str, value: Any, l1_ttl: int = None, l2_ttl: int = None) -> None:
        """Set value in both layers (write-through)"""
        self.l1.set(key, value, ttl=l1_ttl)
        
        if self.l2.available:
            self.l2.set(key, value, ttl=l2_ttl or self.l2_ttl)
    
    def delete(self, key: str) -> None:
        """Delete from both layers"""
        self.l1.delete(key)
        self.l2.delete(key)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern"""
        # Clear L1 (can't do pattern match efficiently)
        self.l1.clear()
        
        # Delete from L2
        return self.l2.delete_pattern(pattern)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from both layers"""
        return {
            "l1": self.l1.get_stats(),
            "l2": self.l2.get_stats()
        }


# Global cache instance
cache = MultiTierCache()


# =============================================================================
# Cache Decorators
# =============================================================================

def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Callable = None,
    cache_none: bool = False
):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
        key_builder: Custom function to build cache key
        cache_none: Whether to cache None results
    
    Example:
        @cached(ttl=60, key_prefix="user")
        def get_user(user_id: str):
            return db.get_user(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key: prefix:function:args_hash
                args_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
                args_hash = hashlib.md5(args_str.encode()).hexdigest()[:12]
                cache_key = f"{key_prefix}:{func.__name__}:{args_hash}"
            
            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None or cache_none:
                cache.set(cache_key, result, l1_ttl=min(ttl, 60), l2_ttl=ttl)
            
            return result
        
        # Add cache control methods
        wrapper.cache_clear = lambda: cache.invalidate_pattern(f"*{key_prefix}:{func.__name__}:*")
        wrapper.cache_key = lambda *a, **kw: f"{key_prefix}:{func.__name__}:{hashlib.md5(json.dumps({'args': a, 'kwargs': kw}, sort_keys=True, default=str).encode()).hexdigest()[:12]}"
        
        return wrapper
    return decorator


def async_cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Callable = None,
    cache_none: bool = False
):
    """
    Decorator to cache async function results
    
    Example:
        @async_cached(ttl=60)
        async def fetch_data(item_id: str):
            return await db.fetch(item_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                args_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
                args_hash = hashlib.md5(args_str.encode()).hexdigest()[:12]
                cache_key = f"{key_prefix}:{func.__name__}:{args_hash}"
            
            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Call async function
            result = await func(*args, **kwargs)
            
            # Cache result
            if result is not None or cache_none:
                cache.set(cache_key, result, l1_ttl=min(ttl, 60), l2_ttl=ttl)
            
            return result
        
        wrapper.cache_clear = lambda: cache.invalidate_pattern(f"*{key_prefix}:{func.__name__}:*")
        
        return wrapper
    return decorator


# =============================================================================
# Response Caching Middleware
# =============================================================================

@dataclass
class CacheConfig:
    """Configuration for response caching"""
    enabled: bool = True
    default_ttl: int = 60
    max_size_bytes: int = 1024 * 1024  # 1MB max response size to cache
    excluded_paths: List[str] = field(default_factory=list)
    included_methods: List[str] = field(default_factory=lambda: ["GET"])
    vary_headers: List[str] = field(default_factory=lambda: ["Accept", "Accept-Encoding"])


class ResponseCache:
    """
    HTTP response caching
    
    Features:
    - Path-based caching rules
    - Method filtering
    - Response size limits
    - Vary header support
    """
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self._cache = LRUCache(max_size=500, default_ttl=self.config.default_ttl)
    
    def _build_key(self, method: str, path: str, headers: Dict[str, str] = None) -> str:
        """Build cache key from request"""
        key_parts = [method, path]
        
        if headers and self.config.vary_headers:
            for header in self.config.vary_headers:
                if header.lower() in {h.lower() for h in headers}:
                    key_parts.append(f"{header}={headers.get(header, '')}")
        
        return ":".join(key_parts)
    
    def should_cache(self, method: str, path: str) -> bool:
        """Check if request should be cached"""
        if not self.config.enabled:
            return False
        
        if method not in self.config.included_methods:
            return False
        
        for excluded in self.config.excluded_paths:
            if path.startswith(excluded):
                return False
        
        return True
    
    def get(self, method: str, path: str, headers: Dict[str, str] = None) -> Optional[Dict]:
        """Get cached response"""
        if not self.should_cache(method, path):
            return None
        
        key = self._build_key(method, path, headers)
        return self._cache.get(key)
    
    def set(self, method: str, path: str, response: Dict, headers: Dict[str, str] = None, ttl: int = None) -> bool:
        """Cache a response"""
        if not self.should_cache(method, path):
            return False
        
        # Check response size
        response_str = json.dumps(response)
        if len(response_str) > self.config.max_size_bytes:
            return False
        
        key = self._build_key(method, path, headers)
        self._cache.set(key, response, ttl=ttl or self.config.default_ttl)
        return True
    
    def invalidate(self, path: str) -> None:
        """Invalidate cache for a path"""
        # Clear all entries (simple approach)
        self._cache.clear()


# =============================================================================
# Cache Warmup
# =============================================================================

class CacheWarmer:
    """
    Pre-warm cache with frequently accessed data
    
    Usage:
        warmer = CacheWarmer()
        warmer.register("users", lambda: db.get_active_users())
        warmer.register("config", lambda: load_config())
        await warmer.warm_all()
    """
    
    def __init__(self):
        self._warmers: Dict[str, Dict] = {}
    
    def register(self, key: str, loader: Callable, ttl: int = 300):
        """Register a cache warmer"""
        self._warmers[key] = {
            "loader": loader,
            "ttl": ttl
        }
    
    async def warm(self, key: str) -> bool:
        """Warm a specific cache key"""
        if key not in self._warmers:
            return False
        
        warmer = self._warmers[key]
        try:
            result = warmer["loader"]()
            if asyncio.iscoroutine(result):
                result = await result
            
            cache.set(key, result, l2_ttl=warmer["ttl"])
            logger.info(f"Cache warmed: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache warm failed for {key}: {e}")
            return False
    
    async def warm_all(self) -> Dict[str, bool]:
        """Warm all registered caches"""
        results = {}
        for key in self._warmers:
            results[key] = await self.warm(key)
        return results


cache_warmer = CacheWarmer()
