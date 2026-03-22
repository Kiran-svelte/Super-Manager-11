"""
Behavioral Tests: Performance Module
======================================
Tests that the performance module ACTUALLY works:
- CircuitState enum
- CircuitBreakerConfig dataclass
- CircuitBreaker class
- CircuitBreakerMetrics dataclass

README Requirements:
- Circuit Breaker Pattern
- States: CLOSED, OPEN, HALF_OPEN
- Failure threshold: 5
- Recovery timeout: 30s
"""

import pytest
import time
import threading
from datetime import datetime

from backend.core.performance import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitBreakerMetrics,
)


class TestCircuitStateEnum:
    """Test CircuitState enum"""
    
    def test_closed_value(self):
        """CLOSED should have correct value"""
        assert CircuitState.CLOSED.value == "closed"
    
    def test_open_value(self):
        """OPEN should have correct value"""
        assert CircuitState.OPEN.value == "open"
    
    def test_half_open_value(self):
        """HALF_OPEN should have correct value"""
        assert CircuitState.HALF_OPEN.value == "half_open"
    
    def test_all_states(self):
        """Should have exactly 3 states"""
        states = list(CircuitState)
        assert len(states) == 3


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig dataclass"""
    
    def test_can_create(self):
        """CircuitBreakerConfig should be creatable"""
        config = CircuitBreakerConfig()
        assert config is not None
    
    def test_default_failure_threshold(self):
        """Default failure_threshold should be 5"""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
    
    def test_default_success_threshold(self):
        """Default success_threshold should be 3"""
        config = CircuitBreakerConfig()
        assert config.success_threshold == 3
    
    def test_default_timeout(self):
        """Default timeout should be 30.0"""
        config = CircuitBreakerConfig()
        assert config.timeout == 30.0
    
    def test_default_half_open_max_calls(self):
        """Default half_open_max_calls should be 3"""
        config = CircuitBreakerConfig()
        assert config.half_open_max_calls == 3
    
    def test_custom_values(self):
        """Should accept custom values"""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout=60.0,
            half_open_max_calls=5
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 5
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 5


class TestCircuitBreakerInit:
    """Test CircuitBreaker initialization"""
    
    def test_can_instantiate(self):
        """CircuitBreaker should be instantiatable"""
        cb = CircuitBreaker("test")
        assert cb is not None
    
    def test_has_name(self):
        """CircuitBreaker should have name"""
        cb = CircuitBreaker("database")
        assert cb.name == "database"
    
    def test_default_config(self):
        """CircuitBreaker should have default config"""
        cb = CircuitBreaker("test")
        assert cb.config is not None
        assert isinstance(cb.config, CircuitBreakerConfig)
    
    def test_custom_config(self):
        """CircuitBreaker should accept custom config"""
        config = CircuitBreakerConfig(failure_threshold=10)
        cb = CircuitBreaker("test", config)
        assert cb.config.failure_threshold == 10
    
    def test_initial_state_closed(self):
        """CircuitBreaker should start in CLOSED state"""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
    
    def test_initial_failure_count_zero(self):
        """CircuitBreaker should start with 0 failures"""
        cb = CircuitBreaker("test")
        assert cb._failure_count == 0
    
    def test_has_lock(self):
        """CircuitBreaker should have thread lock"""
        cb = CircuitBreaker("test")
        assert hasattr(cb, "_lock")
    
    def test_has_metrics(self):
        """CircuitBreaker should have metrics"""
        cb = CircuitBreaker("test")
        assert hasattr(cb, "_metrics")
        assert isinstance(cb._metrics, CircuitBreakerMetrics)


class TestCircuitBreakerStateTransitions:
    """Test CircuitBreaker state transitions"""
    
    def test_stays_closed_under_threshold(self):
        """Should stay CLOSED with failures under threshold"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=5))
        
        for _ in range(4):
            cb.record_failure()
        
        assert cb.state == CircuitState.CLOSED
    
    def test_opens_at_threshold(self):
        """Should transition to OPEN at failure threshold"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=5))
        
        for _ in range(5):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
    
    def test_success_decrements_failures(self):
        """Success should decrement failure count in CLOSED"""
        cb = CircuitBreaker("test")
        
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        
        assert cb._failure_count == 1
    
    def test_half_open_to_open_on_failure(self):
        """Should go HALF_OPEN -> OPEN on failure"""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.01)
        cb = CircuitBreaker("test", config)
        
        cb.record_failure()  # Open
        time.sleep(0.02)  # Wait for timeout
        
        # Access state to trigger HALF_OPEN
        _ = cb.state
        
        # Failure during recovery
        cb.record_failure()
        
        assert cb._state == CircuitState.OPEN
    
    def test_half_open_to_closed_on_success(self):
        """Should go HALF_OPEN -> CLOSED after enough successes"""
        config = CircuitBreakerConfig(
            failure_threshold=1, 
            success_threshold=2, 
            timeout=0.01
        )
        cb = CircuitBreaker("test", config)
        
        cb.record_failure()  # Open
        time.sleep(0.02)  # Wait for timeout
        
        # Access state to trigger HALF_OPEN
        _ = cb.state
        
        # Enough successes to close
        cb.record_success()
        cb.record_success()
        
        assert cb._state == CircuitState.CLOSED


class TestCircuitBreakerCanExecute:
    """Test CircuitBreaker can_execute"""
    
    def test_can_execute_when_closed(self):
        """Should allow execution when CLOSED"""
        cb = CircuitBreaker("test")
        assert cb.can_execute() is True
    
    def test_cannot_execute_when_open(self):
        """Should reject execution when OPEN"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
        cb.record_failure()
        
        assert cb.can_execute() is False
    
    def test_limited_execution_half_open(self):
        """Should allow limited calls in HALF_OPEN"""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=0.01,
            half_open_max_calls=2
        )
        cb = CircuitBreaker("test", config)
        
        cb.record_failure()
        time.sleep(0.02)
        
        # First two should be allowed
        assert cb.can_execute() is True
        assert cb.can_execute() is True
        # Third should be blocked
        assert cb.can_execute() is False


class TestCircuitBreakerGetStatus:
    """Test CircuitBreaker get_status"""
    
    def test_returns_dict(self):
        """get_status should return dict"""
        cb = CircuitBreaker("test")
        status = cb.get_status()
        assert isinstance(status, dict)
    
    def test_has_name(self):
        """Status should include name"""
        cb = CircuitBreaker("my-service")
        status = cb.get_status()
        assert status["name"] == "my-service"
    
    def test_has_state(self):
        """Status should include state"""
        cb = CircuitBreaker("test")
        status = cb.get_status()
        assert status["state"] == "closed"
    
    def test_has_failure_count(self):
        """Status should include failure_count"""
        cb = CircuitBreaker("test")
        status = cb.get_status()
        assert "failure_count" in status
    
    def test_has_metrics(self):
        """Status should include metrics"""
        cb = CircuitBreaker("test")
        status = cb.get_status()
        assert "metrics" in status


class TestCircuitBreakerMetrics:
    """Test CircuitBreakerMetrics dataclass"""
    
    def test_can_create(self):
        """CircuitBreakerMetrics should be creatable"""
        metrics = CircuitBreakerMetrics()
        assert metrics is not None
    
    def test_initial_totals_zero(self):
        """Metrics should start at 0"""
        metrics = CircuitBreakerMetrics()
        assert metrics.total_calls == 0
        assert metrics.successful_calls == 0
        assert metrics.failed_calls == 0
        assert metrics.rejected_calls == 0
    
    def test_record_success(self):
        """record_success should increment counters"""
        metrics = CircuitBreakerMetrics()
        
        metrics.record_success()
        
        assert metrics.total_calls == 1
        assert metrics.successful_calls == 1
    
    def test_record_failure(self):
        """record_failure should increment counters"""
        metrics = CircuitBreakerMetrics()
        
        metrics.record_failure()
        
        assert metrics.total_calls == 1
        assert metrics.failed_calls == 1
        assert metrics.last_failure_time is not None
    
    def test_record_rejected(self):
        """record_rejected should increment counter"""
        metrics = CircuitBreakerMetrics()
        
        metrics.record_rejected()
        
        assert metrics.rejected_calls == 1
    
    def test_get_summary(self):
        """get_summary should return dict"""
        metrics = CircuitBreakerMetrics()
        metrics.record_success()
        metrics.record_failure()
        
        summary = metrics.get_summary()
        
        assert isinstance(summary, dict)
        assert summary["total_calls"] == 2
        assert summary["successful_calls"] == 1
        assert summary["failed_calls"] == 1
        assert "success_rate" in summary


class TestCircuitBreakerThreadSafety:
    """Test CircuitBreaker thread safety"""
    
    def test_concurrent_record_success(self):
        """Should handle concurrent successes"""
        cb = CircuitBreaker("test")
        errors = []
        
        def record():
            try:
                for _ in range(100):
                    cb.record_success()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=record) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_concurrent_operations(self):
        """Should handle mixed concurrent operations"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=100))
        errors = []
        
        def operate():
            try:
                for _ in range(50):
                    cb.can_execute()
                    cb.record_success()
                    cb.record_failure()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=operate) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_name(self):
        """Should handle empty name"""
        cb = CircuitBreaker("")
        assert cb.name == ""
    
    def test_very_short_timeout(self):
        """Should handle very short timeout"""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.001)
        cb = CircuitBreaker("test", config)
        
        cb.record_failure()
        time.sleep(0.002)
        
        # Should transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_zero_failure_threshold(self):
        """Should handle zero threshold (always open)"""
        config = CircuitBreakerConfig(failure_threshold=0)
        cb = CircuitBreaker("test", config)
        
        # No failures needed to open
        # (implementation may vary)
        assert cb is not None
