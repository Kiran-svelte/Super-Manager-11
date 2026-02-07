"""
Error Handling Module
=====================

Comprehensive error handling system including:
- Custom exception hierarchy
- Error tracking and aggregation
- User-friendly error responses
- Automatic error recovery
- Integration with monitoring

Author: Super Manager
Version: 1.0.0
"""

import os
import sys
import uuid
import json
import traceback
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from collections import defaultdict
import threading
import asyncio

logger = logging.getLogger(__name__)


# =============================================================================
# Error Severity Levels
# =============================================================================

class ErrorSeverity(str, Enum):
    DEBUG = "debug"        # Development-only issues
    INFO = "info"          # Informational, no action needed
    WARNING = "warning"    # Potential issue, monitor
    ERROR = "error"        # Error requiring attention
    CRITICAL = "critical"  # System-level failure


class ErrorCategory(str, Enum):
    VALIDATION = "validation"      # Input validation errors
    AUTHENTICATION = "authentication"  # Auth failures
    AUTHORIZATION = "authorization"    # Permission denied
    NOT_FOUND = "not_found"        # Resource not found
    RATE_LIMIT = "rate_limit"      # Rate limiting
    EXTERNAL_API = "external_api"  # Third-party API errors
    DATABASE = "database"          # Database errors
    NETWORK = "network"            # Network/connectivity issues
    INTERNAL = "internal"          # Internal server errors
    CONFIGURATION = "configuration"  # Configuration issues
    TIMEOUT = "timeout"            # Operation timeouts


# =============================================================================
# Custom Exception Classes
# =============================================================================

class SuperManagerError(Exception):
    """Base exception for Super Manager"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        details: Dict[str, Any] = None,
        user_message: str = None,
        recoverable: bool = True,
        http_status: int = 500
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.category = category
        self.details = details or {}
        self.user_message = user_message or "An error occurred. Please try again."
        self.recoverable = recoverable
        self.http_status = http_status
        self.error_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "error": True,
            "error_id": self.error_id,
            "code": self.error_code,
            "message": self.user_message,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable
        }
    
    def to_log_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging (includes internal details)"""
        return {
            **self.to_dict(),
            "internal_message": self.message,
            "details": self.details,
            "severity": self.severity.value,
            "traceback": traceback.format_exc()
        }


# Specific Exception Types
class ValidationError(SuperManagerError):
    """Input validation failed"""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.VALIDATION,
            http_status=400,
            user_message=message,
            **kwargs
        )
        self.details["field"] = field


class AuthenticationError(SuperManagerError):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTH_REQUIRED",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.AUTHENTICATION,
            http_status=401,
            user_message="Please log in to continue.",
            **kwargs
        )


class AuthorizationError(SuperManagerError):
    """Authorization/permission denied"""
    
    def __init__(self, message: str = "Permission denied", resource: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.AUTHORIZATION,
            http_status=403,
            user_message="You don't have permission to perform this action.",
            **kwargs
        )
        self.details["resource"] = resource


class NotFoundError(SuperManagerError):
    """Resource not found"""
    
    def __init__(self, resource_type: str, resource_id: str = None, **kwargs):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            severity=ErrorSeverity.INFO,
            category=ErrorCategory.NOT_FOUND,
            http_status=404,
            user_message=f"The requested {resource_type.lower()} could not be found.",
            **kwargs
        )
        self.details["resource_type"] = resource_type
        self.details["resource_id"] = resource_id


class RateLimitError(SuperManagerError):
    """Rate limit exceeded"""
    
    def __init__(self, retry_after: int = 60, **kwargs):
        super().__init__(
            message=f"Rate limit exceeded, retry after {retry_after}s",
            error_code="RATE_LIMIT_EXCEEDED",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.RATE_LIMIT,
            http_status=429,
            user_message="You're making too many requests. Please slow down.",
            recoverable=True,
            **kwargs
        )
        self.details["retry_after_seconds"] = retry_after


class ExternalAPIError(SuperManagerError):
    """External API call failed"""
    
    def __init__(self, service: str, message: str, status_code: int = None, **kwargs):
        super().__init__(
            message=f"{service} API error: {message}",
            error_code="EXTERNAL_API_ERROR",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.EXTERNAL_API,
            http_status=502,
            user_message="An external service is temporarily unavailable. Please try again.",
            **kwargs
        )
        self.details["service"] = service
        self.details["upstream_status"] = status_code


class DatabaseError(SuperManagerError):
    """Database operation failed"""
    
    def __init__(self, operation: str, message: str, **kwargs):
        super().__init__(
            message=f"Database {operation} failed: {message}",
            error_code="DATABASE_ERROR",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.DATABASE,
            http_status=503,
            user_message="A database error occurred. Please try again later.",
            recoverable=True,
            **kwargs
        )
        self.details["operation"] = operation


class TimeoutError(SuperManagerError):
    """Operation timed out"""
    
    def __init__(self, operation: str, timeout_seconds: float, **kwargs):
        super().__init__(
            message=f"{operation} timed out after {timeout_seconds}s",
            error_code="TIMEOUT",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.TIMEOUT,
            http_status=504,
            user_message="The request took too long. Please try again.",
            recoverable=True,
            **kwargs
        )
        self.details["operation"] = operation
        self.details["timeout_seconds"] = timeout_seconds


class ConfigurationError(SuperManagerError):
    """Configuration/setup error"""
    
    def __init__(self, config_key: str, message: str, **kwargs):
        super().__init__(
            message=f"Configuration error for '{config_key}': {message}",
            error_code="CONFIGURATION_ERROR",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.CONFIGURATION,
            http_status=500,
            user_message="A system configuration error occurred.",
            recoverable=False,
            **kwargs
        )
        self.details["config_key"] = config_key


# =============================================================================
# Error Tracker
# =============================================================================

@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_id: str
    error_code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    count: int = 1
    last_occurrence: datetime = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""


class ErrorTracker:
    """
    Track and aggregate errors for monitoring
    
    Features:
    - Error counting and deduplication
    - Error rate tracking
    - Threshold-based alerting
    - Error history
    """
    
    def __init__(
        self,
        max_history: int = 1000,
        aggregation_window_minutes: int = 5
    ):
        self.max_history = max_history
        self.aggregation_window = timedelta(minutes=aggregation_window_minutes)
        
        self._errors: List[ErrorRecord] = []
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._error_rates: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Alert thresholds
        self.alert_thresholds: Dict[str, int] = {
            "per_minute": 10,
            "per_hour": 100,
            "critical_any": 1
        }
        
        # Alert callbacks
        self._alert_callbacks: List[Callable] = []
    
    def track(self, error: SuperManagerError, context: Dict[str, Any] = None) -> ErrorRecord:
        """Track an error occurrence"""
        now = datetime.utcnow()
        
        record = ErrorRecord(
            error_id=error.error_id,
            error_code=error.error_code,
            message=error.message,
            category=error.category,
            severity=error.severity,
            timestamp=now,
            last_occurrence=now,
            context=context or {},
            stack_trace=traceback.format_exc()
        )
        
        with self._lock:
            # Update counts
            self._error_counts[error.error_code] += 1
            
            # Track for rate calculation
            self._error_rates[error.error_code].append(now)
            
            # Clean old rate entries
            cutoff = now - timedelta(hours=1)
            for code in self._error_rates:
                self._error_rates[code] = [
                    t for t in self._error_rates[code] if t > cutoff
                ]
            
            # Add to history
            self._errors.append(record)
            
            # Trim history
            if len(self._errors) > self.max_history:
                self._errors = self._errors[-self.max_history:]
        
        # Check for alerts
        self._check_thresholds(error)
        
        # Log the error
        self._log_error(error, record)
        
        return record
    
    def _check_thresholds(self, error: SuperManagerError):
        """Check if error thresholds are exceeded"""
        now = datetime.utcnow()
        
        # Critical errors always alert
        if error.severity == ErrorSeverity.CRITICAL:
            self._trigger_alert("critical", error)
            return
        
        with self._lock:
            rates = self._error_rates.get(error.error_code, [])
            
            # Per-minute rate
            minute_ago = now - timedelta(minutes=1)
            per_minute = len([t for t in rates if t > minute_ago])
            
            if per_minute >= self.alert_thresholds["per_minute"]:
                self._trigger_alert("high_rate", error, {"rate_per_minute": per_minute})
            
            # Per-hour rate
            if len(rates) >= self.alert_thresholds["per_hour"]:
                self._trigger_alert("sustained_errors", error, {"rate_per_hour": len(rates)})
    
    def _trigger_alert(self, alert_type: str, error: SuperManagerError, metadata: Dict = None):
        """Trigger an alert"""
        alert_data = {
            "type": alert_type,
            "error_code": error.error_code,
            "severity": error.severity.value,
            "message": error.message,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.critical(f"ERROR ALERT: {alert_type} - {error.error_code}: {error.message}")
        
        for callback in self._alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def _log_error(self, error: SuperManagerError, record: ErrorRecord):
        """Log error with appropriate level"""
        log_level = {
            ErrorSeverity.DEBUG: logging.DEBUG,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error.severity, logging.ERROR)
        
        logger.log(
            log_level,
            f"[{error.error_id}] {error.error_code}: {error.message}",
            extra={"error_record": record}
        )
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback for alerts"""
        self._alert_callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        with self._lock:
            # Recent errors
            recent_minute = [e for e in self._errors if e.timestamp > minute_ago]
            recent_hour = [e for e in self._errors if e.timestamp > hour_ago]
            
            # By category
            by_category = defaultdict(int)
            for e in recent_hour:
                by_category[e.category.value] += 1
            
            # By severity
            by_severity = defaultdict(int)
            for e in recent_hour:
                by_severity[e.severity.value] += 1
            
            return {
                "total_tracked": len(self._errors),
                "errors_last_minute": len(recent_minute),
                "errors_last_hour": len(recent_hour),
                "by_category": dict(by_category),
                "by_severity": dict(by_severity),
                "top_errors": sorted(
                    self._error_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            }
    
    def get_recent_errors(self, limit: int = 50, category: ErrorCategory = None) -> List[Dict]:
        """Get recent errors"""
        with self._lock:
            errors = self._errors.copy()
        
        if category:
            errors = [e for e in errors if e.category == category]
        
        errors.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                "error_id": e.error_id,
                "code": e.error_code,
                "message": e.message,
                "category": e.category.value,
                "severity": e.severity.value,
                "timestamp": e.timestamp.isoformat()
            }
            for e in errors[:limit]
        ]


# Global error tracker
error_tracker = ErrorTracker()


# =============================================================================
# Error Handler Decorators
# =============================================================================

def handle_errors(
    default_message: str = "An error occurred",
    reraise: bool = True,
    track: bool = True
):
    """
    Decorator to handle and track errors in functions
    
    Args:
        default_message: Default error message for unhandled exceptions
        reraise: Whether to re-raise the exception
        track: Whether to track the error
    """
    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SuperManagerError as e:
                if track:
                    error_tracker.track(e, {"function": func.__name__, "args": str(args)[:200]})
                if reraise:
                    raise
                return None
            except Exception as e:
                error = SuperManagerError(
                    message=str(e) or default_message,
                    severity=ErrorSeverity.ERROR
                )
                if track:
                    error_tracker.track(error, {"function": func.__name__, "original_error": type(e).__name__})
                if reraise:
                    raise error from e
                return None
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SuperManagerError as e:
                if track:
                    error_tracker.track(e, {"function": func.__name__})
                if reraise:
                    raise
                return None
            except Exception as e:
                error = SuperManagerError(
                    message=str(e) or default_message,
                    severity=ErrorSeverity.ERROR
                )
                if track:
                    error_tracker.track(error, {"function": func.__name__, "original_error": type(e).__name__})
                if reraise:
                    raise error from e
                return None
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on error with exponential backoff
    
    Args:
        max_retries: Maximum retry attempts
        delay_seconds: Initial delay between retries
        backoff_multiplier: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to retry on
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            delay = delay_seconds
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                        await asyncio.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(f"Max retries exceeded for {func.__name__}")
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_exception = None
            delay = delay_seconds
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                        time.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(f"Max retries exceeded for {func.__name__}")
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# =============================================================================
# FastAPI Error Handlers
# =============================================================================

def setup_fastapi_error_handlers(app):
    """
    Setup FastAPI exception handlers
    
    Usage:
        from errors import setup_fastapi_error_handlers
        setup_fastapi_error_handlers(app)
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    @app.exception_handler(SuperManagerError)
    async def supermanager_error_handler(request: Request, exc: SuperManagerError):
        error_tracker.track(exc, {"path": request.url.path, "method": request.method})
        
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        error = SuperManagerError(
            message=str(exc),
            severity=ErrorSeverity.ERROR
        )
        error_tracker.track(error, {"path": request.url.path, "method": request.method})
        
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_id": error.error_id,
                "message": "An unexpected error occurred. Please try again.",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return app
