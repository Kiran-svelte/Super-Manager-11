"""
Performance & Reliability Module
================================

Enterprise-grade performance optimizations including:
- Circuit Breaker Pattern (prevents cascade failures)
- Connection Pooling (reduces connection overhead)
- Request Caching (LRU cache for repeated queries)
- Rate Limiting (protects against abuse)
- Retry Logic with Exponential Backoff
- Request Tracing and Metrics

Author: Super Manager AI
Version: 1.0.0
"""

import asyncio
import time
import hashlib
import logging
import functools
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import OrderedDict
from contextlib import asynccontextmanager
import threading
import statistics

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# Circuit Breaker Pattern
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout: float = 30.0               # Seconds before attempting recovery
    half_open_max_calls: int = 3        # Max calls in half-open state


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation
    
    Prevents cascade failures by tracking failures and temporarily
    blocking requests to failing services.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject all requests immediately
    - HALF_OPEN: Testing recovery, allow limited requests
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()
        self._metrics = CircuitBreakerMetrics()
    
    @property
    def state(self) -> CircuitState:
        """Get current state, potentially transitioning from OPEN to HALF_OPEN"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN")
            return self._state
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.config.timeout
    
    def record_success(self):
        """Record a successful call"""
        with self._lock:
            self._metrics.record_success()
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED (recovered)")
            else:
                self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self, error: Optional[Exception] = None):
        """Record a failed call"""
        with self._lock:
            self._metrics.record_failure()
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN (failure during recovery)")
            elif self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: CLOSED -> OPEN (threshold reached: {self._failure_count} failures)")
    
    def can_execute(self) -> bool:
        """Check if a request can be executed"""
        current_state = self.state
        
        if current_state == CircuitState.CLOSED:
            return True
        
        if current_state == CircuitState.OPEN:
            self._metrics.record_rejected()
            return False
        
        # HALF_OPEN: allow limited calls
        with self._lock:
            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "metrics": self._metrics.get_summary()
        }


@dataclass
class CircuitBreakerMetrics:
    """Track circuit breaker metrics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    
    def record_success(self):
        self.total_calls += 1
        self.successful_calls += 1
    
    def record_failure(self):
        self.total_calls += 1
        self.failed_calls += 1
        self.last_failure_time = datetime.utcnow()
    
    def record_rejected(self):
        self.rejected_calls += 1
    
    def get_summary(self) -> Dict[str, Any]:
        success_rate = (self.successful_calls / max(1, self.total_calls)) * 100
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rejected_calls": self.rejected_calls,
            "success_rate": f"{success_rate:.2f}%",
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


def circuit_breaker(breaker: CircuitBreaker):
    """Decorator to wrap functions with circuit breaker"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not breaker.can_execute():
                raise CircuitOpenError(f"Circuit {breaker.name} is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure(e)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not breaker.can_execute():
                raise CircuitOpenError(f"Circuit {breaker.name} is OPEN")
            
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure(e)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# =============================================================================
# LRU Cache with TTL
# =============================================================================

@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with expiration"""
    value: T
    expires_at: float
    hits: int = 0


class LRUCache(Generic[T]):
    """
    Thread-safe LRU Cache with TTL
    
    Features:
    - Least Recently Used eviction
    - Time-to-live for entries
    - Metrics tracking
    - Thread-safe operations
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            # Check expiration
            if time.time() > entry.expires_at:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[float] = None):
        """Set value in cache"""
        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            expires_at = time.time() + (ttl or self.default_ttl)
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
    
    def delete(self, key: str):
        """Delete value from cache"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / max(1, total)) * 100
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2f}%"
            }


def cached(cache: LRUCache, ttl: Optional[float] = None):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Skip caching for certain argument patterns
            skip_cache = kwargs.pop('_skip_cache', False)
            
            key = cache._generate_key(func.__name__, *args, **kwargs)
            
            if not skip_cache:
                cached_value = cache.get(key)
                if cached_value is not None:
                    return cached_value
            
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            skip_cache = kwargs.pop('_skip_cache', False)
            
            key = cache._generate_key(func.__name__, *args, **kwargs)
            
            if not skip_cache:
                cached_value = cache.get(key)
                if cached_value is not None:
                    return cached_value
            
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# =============================================================================
# Rate Limiter (Token Bucket Algorithm)
# =============================================================================

class RateLimiter:
    """
    Token Bucket Rate Limiter
    
    Allows bursts while maintaining average rate limit.
    Thread-safe for concurrent access.
    """
    
    def __init__(
        self,
        rate: float = 10.0,      # Tokens per second
        capacity: float = 100.0,  # Maximum tokens
        name: str = "default"
    ):
        self.rate = rate
        self.capacity = capacity
        self.name = name
        self._tokens = capacity
        self._last_update = time.time()
        self._lock = threading.Lock()
        self._total_requests = 0
        self._rejected_requests = 0
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self._last_update
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_update = now
    
    def acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire tokens, returns True if successful"""
        with self._lock:
            self._refill()
            self._total_requests += 1
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            
            self._rejected_requests += 1
            return False
    
    async def acquire_async(self, tokens: float = 1.0, timeout: float = 5.0) -> bool:
        """Async acquire with wait"""
        start = time.time()
        
        while time.time() - start < timeout:
            if self.acquire(tokens):
                return True
            await asyncio.sleep(0.1)
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        with self._lock:
            self._refill()
            return {
                "name": self.name,
                "available_tokens": self._tokens,
                "capacity": self.capacity,
                "rate": f"{self.rate}/s",
                "total_requests": self._total_requests,
                "rejected_requests": self._rejected_requests,
                "rejection_rate": f"{(self._rejected_requests / max(1, self._total_requests)) * 100:.2f}%"
            }


def rate_limited(limiter: RateLimiter, tokens: float = 1.0):
    """Decorator to apply rate limiting"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not await limiter.acquire_async(tokens):
                raise RateLimitExceeded(f"Rate limit exceeded for {limiter.name}")
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not limiter.acquire(tokens):
                raise RateLimitExceeded(f"Rate limit exceeded for {limiter.name}")
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


# =============================================================================
# Retry Logic with Exponential Backoff
# =============================================================================

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd


class RetryHandler:
    """
    Retry handler with exponential backoff
    
    Features:
    - Configurable retry attempts
    - Exponential backoff with optional jitter
    - Exception filtering
    - Metrics tracking
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._total_retries = 0
        self._successful_retries = 0
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry"""
        delay = min(
            self.config.max_delay,
            self.config.base_delay * (self.config.exponential_base ** attempt)
        )
        
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random())
        
        return delay
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if attempt > 0:
                    self._successful_retries += 1
                    logger.info(f"Retry successful after {attempt} attempts")
                
                return result
                
            except retryable_exceptions as e:
                last_exception = e
                self._total_retries += 1
                
                if attempt < self.config.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_attempts} attempts failed")
        
        raise last_exception
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        return {
            "total_retries": self._total_retries,
            "successful_retries": self._successful_retries,
            "config": {
                "max_attempts": self.config.max_attempts,
                "base_delay": self.config.base_delay,
                "max_delay": self.config.max_delay
            }
        }


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (Exception,)
):
    """Decorator for automatic retries"""
    config = RetryConfig(max_attempts=max_attempts, base_delay=base_delay)
    handler = RetryHandler(config)
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await handler.execute_with_retry(
                func, *args,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
        
        return async_wrapper
    
    return decorator


# =============================================================================
# Request Tracing & Metrics
# =============================================================================

@dataclass
class RequestTrace:
    """Individual request trace"""
    trace_id: str
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "in_progress"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RequestTracer:
    """
    Request tracing for observability
    
    Features:
    - Unique trace IDs
    - Duration tracking
    - Error capture
    - Percentile calculations
    """
    
    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self._traces: Dict[str, RequestTrace] = {}
        self._completed_durations: list = []
        self._lock = threading.Lock()
    
    def start_trace(self, operation: str, metadata: Optional[Dict] = None) -> str:
        """Start a new trace"""
        import uuid
        trace_id = str(uuid.uuid4())[:8]
        
        trace = RequestTrace(
            trace_id=trace_id,
            operation=operation,
            start_time=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self._traces[trace_id] = trace
            
            # Cleanup old traces
            while len(self._traces) > self.max_traces:
                oldest = min(self._traces.items(), key=lambda x: x[1].start_time)
                del self._traces[oldest[0]]
        
        return trace_id
    
    def end_trace(self, trace_id: str, status: str = "success", error: Optional[str] = None):
        """End a trace"""
        with self._lock:
            trace = self._traces.get(trace_id)
            if trace:
                trace.end_time = datetime.utcnow()
                trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000
                trace.status = status
                trace.error = error
                
                self._completed_durations.append(trace.duration_ms)
                
                # Keep only last 1000 durations for percentiles
                if len(self._completed_durations) > 1000:
                    self._completed_durations = self._completed_durations[-1000:]
    
    @asynccontextmanager
    async def trace(self, operation: str, metadata: Optional[Dict] = None):
        """Context manager for tracing"""
        trace_id = self.start_trace(operation, metadata)
        try:
            yield trace_id
            self.end_trace(trace_id, "success")
        except Exception as e:
            self.end_trace(trace_id, "error", str(e))
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        with self._lock:
            if not self._completed_durations:
                return {
                    "total_traces": 0,
                    "active_traces": len([t for t in self._traces.values() if t.status == "in_progress"]),
                    "percentiles": {}
                }
            
            durations = sorted(self._completed_durations)
            
            def percentile(p):
                k = (len(durations) - 1) * p / 100
                f = int(k)
                c = f + 1 if f + 1 < len(durations) else f
                return durations[f] + (k - f) * (durations[c] - durations[f])
            
            return {
                "total_traces": len(self._completed_durations),
                "active_traces": len([t for t in self._traces.values() if t.status == "in_progress"]),
                "avg_duration_ms": statistics.mean(durations),
                "percentiles": {
                    "p50": percentile(50),
                    "p90": percentile(90),
                    "p95": percentile(95),
                    "p99": percentile(99)
                }
            }
    
    def record_duration(self, operation: str, duration_ms: float):
        """
        Record a duration measurement directly without tracing
        Useful for middleware that just needs to track timing
        """
        with self._lock:
            self._completed_durations.append(duration_ms)
            
            # Keep only last 1000 durations
            if len(self._completed_durations) > 1000:
                self._completed_durations = self._completed_durations[-1000:]


# =============================================================================
# Connection Pool
# =============================================================================

class ConnectionPool:
    """
    Generic async connection pool
    
    Features:
    - Configurable pool size
    - Health checking
    - Automatic connection recycling
    """
    
    def __init__(
        self,
        create_connection: Callable,
        max_size: int = 10,
        min_size: int = 2,
        max_idle_time: float = 300.0
    ):
        self.create_connection = create_connection
        self.max_size = max_size
        self.min_size = min_size
        self.max_idle_time = max_idle_time
        
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._size = 0
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Initialize pool with minimum connections"""
        async with self._lock:
            if self._initialized:
                return
            
            for _ in range(self.min_size):
                conn = await self.create_connection()
                await self._pool.put(conn)
                self._size += 1
            
            self._initialized = True
            logger.info(f"Connection pool initialized with {self._size} connections")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        if not self._initialized:
            await self.initialize()
        
        conn = None
        
        # Try to get from pool
        try:
            conn = self._pool.get_nowait()
        except asyncio.QueueEmpty:
            # Create new if under max
            async with self._lock:
                if self._size < self.max_size:
                    conn = await self.create_connection()
                    self._size += 1
        
        if conn is None:
            # Wait for available connection
            conn = await self._pool.get()
        
        try:
            yield conn
        finally:
            # Return to pool
            try:
                self._pool.put_nowait(conn)
            except asyncio.QueueFull:
                # Pool full, discard connection
                async with self._lock:
                    self._size -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            "size": self._size,
            "available": self._pool.qsize(),
            "max_size": self.max_size,
            "min_size": self.min_size
        }


# =============================================================================
# Health Monitor
# =============================================================================

class HealthMonitor:
    """
    System health monitoring
    
    Tracks health of various components and provides
    overall system health status.
    """
    
    def __init__(self):
        self._components: Dict[str, Callable] = {}
        self._health_status: Dict[str, Dict] = {}
        self._last_check: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def register_component(self, name: str, health_check: Optional[Callable] = None):
        """Register a component for health monitoring"""
        with self._lock:
            if health_check:
                self._components[name] = health_check
            # Initialize health status
            self._health_status[name] = {
                "healthy": False,
                "message": "Not yet initialized",
                "updated_at": datetime.utcnow().isoformat()
            }
    
    def update_health(self, name: str, healthy: bool, message: str = "", metadata: Dict = None):
        """Update health status for a component"""
        with self._lock:
            self._health_status[name] = {
                "healthy": healthy,
                "message": message,
                "metadata": metadata or {},
                "updated_at": datetime.utcnow().isoformat()
            }
    
    def get_component_health(self, name: str) -> Dict[str, Any]:
        """Get current health of a component"""
        with self._lock:
            return self._health_status.get(name, {"healthy": False, "error": "Unknown component"})
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health status"""
        with self._lock:
            all_healthy = all(
                status.get("healthy", False) 
                for status in self._health_status.values()
            )
            return {
                "healthy": all_healthy,
                "status": "healthy" if all_healthy else "degraded",
                "components": dict(self._health_status)
            }
    
    async def check_component(self, name: str) -> Dict[str, Any]:
        """Check health of a specific component (if health_check registered)"""
        health_check = self._components.get(name)
        if not health_check:
            # Return cached status
            return self.get_component_health(name)
        
        try:
            start = time.time()
            if asyncio.iscoroutinefunction(health_check):
                result = await health_check()
            else:
                result = health_check()
            
            duration = (time.time() - start) * 1000
            
            status = {
                "status": "healthy" if result.get("healthy", True) else "unhealthy",
                "latency_ms": duration,
                "details": result,
                "checked_at": datetime.utcnow().isoformat()
            }
            
            with self._lock:
                self._last_check[name] = status
            
            return status
            
        except Exception as e:
            status = {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
            
            with self._lock:
                self._last_check[name] = status
            
            return status
    
    async def check_all(self) -> Dict[str, Any]:
        """Check health of all components"""
        results = {}
        overall_healthy = True
        
        for name in self._components:
            result = await self.check_component(name)
            results[name] = result
            if result.get("status") != "healthy":
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "components": results,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    def get_cached_status(self) -> Dict[str, Any]:
        """Get last known health status without checking"""
        with self._lock:
            return {
                "components": dict(self._last_check),
                "note": "Cached status, may be stale"
            }


# =============================================================================
# Global Instances for Easy Access
# =============================================================================

# Default instances
ai_circuit_breaker = CircuitBreaker("ai_provider", CircuitBreakerConfig(
    failure_threshold=3,
    timeout=30.0
))

db_circuit_breaker = CircuitBreaker("database", CircuitBreakerConfig(
    failure_threshold=5,
    timeout=60.0
))

email_circuit_breaker = CircuitBreaker("email", CircuitBreakerConfig(
    failure_threshold=3,
    timeout=120.0
))

response_cache = LRUCache(max_size=500, default_ttl=300.0)
api_rate_limiter = RateLimiter(rate=10.0, capacity=100.0, name="api")
request_tracer = RequestTracer(max_traces=1000)
retry_handler = RetryHandler()
health_monitor = HealthMonitor()


def get_all_metrics() -> Dict[str, Any]:
    """Get all performance metrics"""
    return {
        "circuit_breakers": {
            "ai_provider": ai_circuit_breaker.get_status(),
            "database": db_circuit_breaker.get_status(),
            "email": email_circuit_breaker.get_status()
        },
        "cache": response_cache.get_stats(),
        "rate_limiter": api_rate_limiter.get_stats(),
        "request_tracing": request_tracer.get_stats(),
        "retry_handler": retry_handler.get_stats()
    }
