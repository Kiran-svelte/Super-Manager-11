"""
Super Manager - Core Module Tests
=================================

Tests for core modules: validation, cache, errors, monitoring
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


# =============================================================================
# Validation Tests
# =============================================================================

class TestInputValidation:
    """Tests for input validation module"""
    
    def test_sanitize_html_strips_scripts(self):
        """HTML sanitizer should remove script tags"""
        from core.validation import sanitize_html
        
        dirty = "<script>alert('xss')</script>Hello"
        clean = sanitize_html(dirty)
        
        assert "<script>" not in clean
        assert "Hello" in clean
    
    def test_sanitize_html_allows_safe_tags(self):
        """HTML sanitizer should allow safe HTML tags"""
        from core.validation import sanitize_html
        
        text = "<p>Hello <strong>World</strong></p>"
        clean = sanitize_html(text)
        
        # Should preserve or strip but not break
        assert "Hello" in clean
        assert "World" in clean
    
    def test_check_sql_injection_detects_attacks(self):
        """SQL injection detection should catch common patterns"""
        from core.validation import check_sql_injection
        
        attacks = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "UNION SELECT * FROM passwords",
            "'; DELETE FROM users WHERE '1'='1"
        ]
        
        for attack in attacks:
            assert check_sql_injection(attack) == True
    
    def test_check_sql_injection_allows_normal_text(self):
        """SQL injection detection should not block normal text"""
        from core.validation import check_sql_injection
        
        normal_texts = [
            "Hello, how are you?",
            "Please schedule a meeting for tomorrow",
            "I need to update my profile",
            "Let's drop by the office"
        ]
        
        for text in normal_texts:
            assert check_sql_injection(text) == False
    
    def test_validate_email_valid_addresses(self):
        """Email validation should accept valid addresses"""
        from core.validation import validate_email
        
        valid_emails = [
            "user@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk",
            "user123@test.io"
        ]
        
        for email in valid_emails:
            assert validate_email(email) == True
    
    def test_validate_email_invalid_addresses(self):
        """Email validation should reject invalid addresses"""
        from core.validation import validate_email
        
        invalid_emails = [
            "not-an-email",
            "@missing-local.com",
            "missing@.com",
            "spaces in@email.com",
            ""
        ]
        
        for email in invalid_emails:
            assert validate_email(email) == False


class TestChatRequestValidation:
    """Tests for ChatRequest pydantic model"""
    
    def test_valid_chat_request(self):
        """Valid chat request should pass validation"""
        from core.validation import ChatRequest
        
        request = ChatRequest(
            message="Hello, can you help me?",
            conversation_id="conv-123"
        )
        
        assert request.message == "Hello, can you help me?"
    
    def test_empty_message_rejected(self):
        """Empty message should be rejected"""
        from core.validation import ChatRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ChatRequest(message="")
    
    def test_message_too_long(self):
        """Message exceeding max length should be rejected"""
        from core.validation import ChatRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 50001)


# =============================================================================
# Cache Tests
# =============================================================================

class TestLRUCache:
    """Tests for in-memory LRU cache"""
    
    def test_basic_get_set(self):
        """Basic get/set operations should work"""
        from core.cache import LRUCache
        
        cache = LRUCache(max_size=100)
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
    
    def test_cache_miss_returns_default(self):
        """Cache miss should return default value"""
        from core.cache import LRUCache
        
        cache = LRUCache()
        
        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"
    
    def test_lru_eviction(self):
        """LRU eviction should work when cache is full"""
        from core.cache import LRUCache
        
        cache = LRUCache(max_size=3)
        
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a"
        
        assert cache.get("a") is None
        assert cache.get("d") == 4
    
    def test_ttl_expiration(self):
        """Expired items should not be returned"""
        from core.cache import LRUCache
        import time
        
        cache = LRUCache(default_ttl=1)  # 1 second TTL
        cache.set("key", "value")
        
        assert cache.get("key") == "value"
        
        time.sleep(1.1)
        
        assert cache.get("key") is None
    
    def test_cache_stats(self):
        """Cache should track hit/miss statistics"""
        from core.cache import LRUCache
        
        cache = LRUCache()
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert "hit_rate" in stats
    
    def test_cache_clear(self):
        """Cache clear should remove all entries"""
        from core.cache import LRUCache
        
        cache = LRUCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestMultiTierCache:
    """Tests for multi-tier cache"""
    
    def test_l1_cache_used_first(self):
        """L1 cache should be checked before L2"""
        from core.cache import MultiTierCache
        
        cache = MultiTierCache()
        cache.set("key", "value")
        
        # Should get from L1
        assert cache.get("key") == "value"
    
    def test_cache_deletion(self):
        """Delete should remove from both tiers"""
        from core.cache import MultiTierCache
        
        cache = MultiTierCache()
        cache.set("key", "value")
        cache.delete("key")
        
        assert cache.get("key") is None


class TestCacheDecorators:
    """Tests for cache decorators"""
    
    def test_cached_decorator_caches_result(self):
        """Cached decorator should cache function results"""
        from core.cache import cached, cache
        
        call_count = 0
        
        @cached(ttl=60, key_prefix="test")
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Clear cache first
        cache.l1.clear()
        call_count = 0
        
        result1 = expensive_function(5)
        result2 = expensive_function(5)
        
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestCustomExceptions:
    """Tests for custom exception classes"""
    
    def test_validation_error_structure(self):
        """ValidationError should have correct structure"""
        from core.errors import ValidationError
        
        error = ValidationError("Invalid input", field="email")
        
        assert error.error_code == "VALIDATION_ERROR"
        assert error.http_status == 400
        assert error.details["field"] == "email"
    
    def test_not_found_error(self):
        """NotFoundError should format correctly"""
        from core.errors import NotFoundError
        
        error = NotFoundError("User", "user-123")
        
        assert "User" in error.message
        assert "user-123" in error.message
        assert error.http_status == 404
    
    def test_rate_limit_error(self):
        """RateLimitError should include retry info"""
        from core.errors import RateLimitError
        
        error = RateLimitError(retry_after=60)
        
        assert error.http_status == 429
        assert error.details["retry_after_seconds"] == 60
    
    def test_error_to_dict(self):
        """Error to_dict should create API-safe response"""
        from core.errors import SuperManagerError
        
        error = SuperManagerError(
            message="Internal error details",
            user_message="Something went wrong"
        )
        
        response = error.to_dict()
        
        assert response["error"] == True
        assert response["message"] == "Something went wrong"
        assert "error_id" in response


class TestErrorTracker:
    """Tests for error tracking"""
    
    def test_track_error(self):
        """Error tracker should track errors"""
        from core.errors import ErrorTracker, SuperManagerError
        
        tracker = ErrorTracker()
        error = SuperManagerError("Test error")
        
        record = tracker.track(error)
        
        assert record.error_id == error.error_id
        assert record.message == "Test error"
    
    def test_error_stats(self):
        """Error tracker should provide statistics"""
        from core.errors import ErrorTracker, ValidationError
        
        tracker = ErrorTracker()
        
        # Track some errors
        for _ in range(5):
            tracker.track(ValidationError("Test"))
        
        stats = tracker.get_stats()
        
        assert stats["total_tracked"] >= 5
        assert "by_category" in stats
    
    def test_recent_errors(self):
        """Should retrieve recent errors"""
        from core.errors import ErrorTracker, SuperManagerError
        
        tracker = ErrorTracker()
        
        for i in range(10):
            tracker.track(SuperManagerError(f"Error {i}"))
        
        recent = tracker.get_recent_errors(limit=5)
        
        assert len(recent) <= 5


class TestErrorDecorators:
    """Tests for error handling decorators"""
    
    def test_handle_errors_catches_exceptions(self):
        """handle_errors decorator should catch exceptions"""
        from core.errors import handle_errors, SuperManagerError
        
        @handle_errors(reraise=False)
        def failing_function():
            raise ValueError("Something failed")
        
        # Should not raise
        result = failing_function()
        assert result is None
    
    def test_handle_errors_preserves_return_value(self):
        """handle_errors should preserve successful return values"""
        from core.errors import handle_errors
        
        @handle_errors()
        def successful_function():
            return "success"
        
        assert successful_function() == "success"


# =============================================================================
# Monitoring Tests
# =============================================================================

class TestMetricsCollector:
    """Tests for metrics collection"""
    
    def test_counter_increment(self):
        """Counter should increment correctly"""
        from core.monitoring import MetricsCollector
        
        metrics = MetricsCollector()
        
        metrics.counter_inc("test_counter")
        metrics.counter_inc("test_counter")
        metrics.counter_inc("test_counter", 5)
        
        value = metrics.get_counter("test_counter")
        assert value.get("", 0) == 7
    
    def test_gauge_set(self):
        """Gauge should set value correctly"""
        from core.monitoring import MetricsCollector
        
        metrics = MetricsCollector()
        
        metrics.gauge_set("test_gauge", 42)
        
        value = metrics.get_gauge("test_gauge")
        assert value.get("", 0) == 42
    
    def test_histogram_observation(self):
        """Histogram should record observations"""
        from core.monitoring import MetricsCollector
        
        metrics = MetricsCollector()
        
        for i in range(10):
            metrics.histogram_observe("response_time", i * 10)
        
        stats = metrics.get_histogram_stats("response_time")
        
        assert "" in stats
        assert stats[""]["count"] == 10


class TestHealthChecker:
    """Tests for health check system"""
    
    @pytest.mark.asyncio
    async def test_register_health_check(self):
        """Should register and run health checks"""
        from core.monitoring import HealthChecker
        
        checker = HealthChecker()
        
        def simple_check():
            return True
        
        checker.register("simple", simple_check)
        
        result = await checker.check_component("simple")
        
        assert result.status.value == "healthy"
    
    @pytest.mark.asyncio
    async def test_failing_health_check(self):
        """Failing health check should report unhealthy"""
        from core.monitoring import HealthChecker
        
        checker = HealthChecker()
        
        def failing_check():
            raise Exception("Service down")
        
        checker.register("failing", failing_check)
        
        result = await checker.check_component("failing")
        
        assert result.status.value == "unhealthy"
    
    def test_overall_status_aggregation(self):
        """Overall status should aggregate component statuses"""
        from core.monitoring import HealthChecker
        
        checker = HealthChecker()
        
        checker.register("healthy1", lambda: True)
        checker.register("healthy2", lambda: True)
        
        status = checker.get_overall_status()
        
        assert "status" in status
        assert "components" in status
