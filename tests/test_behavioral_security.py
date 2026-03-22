"""
Behavioral Tests: Security Module
===================================
Tests that the security module ACTUALLY works:
- IPRateLimitConfig dataclass
- IPRateLimiter class
- Request ID generation

README Requirements:
- Security Headers (CSP, HSTS, X-Frame-Options)
- Request Rate Limiting per IP
- Request ID Generation
"""

import pytest
import time
import threading

from backend.core.security import (
    IPRateLimitConfig,
    IPRateLimiter,
)


class TestIPRateLimitConfig:
    """Test IPRateLimitConfig dataclass"""
    
    def test_can_create(self):
        """IPRateLimitConfig should be creatable"""
        config = IPRateLimitConfig()
        assert config is not None
    
    def test_default_requests_per_minute(self):
        """Default requests_per_minute should be 60"""
        config = IPRateLimitConfig()
        assert config.requests_per_minute == 60
    
    def test_default_requests_per_hour(self):
        """Default requests_per_hour should be 1000"""
        config = IPRateLimitConfig()
        assert config.requests_per_hour == 1000
    
    def test_default_block_duration(self):
        """Default block_duration_minutes should be 15"""
        config = IPRateLimitConfig()
        assert config.block_duration_minutes == 15
    
    def test_default_whitelist_empty(self):
        """Default whitelist should be empty set"""
        config = IPRateLimitConfig()
        assert isinstance(config.whitelist, set)
        assert len(config.whitelist) == 0
    
    def test_custom_values(self):
        """Should accept custom values"""
        config = IPRateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=2000,
            block_duration_minutes=30,
            whitelist={"127.0.0.1", "10.0.0.1"}
        )
        assert config.requests_per_minute == 100
        assert config.requests_per_hour == 2000
        assert config.block_duration_minutes == 30
        assert "127.0.0.1" in config.whitelist


class TestIPRateLimiterInit:
    """Test IPRateLimiter initialization"""
    
    def test_can_instantiate(self):
        """IPRateLimiter should be instantiatable"""
        limiter = IPRateLimiter()
        assert limiter is not None
    
    def test_default_config(self):
        """Should have default config"""
        limiter = IPRateLimiter()
        assert limiter.config is not None
        assert isinstance(limiter.config, IPRateLimitConfig)
    
    def test_custom_config(self):
        """Should accept custom config"""
        config = IPRateLimitConfig(requests_per_minute=10)
        limiter = IPRateLimiter(config=config)
        assert limiter.config.requests_per_minute == 10
    
    def test_shorthand_requests_per_minute(self):
        """Should accept requests_per_minute directly"""
        limiter = IPRateLimiter(requests_per_minute=30)
        assert limiter.config.requests_per_minute == 30
    
    def test_has_minute_counts(self):
        """Should have _minute_counts dict"""
        limiter = IPRateLimiter()
        assert hasattr(limiter, "_minute_counts")
    
    def test_has_hour_counts(self):
        """Should have _hour_counts dict"""
        limiter = IPRateLimiter()
        assert hasattr(limiter, "_hour_counts")
    
    def test_has_blocked_ips(self):
        """Should have _blocked_ips dict"""
        limiter = IPRateLimiter()
        assert hasattr(limiter, "_blocked_ips")
    
    def test_has_lock(self):
        """Should have thread lock"""
        limiter = IPRateLimiter()
        assert hasattr(limiter, "_lock")


class TestIPRateLimiterIsBlocked:
    """Test IPRateLimiter is_blocked method"""
    
    def test_new_ip_not_blocked(self):
        """New IP should not be blocked"""
        limiter = IPRateLimiter()
        assert limiter.is_blocked("192.168.1.1") is False
    
    def test_whitelisted_ip_not_blocked(self):
        """Whitelisted IP should never be blocked"""
        config = IPRateLimitConfig(whitelist={"10.0.0.1"})
        limiter = IPRateLimiter(config=config)
        
        # Even if we manually block it
        limiter._blocked_ips["10.0.0.1"] = time.time() + 3600
        
        assert limiter.is_blocked("10.0.0.1") is False
    
    def test_blocked_ip_detected(self):
        """Blocked IP should be detected"""
        limiter = IPRateLimiter()
        
        # Manually block an IP
        limiter._blocked_ips["1.2.3.4"] = time.time() + 3600
        
        assert limiter.is_blocked("1.2.3.4") is True
    
    def test_expired_block_cleared(self):
        """Expired block should be cleared"""
        limiter = IPRateLimiter()
        
        # Block in the past
        limiter._blocked_ips["1.2.3.4"] = time.time() - 1
        
        assert limiter.is_blocked("1.2.3.4") is False


class TestIPRateLimiterCheckAndRecord:
    """Test IPRateLimiter check_and_record method"""
    
    def test_first_request_allowed(self):
        """First request should be allowed"""
        limiter = IPRateLimiter()
        
        allowed, reason = limiter.check_and_record("192.168.1.1")
        
        assert allowed is True
        assert reason is None
    
    def test_under_limit_allowed(self):
        """Requests under limit should be allowed"""
        limiter = IPRateLimiter(requests_per_minute=10)
        
        for _ in range(5):
            allowed, _ = limiter.check_and_record("192.168.1.1")
            assert allowed is True
    
    def test_over_limit_blocked(self):
        """Requests over limit should be blocked"""
        limiter = IPRateLimiter(requests_per_minute=5)
        
        for _ in range(5):
            limiter.check_and_record("192.168.1.1")
        
        # 6th request should be blocked
        allowed, reason = limiter.check_and_record("192.168.1.1")
        
        assert allowed is False
        assert reason is not None
    
    def test_different_ips_separate_limits(self):
        """Different IPs should have separate limits"""
        limiter = IPRateLimiter(requests_per_minute=3)
        
        # Use up IP1's quota
        for _ in range(3):
            limiter.check_and_record("192.168.1.1")
        
        # IP2 should still be allowed
        allowed, _ = limiter.check_and_record("192.168.1.2")
        assert allowed is True


class TestIPRateLimiterCleanOldEntries:
    """Test IPRateLimiter cleanup of old entries"""
    
    def test_has_clean_method(self):
        """Should have _clean_old_entries method"""
        limiter = IPRateLimiter()
        assert hasattr(limiter, "_clean_old_entries")
        assert callable(limiter._clean_old_entries)
    
    def test_clean_removes_old_entries(self):
        """Should remove entries older than window"""
        limiter = IPRateLimiter()
        
        # Add old entry
        ip = "192.168.1.1"
        now = time.time()
        limiter._minute_counts[ip] = [now - 120, now - 90, now - 30, now]
        
        limiter._clean_old_entries(ip, now)
        
        # Only entries from last 60 seconds should remain
        assert len(limiter._minute_counts[ip]) == 2


class TestIPRateLimiterThreadSafety:
    """Test IPRateLimiter thread safety"""
    
    def test_concurrent_check_and_record(self):
        """Should handle concurrent requests safely"""
        limiter = IPRateLimiter(requests_per_minute=1000)
        errors = []
        
        def make_requests():
            try:
                for _ in range(100):
                    limiter.check_and_record("192.168.1.1")
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=make_requests) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestWhitelistBehavior:
    """Test whitelist behavior"""
    
    def test_whitelisted_always_allowed(self):
        """Whitelisted IPs should always be allowed"""
        config = IPRateLimitConfig(
            requests_per_minute=2,
            whitelist={"127.0.0.1"}
        )
        limiter = IPRateLimiter(config=config)
        
        # Make many requests
        for _ in range(100):
            allowed, _ = limiter.check_and_record("127.0.0.1")
            assert allowed is True
    
    def test_non_whitelisted_can_be_blocked(self):
        """Non-whitelisted IPs can be rate limited"""
        config = IPRateLimitConfig(
            requests_per_minute=3,
            whitelist={"127.0.0.1"}
        )
        limiter = IPRateLimiter(config=config)
        
        # Use up quota for non-whitelisted IP
        for _ in range(3):
            limiter.check_and_record("1.2.3.4")
        
        allowed, _ = limiter.check_and_record("1.2.3.4")
        assert allowed is False


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_ip(self):
        """Should handle empty IP string"""
        limiter = IPRateLimiter()
        allowed, _ = limiter.check_and_record("")
        # Should not crash
        assert isinstance(allowed, bool)
    
    def test_ipv6_address(self):
        """Should handle IPv6 addresses"""
        limiter = IPRateLimiter()
        allowed, _ = limiter.check_and_record("::1")
        assert allowed is True
    
    def test_very_high_limit(self):
        """Should handle high limits"""
        limiter = IPRateLimiter(requests_per_minute=1000000)
        
        for _ in range(100):
            allowed, _ = limiter.check_and_record("192.168.1.1")
            assert allowed is True
    
    def test_very_low_limit(self):
        """Should handle limit of 1"""
        limiter = IPRateLimiter(requests_per_minute=1)
        
        allowed1, _ = limiter.check_and_record("192.168.1.1")
        allowed2, _ = limiter.check_and_record("192.168.1.1")
        
        assert allowed1 is True
        assert allowed2 is False
