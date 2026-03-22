"""
Behavioral Tests: Cache Module
================================
Tests that the cache module ACTUALLY works:
- LRUCache class
- TTL support
- Size limits
- Hit/miss statistics

README Requirements:
- In-memory LRU cache
- Thread-safe operations
- Automatic expiration
- Size limits
"""

import pytest
import time
import threading
from collections import OrderedDict

from backend.core.cache import LRUCache


class TestLRUCacheInit:
    """Test LRUCache initialization"""
    
    def test_can_instantiate(self):
        """LRUCache should be instantiatable"""
        cache = LRUCache()
        assert cache is not None
    
    def test_default_max_size(self):
        """LRUCache should have default max_size of 1000"""
        cache = LRUCache()
        assert cache.max_size == 1000
    
    def test_custom_max_size(self):
        """LRUCache should accept custom max_size"""
        cache = LRUCache(max_size=100)
        assert cache.max_size == 100
    
    def test_default_ttl(self):
        """LRUCache should have default_ttl of 300"""
        cache = LRUCache()
        assert cache.default_ttl == 300
    
    def test_custom_ttl(self):
        """LRUCache should accept custom default_ttl"""
        cache = LRUCache(default_ttl=60)
        assert cache.default_ttl == 60
    
    def test_has_cache_ordered_dict(self):
        """LRUCache should use OrderedDict internally"""
        cache = LRUCache()
        assert hasattr(cache, "_cache")
        assert isinstance(cache._cache, OrderedDict)
    
    def test_has_expiry_dict(self):
        """LRUCache should have _expiry dict"""
        cache = LRUCache()
        assert hasattr(cache, "_expiry")
        assert isinstance(cache._expiry, dict)
    
    def test_has_lock(self):
        """LRUCache should have thread lock"""
        cache = LRUCache()
        assert hasattr(cache, "_lock")
    
    def test_initial_hits_zero(self):
        """LRUCache should start with 0 hits"""
        cache = LRUCache()
        assert cache._hits == 0
    
    def test_initial_misses_zero(self):
        """LRUCache should start with 0 misses"""
        cache = LRUCache()
        assert cache._misses == 0


class TestLRUCacheGet:
    """Test LRUCache get operation"""
    
    def test_get_nonexistent_returns_none(self):
        """get should return None for nonexistent key"""
        cache = LRUCache()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_get_nonexistent_returns_default(self):
        """get should return default for nonexistent key"""
        cache = LRUCache()
        result = cache.get("nonexistent", default="fallback")
        assert result == "fallback"
    
    def test_get_existing_key(self):
        """get should return value for existing key"""
        cache = LRUCache()
        cache.set("key", "value")
        result = cache.get("key")
        assert result == "value"
    
    def test_get_increments_hits(self):
        """get on existing key should increment hits"""
        cache = LRUCache()
        cache.set("key", "value")
        
        cache.get("key")
        
        assert cache._hits == 1
    
    def test_get_increments_misses(self):
        """get on nonexistent key should increment misses"""
        cache = LRUCache()
        
        cache.get("nonexistent")
        
        assert cache._misses == 1


class TestLRUCacheSet:
    """Test LRUCache set operation"""
    
    def test_set_stores_value(self):
        """set should store value"""
        cache = LRUCache()
        cache.set("key", "value")
        assert cache.get("key") == "value"
    
    def test_set_stores_various_types(self):
        """set should store various types"""
        cache = LRUCache()
        
        cache.set("string", "hello")
        cache.set("int", 42)
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"a": 1})
        
        assert cache.get("string") == "hello"
        assert cache.get("int") == 42
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"a": 1}
    
    def test_set_overwrites_existing(self):
        """set should overwrite existing key"""
        cache = LRUCache()
        cache.set("key", "old")
        cache.set("key", "new")
        assert cache.get("key") == "new"
    
    def test_set_uses_default_ttl(self):
        """set should use default_ttl if not specified"""
        cache = LRUCache(default_ttl=1)
        cache.set("key", "value")
        
        # Should exist immediately
        assert cache.get("key") == "value"
        
        # Wait for expiry
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("key") is None
    
    def test_set_custom_ttl(self):
        """set should accept custom TTL"""
        cache = LRUCache(default_ttl=300)
        cache.set("key", "value", ttl=1)
        
        # Should exist immediately
        assert cache.get("key") == "value"
        
        # Wait for expiry
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("key") is None


class TestLRUCacheDelete:
    """Test LRUCache delete operation"""
    
    def test_delete_existing_key(self):
        """delete should remove existing key"""
        cache = LRUCache()
        cache.set("key", "value")
        
        result = cache.delete("key")
        
        assert result is True
        assert cache.get("key") is None
    
    def test_delete_nonexistent_key(self):
        """delete should return False for nonexistent key"""
        cache = LRUCache()
        
        result = cache.delete("nonexistent")
        
        assert result is False


class TestLRUCacheSizeLimit:
    """Test LRUCache size limit"""
    
    def test_evicts_when_full(self):
        """Should evict LRU item when full"""
        cache = LRUCache(max_size=3)
        
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a"
        
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") == 4
    
    def test_access_updates_lru(self):
        """Accessing item should update LRU order"""
        cache = LRUCache(max_size=3)
        
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        
        # Access "a" to make it recent
        cache.get("a")
        
        # Add "d" - should evict "b" not "a"
        cache.set("d", 4)
        
        assert cache.get("a") == 1  # Still present
        assert cache.get("b") is None  # Evicted
        assert cache.get("c") == 3
        assert cache.get("d") == 4


class TestLRUCacheTTL:
    """Test LRUCache TTL behavior"""
    
    def test_expired_key_returns_none(self):
        """Expired key should return None"""
        cache = LRUCache(default_ttl=1)
        cache.set("key", "value")
        
        time.sleep(1.1)
        
        assert cache.get("key") is None
    
    def test_expired_key_increments_misses(self):
        """Accessing expired key should count as miss"""
        cache = LRUCache(default_ttl=1)
        cache.set("key", "value")
        
        cache.get("key")  # Hit
        time.sleep(1.1)
        cache.get("key")  # Miss (expired)
        
        assert cache._hits == 1
        assert cache._misses == 1
    
    def test_zero_ttl_no_expiry(self):
        """TTL of 0 should mean no expiration"""
        cache = LRUCache()
        cache.set("key", "value", ttl=0)
        
        # Key should be stored but not in expiry
        assert "key" not in cache._expiry or cache._expiry.get("key", 0) <= time.time()


class TestLRUCacheStatistics:
    """Test LRUCache hit/miss statistics"""
    
    def test_multiple_hits(self):
        """Should count multiple hits"""
        cache = LRUCache()
        cache.set("key", "value")
        
        cache.get("key")
        cache.get("key")
        cache.get("key")
        
        assert cache._hits == 3
    
    def test_multiple_misses(self):
        """Should count multiple misses"""
        cache = LRUCache()
        
        cache.get("a")
        cache.get("b")
        cache.get("c")
        
        assert cache._misses == 3
    
    def test_hit_rate_calculation(self):
        """Should be able to calculate hit rate"""
        cache = LRUCache()
        cache.set("exists", "value")
        
        cache.get("exists")  # hit
        cache.get("exists")  # hit
        cache.get("missing")  # miss
        cache.get("missing")  # miss
        
        total = cache._hits + cache._misses
        hit_rate = cache._hits / total if total > 0 else 0
        
        assert hit_rate == 0.5


class TestLRUCacheThreadSafety:
    """Test LRUCache thread safety"""
    
    def test_concurrent_access(self):
        """Cache should handle concurrent access"""
        cache = LRUCache(max_size=100)
        errors = []
        
        def writer():
            try:
                for i in range(100):
                    cache.set(f"key_{i}", i)
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                for i in range(100):
                    cache.get(f"key_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_key(self):
        """Should handle empty string key"""
        cache = LRUCache()
        cache.set("", "empty key value")
        assert cache.get("") == "empty key value"
    
    def test_none_value(self):
        """Should store None as value"""
        cache = LRUCache()
        cache.set("key", None)
        
        # Should return None (not default)
        assert cache.get("key", default="fallback") is None
    
    def test_large_value(self):
        """Should handle large values"""
        cache = LRUCache()
        large_value = "x" * 1000000  # 1MB string
        cache.set("large", large_value)
        assert cache.get("large") == large_value
    
    def test_special_characters_in_key(self):
        """Should handle special characters in key"""
        cache = LRUCache()
        cache.set("key:with:colons", "value1")
        cache.set("key/with/slashes", "value2")
        cache.set("key with spaces", "value3")
        
        assert cache.get("key:with:colons") == "value1"
        assert cache.get("key/with/slashes") == "value2"
        assert cache.get("key with spaces") == "value3"
    
    def test_small_max_size(self):
        """Should work with max_size of 1"""
        cache = LRUCache(max_size=1)
        
        cache.set("a", 1)
        assert cache.get("a") == 1
        
        cache.set("b", 2)
        assert cache.get("a") is None
        assert cache.get("b") == 2
