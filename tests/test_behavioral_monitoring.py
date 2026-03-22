"""
Behavioral Tests: Monitoring System
=====================================
Tests that the monitoring system ACTUALLY works:
- HealthStatus enum
- ComponentHealth dataclass
- HealthChecker class

README Requirements:
- Health checks for all components
- Status: healthy, degraded, unhealthy, unknown
- Parallel health checks
- History tracking
"""

import pytest
from datetime import datetime
from collections import deque

from backend.core.monitoring import (
    HealthStatus,
    ComponentHealth,
    HealthChecker,
)


class TestHealthStatusEnum:
    """Test HealthStatus enum"""
    
    def test_healthy_value(self):
        """HEALTHY should have correct value"""
        assert HealthStatus.HEALTHY == "healthy"
    
    def test_degraded_value(self):
        """DEGRADED should have correct value"""
        assert HealthStatus.DEGRADED == "degraded"
    
    def test_unhealthy_value(self):
        """UNHEALTHY should have correct value"""
        assert HealthStatus.UNHEALTHY == "unhealthy"
    
    def test_unknown_value(self):
        """UNKNOWN should have correct value"""
        assert HealthStatus.UNKNOWN == "unknown"
    
    def test_all_statuses(self):
        """Should have exactly 4 statuses"""
        statuses = list(HealthStatus)
        assert len(statuses) == 4
    
    def test_is_string_enum(self):
        """HealthStatus should be string comparable"""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.HEALTHY.value == "healthy"


class TestComponentHealth:
    """Test ComponentHealth dataclass"""
    
    def test_can_create_component_health(self):
        """ComponentHealth should be creatable"""
        health = ComponentHealth(name="database", status=HealthStatus.HEALTHY)
        assert health is not None
    
    def test_has_name(self):
        """ComponentHealth should have name"""
        health = ComponentHealth(name="redis", status=HealthStatus.HEALTHY)
        assert health.name == "redis"
    
    def test_has_status(self):
        """ComponentHealth should have status"""
        health = ComponentHealth(name="api", status=HealthStatus.DEGRADED)
        assert health.status == HealthStatus.DEGRADED
    
    def test_default_message(self):
        """ComponentHealth should have default empty message"""
        health = ComponentHealth(name="test", status=HealthStatus.HEALTHY)
        assert health.message == ""
    
    def test_custom_message(self):
        """ComponentHealth should accept custom message"""
        health = ComponentHealth(
            name="test", 
            status=HealthStatus.UNHEALTHY,
            message="Connection refused"
        )
        assert health.message == "Connection refused"
    
    def test_default_response_time(self):
        """ComponentHealth should have default response_time_ms"""
        health = ComponentHealth(name="test", status=HealthStatus.HEALTHY)
        assert health.response_time_ms == 0
    
    def test_custom_response_time(self):
        """ComponentHealth should accept custom response_time_ms"""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            response_time_ms=45.5
        )
        assert health.response_time_ms == 45.5
    
    def test_has_last_check(self):
        """ComponentHealth should have last_check"""
        health = ComponentHealth(name="test", status=HealthStatus.HEALTHY)
        assert hasattr(health, "last_check")
        assert isinstance(health.last_check, datetime)
    
    def test_default_metadata(self):
        """ComponentHealth should have default empty metadata"""
        health = ComponentHealth(name="test", status=HealthStatus.HEALTHY)
        assert health.metadata == {}
    
    def test_custom_metadata(self):
        """ComponentHealth should accept custom metadata"""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            metadata={"version": "1.0", "connections": 5}
        )
        assert health.metadata["version"] == "1.0"
        assert health.metadata["connections"] == 5
    
    def test_default_consecutive_failures(self):
        """ComponentHealth should have default consecutive_failures"""
        health = ComponentHealth(name="test", status=HealthStatus.HEALTHY)
        assert health.consecutive_failures == 0
    
    def test_custom_consecutive_failures(self):
        """ComponentHealth should accept custom consecutive_failures"""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.UNHEALTHY,
            consecutive_failures=5
        )
        assert health.consecutive_failures == 5


class TestHealthCheckerInit:
    """Test HealthChecker initialization"""
    
    def test_can_instantiate(self):
        """HealthChecker should be instantiatable"""
        checker = HealthChecker()
        assert checker is not None
    
    def test_default_check_interval(self):
        """HealthChecker should have default check_interval"""
        checker = HealthChecker()
        assert checker.check_interval == 30
    
    def test_custom_check_interval(self):
        """HealthChecker should accept custom check_interval"""
        checker = HealthChecker(check_interval=60)
        assert checker.check_interval == 60
    
    def test_has_checks_dict(self):
        """HealthChecker should have _checks dict"""
        checker = HealthChecker()
        assert hasattr(checker, "_checks")
        assert isinstance(checker._checks, dict)
    
    def test_has_status_dict(self):
        """HealthChecker should have _status dict"""
        checker = HealthChecker()
        assert hasattr(checker, "_status")
        assert isinstance(checker._status, dict)
    
    def test_has_history_dict(self):
        """HealthChecker should have _history dict"""
        checker = HealthChecker()
        assert hasattr(checker, "_history")
        assert isinstance(checker._history, dict)
    
    def test_has_lock(self):
        """HealthChecker should have thread lock"""
        import threading
        checker = HealthChecker()
        assert hasattr(checker, "_lock")
        assert isinstance(checker._lock, type(threading.Lock()))
    
    def test_running_initially_false(self):
        """HealthChecker should not be running initially"""
        checker = HealthChecker()
        assert checker._running is False


class TestHealthCheckerRegister:
    """Test HealthChecker registration"""
    
    def test_register_check(self):
        """register should add check function"""
        checker = HealthChecker()
        
        def db_check():
            return True
        
        checker.register("database", db_check)
        
        assert "database" in checker._checks
    
    def test_register_stores_function(self):
        """register should store check function"""
        checker = HealthChecker()
        
        def my_check():
            return True
        
        checker.register("test", my_check)
        
        assert checker._checks["test"]["func"] is my_check
    
    def test_register_stores_critical_flag(self):
        """register should store critical flag"""
        checker = HealthChecker()
        
        checker.register("database", lambda: True, critical=True)
        
        assert checker._checks["database"]["critical"] is True
    
    def test_register_creates_status(self):
        """register should create initial status"""
        checker = HealthChecker()
        
        checker.register("redis", lambda: True)
        
        assert "redis" in checker._status
        assert checker._status["redis"].status == HealthStatus.UNKNOWN
    
    def test_register_creates_history(self):
        """register should create history deque"""
        checker = HealthChecker()
        
        checker.register("api", lambda: True)
        
        assert "api" in checker._history
        assert isinstance(checker._history["api"], deque)
    
    def test_history_maxlen(self):
        """history should have maxlen of 100"""
        checker = HealthChecker()
        
        checker.register("test", lambda: True)
        
        assert checker._history["test"].maxlen == 100
    
    def test_register_multiple(self):
        """Should register multiple checks"""
        checker = HealthChecker()
        
        checker.register("db", lambda: True)
        checker.register("redis", lambda: True)
        checker.register("api", lambda: True)
        
        assert len(checker._checks) == 3


class TestHealthCheckerCheck:
    """Test HealthChecker check_component"""
    
    @pytest.mark.asyncio
    async def test_check_unregistered_component(self):
        """check_component should handle unregistered component"""
        checker = HealthChecker()
        
        result = await checker.check_component("nonexistent")
        
        assert result.status == HealthStatus.UNKNOWN
        assert result.message == "Not registered"
    
    @pytest.mark.asyncio
    async def test_check_sync_function(self):
        """check_component should work with sync functions"""
        checker = HealthChecker()
        checker.register("sync_check", lambda: {"status": "ok"})
        
        result = await checker.check_component("sync_check")
        
        # Should not raise
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_check_async_function(self):
        """check_component should work with async functions"""
        checker = HealthChecker()
        
        async def async_check():
            return {"status": "ok"}
        
        checker.register("async_check", async_check)
        
        result = await checker.check_component("async_check")
        
        # Should not raise
        assert result is not None


class TestHealthStatusUsage:
    """Test HealthStatus practical usage"""
    
    def test_compare_with_string(self):
        """HealthStatus should compare with string"""
        status = HealthStatus.HEALTHY
        assert status == "healthy"
    
    def test_use_in_dict(self):
        """HealthStatus should work as dict value"""
        data = {"status": HealthStatus.HEALTHY}
        assert data["status"] == "healthy"
    
    def test_json_serializable(self):
        """HealthStatus value should be JSON serializable"""
        import json
        
        status = HealthStatus.DEGRADED
        result = json.dumps({"status": status.value})
        
        assert '"status": "degraded"' in result


class TestComponentHealthFields:
    """Test ComponentHealth with various field combinations"""
    
    def test_all_fields(self):
        """ComponentHealth should accept all fields"""
        health = ComponentHealth(
            name="full-test",
            status=HealthStatus.HEALTHY,
            message="All good",
            response_time_ms=12.5,
            last_check=datetime.utcnow(),
            metadata={"key": "value"},
            consecutive_failures=0
        )
        
        assert health.name == "full-test"
        assert health.status == HealthStatus.HEALTHY
        assert health.message == "All good"
        assert health.response_time_ms == 12.5
        assert health.metadata["key"] == "value"
    
    def test_unhealthy_with_message(self):
        """ComponentHealth should capture error message"""
        health = ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message="Connection refused: host=localhost port=5432",
            consecutive_failures=3
        )
        
        assert health.status == HealthStatus.UNHEALTHY
        assert "Connection refused" in health.message
        assert health.consecutive_failures == 3


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_name(self):
        """ComponentHealth should accept empty name"""
        health = ComponentHealth(name="", status=HealthStatus.UNKNOWN)
        assert health.name == ""
    
    def test_zero_response_time(self):
        """ComponentHealth should accept zero response time"""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            response_time_ms=0.0
        )
        assert health.response_time_ms == 0.0
    
    def test_large_response_time(self):
        """ComponentHealth should accept large response time"""
        health = ComponentHealth(
            name="slow-db",
            status=HealthStatus.DEGRADED,
            response_time_ms=30000.0
        )
        assert health.response_time_ms == 30000.0
    
    def test_nested_metadata(self):
        """ComponentHealth should accept nested metadata"""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            metadata={
                "config": {
                    "host": "localhost",
                    "port": 8080
                },
                "stats": [1, 2, 3]
            }
        )
        assert health.metadata["config"]["host"] == "localhost"
        assert health.metadata["stats"] == [1, 2, 3]
    
    def test_lambda_check_function(self):
        """HealthChecker should accept lambda functions"""
        checker = HealthChecker()
        
        checker.register("lambda_check", lambda: {"status": "ok"})
        
        assert "lambda_check" in checker._checks
    
    def test_multiple_intervals(self):
        """HealthChecker should work with various intervals"""
        checker1 = HealthChecker(check_interval=1)
        checker2 = HealthChecker(check_interval=300)
        
        assert checker1.check_interval == 1
        assert checker2.check_interval == 300
