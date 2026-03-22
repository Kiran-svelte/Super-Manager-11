"""
Behavioral Tests: AI Provider & Circuit Breaker
================================================
Tests that the AI provider system ACTUALLY:
- Implements circuit breaker pattern
- Transitions between CLOSED, OPEN, HALF_OPEN states
- Blocks requests when OPEN
- Recovers after timeout
- Tracks failure/success counts

README Requirements:
- Circuit breaker: 5 failures → 30s cooldown
- AI Provider failover with circuit breaker
- Multiple provider support (Groq, OpenAI, Gemini, SambaNova)
"""

import pytest
import time
from unittest.mock import Mock, patch
import threading

from backend.core.performance import (
    CircuitBreaker, 
    CircuitState, 
    CircuitBreakerConfig,
    CircuitBreakerMetrics
)


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions"""
    
    def test_initial_state_is_closed(self):
        """Circuit should start CLOSED"""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
    
    def test_state_remains_closed_under_threshold(self):
        """Circuit should stay CLOSED with failures under threshold"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=5))
        
        # Record 4 failures (under threshold of 5)
        for _ in range(4):
            cb.record_failure()
        
        assert cb.state == CircuitState.CLOSED
    
    def test_state_opens_at_threshold(self):
        """Circuit should OPEN when failures reach threshold"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=5))
        
        # Record exactly 5 failures
        for _ in range(5):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
    
    def test_state_opens_above_threshold(self):
        """Circuit should definitely be OPEN above threshold"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        
        for _ in range(10):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerCanExecute:
    """Test can_execute behavior"""
    
    def test_can_execute_when_closed(self):
        """Should allow execution when CLOSED"""
        cb = CircuitBreaker("test")
        assert cb.can_execute() is True
    
    def test_cannot_execute_when_open(self):
        """Should reject execution when OPEN"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout=60.0  # Long timeout so it stays open
        ))
        
        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Should reject
        assert cb.can_execute() is False
    
    def test_limited_execution_when_half_open(self):
        """Should allow limited calls when HALF_OPEN"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.01,  # Very short timeout for testing
            half_open_max_calls=3
        ))
        
        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        
        # Wait for timeout to transition to HALF_OPEN
        time.sleep(0.02)
        
        assert cb.state == CircuitState.HALF_OPEN
        
        # Should allow up to half_open_max_calls
        assert cb.can_execute() is True
        assert cb.can_execute() is True
        assert cb.can_execute() is True
        # Fourth call should be rejected
        assert cb.can_execute() is False


class TestCircuitBreakerRecovery:
    """Test circuit breaker recovery"""
    
    def test_recovers_after_timeout(self):
        """Should transition to HALF_OPEN after timeout"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.01  # Very short timeout
        ))
        
        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb._state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(0.02)
        
        # Accessing state should trigger transition
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_closes_after_successful_recovery(self):
        """Should close after success_threshold successes in HALF_OPEN"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.01
        ))
        
        # Open and wait for half-open
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Record successes
        cb.record_success()
        cb.record_success()
        
        assert cb.state == CircuitState.CLOSED
    
    def test_reopens_on_failure_during_half_open(self):
        """Should reopen if failure during HALF_OPEN"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.01
        ))
        
        # Open and wait for half-open
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Fail during half-open
        cb.record_failure()
        
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerDefaultConfig:
    """Test default configuration matches README"""
    
    def test_default_failure_threshold(self):
        """Default failure threshold should be 5 (README: 5 failures)"""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
    
    def test_default_timeout(self):
        """Default timeout should be 30 seconds (README: 30s cooldown)"""
        config = CircuitBreakerConfig()
        assert config.timeout == 30.0
    
    def test_default_success_threshold(self):
        """Default success threshold should be 3"""
        config = CircuitBreakerConfig()
        assert config.success_threshold == 3


class TestCircuitBreakerMetrics:
    """Test circuit breaker metrics tracking"""
    
    def test_metrics_track_successes(self):
        """Should track successful calls"""
        metrics = CircuitBreakerMetrics()
        
        metrics.record_success()
        metrics.record_success()
        
        assert metrics.successful_calls == 2
        assert metrics.total_calls == 2
    
    def test_metrics_track_failures(self):
        """Should track failed calls"""
        metrics = CircuitBreakerMetrics()
        
        metrics.record_failure()
        metrics.record_failure()
        metrics.record_failure()
        
        assert metrics.failed_calls == 3
        assert metrics.total_calls == 3
    
    def test_metrics_track_rejected(self):
        """Should track rejected calls"""
        metrics = CircuitBreakerMetrics()
        
        metrics.record_rejected()
        
        assert metrics.rejected_calls == 1
    
    def test_metrics_last_failure_time(self):
        """Should track last failure time"""
        metrics = CircuitBreakerMetrics()
        
        assert metrics.last_failure_time is None
        
        metrics.record_failure()
        
        assert metrics.last_failure_time is not None
    
    def test_metrics_summary(self):
        """Should provide summary with success rate"""
        metrics = CircuitBreakerMetrics()
        
        metrics.record_success()
        metrics.record_success()
        metrics.record_failure()
        
        summary = metrics.get_summary()
        
        assert summary["total_calls"] == 3
        assert summary["successful_calls"] == 2
        assert summary["failed_calls"] == 1
        assert "success_rate" in summary


class TestCircuitBreakerStatus:
    """Test circuit breaker status reporting"""
    
    def test_get_status(self):
        """get_status should return all relevant info"""
        cb = CircuitBreaker("test-circuit")
        
        status = cb.get_status()
        
        assert status["name"] == "test-circuit"
        assert status["state"] == "closed"
        assert "failure_count" in status
        assert "success_count" in status
        assert "metrics" in status


class TestCircuitBreakerThreadSafety:
    """Test circuit breaker is thread-safe"""
    
    def test_concurrent_failures(self):
        """Circuit should handle concurrent failures correctly"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=100))
        
        def record_failures():
            for _ in range(20):
                cb.record_failure()
        
        threads = [threading.Thread(target=record_failures) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have recorded all 100 failures
        assert cb._failure_count == 100


class TestCircuitBreakerIntegration:
    """Test circuit breaker in typical scenarios"""
    
    def test_api_failure_scenario(self):
        """Simulate API failures causing circuit to open"""
        cb = CircuitBreaker("ai-provider", CircuitBreakerConfig(
            failure_threshold=5,
            timeout=0.05
        ))
        
        # Normal operation
        assert cb.can_execute() is True
        cb.record_success()
        
        # API starts failing
        for _ in range(5):
            if cb.can_execute():
                cb.record_failure()
        
        # Circuit should be open
        assert cb.state == CircuitState.OPEN
        
        # New requests should be rejected
        assert cb.can_execute() is False
        
        # Wait for recovery
        time.sleep(0.06)
        
        # Should be half-open now
        assert cb.state == CircuitState.HALF_OPEN
        
        # Test request succeeds
        cb.record_success()
        cb.record_success()
        cb.record_success()
        
        # Circuit should be closed
        assert cb.state == CircuitState.CLOSED
    
    def test_rapid_failure_recovery_cycle(self):
        """Test multiple open/close cycles"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=1,
            timeout=0.01
        ))
        
        for cycle in range(3):
            # Open circuit
            cb.record_failure()
            cb.record_failure()
            assert cb.state == CircuitState.OPEN
            
            # Wait and recover
            time.sleep(0.02)
            assert cb.state == CircuitState.HALF_OPEN
            
            cb.record_success()
            assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerSuccessReducesFailureCount:
    """Test that successes reduce failure count"""
    
    def test_success_decrements_failure_count(self):
        """Success in CLOSED state should decrement failure count"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=5))
        
        # Record some failures
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb._failure_count == 3
        
        # Success should reduce count
        cb.record_success()
        assert cb._failure_count == 2
        
        cb.record_success()
        assert cb._failure_count == 1
        
        cb.record_success()
        assert cb._failure_count == 0
        
        # Can't go below 0
        cb.record_success()
        assert cb._failure_count == 0
