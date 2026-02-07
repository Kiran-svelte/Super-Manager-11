"""
Monitoring & Observability Module
=================================

Comprehensive monitoring system including:
- Health checks for all components
- Metrics collection (Prometheus-compatible)
- Structured logging
- Alerting integration
- Performance tracking

Author: Super Manager
Version: 1.0.0
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading
import json

logger = logging.getLogger(__name__)


# =============================================================================
# Health Check System
# =============================================================================

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component"""
    name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0
    last_check: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    consecutive_failures: int = 0


class HealthChecker:
    """
    Centralized health check system
    
    Features:
    - Register multiple health check functions
    - Parallel health checks
    - Automatic status aggregation
    - History tracking
    """
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._checks: Dict[str, Callable] = {}
        self._status: Dict[str, ComponentHealth] = {}
        self._history: Dict[str, deque] = {}
        self._lock = threading.Lock()
        self._running = False
    
    def register(self, name: str, check_func: Callable, critical: bool = False):
        """Register a health check function"""
        self._checks[name] = {
            "func": check_func,
            "critical": critical
        }
        self._status[name] = ComponentHealth(
            name=name,
            status=HealthStatus.UNKNOWN
        )
        self._history[name] = deque(maxlen=100)  # Keep last 100 checks
        logger.info(f"Registered health check: {name}")
    
    async def check_component(self, name: str) -> ComponentHealth:
        """Run health check for a single component"""
        if name not in self._checks:
            return ComponentHealth(name=name, status=HealthStatus.UNKNOWN, message="Not registered")
        
        check_info = self._checks[name]
        start_time = time.time()
        
        try:
            result = check_info["func"]()
            if asyncio.iscoroutine(result):
                result = await result
            
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, dict):
                status = HealthStatus.HEALTHY if result.get("healthy", True) else HealthStatus.UNHEALTHY
                message = result.get("message", "")
                metadata = result.get("metadata", {})
            elif isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = ""
                metadata = {}
            else:
                status = HealthStatus.HEALTHY
                message = str(result) if result else ""
                metadata = {}
            
            health = ComponentHealth(
                name=name,
                status=status,
                message=message,
                response_time_ms=response_time,
                metadata=metadata,
                consecutive_failures=0
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            prev_failures = self._status.get(name, ComponentHealth(name=name, status=HealthStatus.UNKNOWN)).consecutive_failures
            
            health = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                response_time_ms=response_time,
                consecutive_failures=prev_failures + 1
            )
            logger.warning(f"Health check failed for {name}: {e}")
        
        with self._lock:
            self._status[name] = health
            self._history[name].append({
                "status": health.status.value,
                "response_time_ms": health.response_time_ms,
                "timestamp": health.last_check.isoformat()
            })
        
        return health
    
    async def check_all(self) -> Dict[str, ComponentHealth]:
        """Run all health checks in parallel"""
        tasks = [self.check_component(name) for name in self._checks]
        await asyncio.gather(*tasks, return_exceptions=True)
        return self._status.copy()
    
    def get_overall_status(self) -> Dict[str, Any]:
        """Get aggregated health status"""
        with self._lock:
            statuses = list(self._status.values())
        
        if not statuses:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "healthy": False,
                "components": {}
            }
        
        # Check critical components
        critical_unhealthy = any(
            s.status == HealthStatus.UNHEALTHY
            for name, s in self._status.items()
            if self._checks.get(name, {}).get("critical", False)
        )
        
        all_healthy = all(s.status == HealthStatus.HEALTHY for s in statuses)
        any_unhealthy = any(s.status == HealthStatus.UNHEALTHY for s in statuses)
        
        if critical_unhealthy:
            overall = HealthStatus.UNHEALTHY
        elif all_healthy:
            overall = HealthStatus.HEALTHY
        elif any_unhealthy:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.DEGRADED
        
        return {
            "status": overall.value,
            "healthy": overall == HealthStatus.HEALTHY,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                name: {
                    "status": health.status.value,
                    "message": health.message,
                    "response_time_ms": health.response_time_ms,
                    "last_check": health.last_check.isoformat()
                }
                for name, health in self._status.items()
            }
        }
    
    def get_history(self, component: str = None) -> Dict[str, List]:
        """Get health check history"""
        with self._lock:
            if component:
                return {component: list(self._history.get(component, []))}
            return {name: list(history) for name, history in self._history.items()}


# Global health checker instance
health_checker = HealthChecker()


# =============================================================================
# Metrics Collection
# =============================================================================

class MetricsCollector:
    """
    Prometheus-compatible metrics collector
    
    Metric Types:
    - Counter: Monotonically increasing values
    - Gauge: Values that can go up and down
    - Histogram: Distribution of values
    """
    
    def __init__(self):
        self._counters: Dict[str, Dict[str, float]] = {}
        self._gauges: Dict[str, Dict[str, float]] = {}
        self._histograms: Dict[str, Dict[str, List[float]]] = {}
        self._labels: Dict[str, Dict[str, str]] = {}
        self._lock = threading.Lock()
    
    def counter_inc(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Increment a counter"""
        labels_key = self._labels_to_key(labels)
        with self._lock:
            if name not in self._counters:
                self._counters[name] = {}
            if labels_key not in self._counters[name]:
                self._counters[name][labels_key] = 0
            self._counters[name][labels_key] += value
    
    def gauge_set(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value"""
        labels_key = self._labels_to_key(labels)
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
            self._gauges[name][labels_key] = value
    
    def histogram_observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram observation"""
        labels_key = self._labels_to_key(labels)
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = {}
            if labels_key not in self._histograms[name]:
                self._histograms[name][labels_key] = []
            
            # Keep last 1000 observations
            observations = self._histograms[name][labels_key]
            observations.append(value)
            if len(observations) > 1000:
                self._histograms[name][labels_key] = observations[-1000:]
    
    def _labels_to_key(self, labels: Dict[str, str] = None) -> str:
        """Convert labels dict to a hashable key"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    def get_counter(self, name: str) -> Dict[str, float]:
        """Get counter values"""
        with self._lock:
            return self._counters.get(name, {}).copy()
    
    def get_gauge(self, name: str) -> Dict[str, float]:
        """Get gauge values"""
        with self._lock:
            return self._gauges.get(name, {}).copy()
    
    def get_histogram_stats(self, name: str) -> Dict[str, Dict]:
        """Get histogram statistics"""
        with self._lock:
            if name not in self._histograms:
                return {}
            
            result = {}
            for labels_key, observations in self._histograms[name].items():
                if not observations:
                    continue
                
                sorted_obs = sorted(observations)
                n = len(sorted_obs)
                
                result[labels_key] = {
                    "count": n,
                    "sum": sum(sorted_obs),
                    "min": sorted_obs[0],
                    "max": sorted_obs[-1],
                    "mean": sum(sorted_obs) / n,
                    "p50": sorted_obs[int(n * 0.5)],
                    "p90": sorted_obs[int(n * 0.9)],
                    "p95": sorted_obs[int(n * 0.95)],
                    "p99": sorted_obs[int(n * 0.99)] if n > 100 else sorted_obs[-1]
                }
            
            return result
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            "counters": {name: self.get_counter(name) for name in self._counters},
            "gauges": {name: self.get_gauge(name) for name in self._gauges},
            "histograms": {name: self.get_histogram_stats(name) for name in self._histograms}
        }
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Counters
        for name, values in self._counters.items():
            for labels_key, value in values.items():
                labels_str = f"{{{labels_key}}}" if labels_key else ""
                lines.append(f"{name}{labels_str} {value}")
        
        # Gauges
        for name, values in self._gauges.items():
            for labels_key, value in values.items():
                labels_str = f"{{{labels_key}}}" if labels_key else ""
                lines.append(f"{name}{labels_str} {value}")
        
        # Histograms (simplified)
        for name, stats in self._histograms.items():
            for labels_key, observations in stats.items():
                if observations:
                    labels_str = f"{{{labels_key}}}" if labels_key else ""
                    lines.append(f"{name}_count{labels_str} {len(observations)}")
                    lines.append(f"{name}_sum{labels_str} {sum(observations)}")
        
        return "\n".join(lines)


# Global metrics collector
metrics = MetricsCollector()


# =============================================================================
# System Metrics
# =============================================================================

def collect_system_metrics():
    """Collect system resource metrics"""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)
    metrics.gauge_set("system_cpu_percent", cpu_percent)
    
    # Memory
    memory = psutil.virtual_memory()
    metrics.gauge_set("system_memory_total_bytes", memory.total)
    metrics.gauge_set("system_memory_used_bytes", memory.used)
    metrics.gauge_set("system_memory_percent", memory.percent)
    
    # Disk
    disk = psutil.disk_usage('/')
    metrics.gauge_set("system_disk_total_bytes", disk.total)
    metrics.gauge_set("system_disk_used_bytes", disk.used)
    metrics.gauge_set("system_disk_percent", disk.percent)
    
    # Process
    process = psutil.Process()
    metrics.gauge_set("process_memory_bytes", process.memory_info().rss)
    metrics.gauge_set("process_cpu_percent", process.cpu_percent())
    metrics.gauge_set("process_threads", process.num_threads())
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "process_memory_mb": process.memory_info().rss / 1024 / 1024
    }


# =============================================================================
# Request Tracking
# =============================================================================

class RequestTracker:
    """Track API request metrics"""
    
    def __init__(self):
        self._active_requests = 0
        self._lock = threading.Lock()
    
    def start_request(self, path: str, method: str):
        """Mark request as started"""
        with self._lock:
            self._active_requests += 1
        
        metrics.counter_inc("http_requests_total", labels={"path": path, "method": method})
        metrics.gauge_set("http_requests_active", self._active_requests)
    
    def end_request(self, path: str, method: str, status_code: int, duration_ms: float):
        """Mark request as completed"""
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
        
        labels = {"path": path, "method": method, "status": str(status_code)}
        metrics.histogram_observe("http_request_duration_ms", duration_ms, labels)
        metrics.gauge_set("http_requests_active", self._active_requests)
        
        # Track errors
        if status_code >= 400:
            metrics.counter_inc("http_errors_total", labels=labels)


request_tracker = RequestTracker()


# =============================================================================
# Built-in Health Checks
# =============================================================================

def check_database_health():
    """Check database connectivity"""
    try:
        # This would be replaced with actual DB check
        from ..database_supabase import get_supabase_client
        client = get_supabase_client()
        if client:
            return {"healthy": True, "message": "Database connected"}
        return {"healthy": False, "message": "Database not configured"}
    except Exception as e:
        return {"healthy": False, "message": str(e)}


def check_memory_health():
    """Check if memory usage is acceptable"""
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        return {"healthy": False, "message": f"Memory critical: {memory.percent}%"}
    elif memory.percent > 80:
        return {"healthy": True, "message": f"Memory warning: {memory.percent}%", "metadata": {"warning": True}}
    return {"healthy": True, "message": f"Memory OK: {memory.percent}%"}


def check_disk_health():
    """Check if disk usage is acceptable"""
    disk = psutil.disk_usage('/')
    if disk.percent > 95:
        return {"healthy": False, "message": f"Disk critical: {disk.percent}%"}
    elif disk.percent > 85:
        return {"healthy": True, "message": f"Disk warning: {disk.percent}%", "metadata": {"warning": True}}
    return {"healthy": True, "message": f"Disk OK: {disk.percent}%"}


def check_cpu_health():
    """Check if CPU usage is acceptable"""
    cpu = psutil.cpu_percent(interval=0.5)
    if cpu > 95:
        return {"healthy": False, "message": f"CPU critical: {cpu}%"}
    elif cpu > 80:
        return {"healthy": True, "message": f"CPU high: {cpu}%", "metadata": {"warning": True}}
    return {"healthy": True, "message": f"CPU OK: {cpu}%"}


# Register built-in health checks
def setup_health_checks():
    """Register all built-in health checks"""
    health_checker.register("database", check_database_health, critical=True)
    health_checker.register("memory", check_memory_health, critical=False)
    health_checker.register("disk", check_disk_health, critical=False)
    health_checker.register("cpu", check_cpu_health, critical=False)
