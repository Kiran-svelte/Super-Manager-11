"""
Structured Logging Module
=========================

Enterprise-grade logging with:
- JSON structured output
- Request context tracking
- Log levels per component
- Log rotation
- Sensitive data masking
- Performance metrics in logs

Author: Super Manager AI
Version: 1.0.0
"""

import os
import sys
import json
import time
import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from contextvars import ContextVar
from functools import wraps
import traceback

# Context variable for request tracking
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


# =============================================================================
# JSON Formatter
# =============================================================================

class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging
    
    Output format:
    {
        "timestamp": "2024-01-01T12:00:00.000Z",
        "level": "INFO",
        "logger": "app.module",
        "message": "Log message",
        "request_id": "abc123",
        "extra": {...}
    }
    """
    
    def __init__(self, include_trace: bool = True, mask_sensitive: bool = True):
        super().__init__()
        self.include_trace = include_trace
        self.mask_sensitive = mask_sensitive
        self._sensitive_keys = {
            'password', 'secret', 'token', 'api_key', 'apikey',
            'authorization', 'auth', 'credentials', 'private'
        }
    
    def _mask_value(self, value: str) -> str:
        """Mask sensitive value"""
        if len(value) <= 8:
            return '***'
        return value[:4] + '***' + value[-4:]
    
    def _mask_dict(self, data: Dict) -> Dict:
        """Recursively mask sensitive data in dict"""
        if not self.mask_sensitive:
            return data
        
        result = {}
        for key, value in data.items():
            lower_key = key.lower()
            if any(s in lower_key for s in self._sensitive_keys):
                result[key] = self._mask_value(str(value)) if isinstance(value, str) else '***'
            elif isinstance(value, dict):
                result[key] = self._mask_dict(value)
            else:
                result[key] = value
        return result
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request context
        ctx = request_context.get()
        if ctx:
            log_entry["request_id"] = ctx.get("request_id")
            log_entry["user_id"] = ctx.get("user_id")
            log_entry["path"] = ctx.get("path")
        
        # Add location info
        log_entry["location"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName
        }
        
        # Add exception info if present
        if record.exc_info and self.include_trace:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        extra = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'message', 'asctime'
            }:
                extra[key] = value
        
        if extra:
            log_entry["extra"] = self._mask_dict(extra)
        
        return json.dumps(log_entry, default=str)


# =============================================================================
# Console Formatter (Human Readable)
# =============================================================================

class ColoredFormatter(logging.Formatter):
    """
    Colored console output for development
    
    Colors:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red background
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[41m',  # Red background
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Get color
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Get request context
        ctx = request_context.get()
        request_id = ctx.get("request_id", "")[:8] if ctx else ""
        
        # Build message
        parts = [
            f"\033[90m{timestamp}\033[0m",  # Gray timestamp
            f"{color}{record.levelname:8s}{reset}",
            f"\033[35m{record.name:20s}\033[0m",  # Purple logger name
        ]
        
        if request_id:
            parts.append(f"\033[90m[{request_id}]\033[0m")
        
        parts.append(record.getMessage())
        
        result = " ".join(parts)
        
        # Add exception if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            result += f"\n{self.COLORS['ERROR']}{exc_text}{reset}"
        
        return result


# =============================================================================
# Logger Configuration
# =============================================================================

class LogConfig:
    """Logger configuration"""
    
    def __init__(
        self,
        level: str = "INFO",
        json_format: bool = False,
        include_trace: bool = True,
        log_file: Optional[str] = None
    ):
        self.level = level
        self.json_format = json_format
        self.include_trace = include_trace
        self.log_file = log_file


def setup_logging(config: Optional[LogConfig] = None) -> logging.Logger:
    """
    Setup application logging
    
    Usage:
        logger = setup_logging(LogConfig(level="DEBUG", json_format=False))
    """
    config = config or LogConfig()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level.upper()))
    
    if config.json_format:
        console_handler.setFormatter(JSONFormatter(
            include_trace=config.include_trace
        ))
    else:
        console_handler.setFormatter(ColoredFormatter())
    
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, config.level.upper()))
        file_handler.setFormatter(JSONFormatter(include_trace=config.include_trace))
        root_logger.addHandler(file_handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return root_logger


# =============================================================================
# Context Manager for Request Context
# =============================================================================

class LogContext:
    """Context manager for setting request context in logs"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self._token = None
    
    def __enter__(self):
        current = request_context.get().copy()
        current.update(self.context)
        self._token = request_context.set(current)
        return self
    
    def __exit__(self, *args):
        request_context.set({})


def log_context(**kwargs):
    """Decorator to add context to all logs within a function"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **inner_kwargs):
            with LogContext(**kwargs):
                return await func(*args, **inner_kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **inner_kwargs):
            with LogContext(**kwargs):
                return func(*args, **inner_kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# =============================================================================
# Performance Logging
# =============================================================================

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_duration(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        **extra
    ):
        """Log operation duration"""
        level = logging.INFO if success else logging.WARNING
        self.logger.log(
            level,
            f"{operation} completed in {duration_ms:.2f}ms",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                **extra
            }
        )
    
    def log_throughput(
        self,
        operation: str,
        count: int,
        duration_ms: float,
        **extra
    ):
        """Log throughput metrics"""
        rate = (count / duration_ms) * 1000 if duration_ms > 0 else 0
        self.logger.info(
            f"{operation}: {count} items in {duration_ms:.2f}ms ({rate:.2f}/s)",
            extra={
                "operation": operation,
                "count": count,
                "duration_ms": duration_ms,
                "rate_per_second": rate,
                **extra
            }
        )


def timed(logger: Optional[logging.Logger] = None, operation: Optional[str] = None):
    """Decorator to log function execution time"""
    def decorator(func):
        nonlocal operation
        if operation is None:
            operation = func.__name__
        
        log = logger or logging.getLogger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                log.debug(
                    f"{operation} completed in {duration_ms:.2f}ms",
                    extra={"operation": operation, "duration_ms": duration_ms}
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                log.warning(
                    f"{operation} failed after {duration_ms:.2f}ms: {e}",
                    extra={"operation": operation, "duration_ms": duration_ms, "error": str(e)}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                log.debug(
                    f"{operation} completed in {duration_ms:.2f}ms",
                    extra={"operation": operation, "duration_ms": duration_ms}
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                log.warning(
                    f"{operation} failed after {duration_ms:.2f}ms: {e}",
                    extra={"operation": operation, "duration_ms": duration_ms, "error": str(e)}
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# =============================================================================
# Audit Logger
# =============================================================================

class AuditLogger:
    """
    Security-focused audit logging
    
    Logs security-relevant events:
    - Authentication attempts
    - Authorization decisions
    - Data access
    - Configuration changes
    """
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
    
    def log_auth_attempt(
        self,
        user_id: Optional[str],
        success: bool,
        method: str = "password",
        ip_address: Optional[str] = None,
        **extra
    ):
        """Log authentication attempt"""
        level = logging.INFO if success else logging.WARNING
        action = "authenticated" if success else "failed authentication"
        
        self.logger.log(
            level,
            f"User {user_id or 'unknown'} {action} via {method}",
            extra={
                "event_type": "auth_attempt",
                "user_id": user_id,
                "success": success,
                "method": method,
                "ip_address": ip_address,
                **extra
            }
        )
    
    def log_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        allowed: bool,
        **extra
    ):
        """Log resource access"""
        level = logging.INFO if allowed else logging.WARNING
        
        self.logger.log(
            level,
            f"User {user_id} {'allowed' if allowed else 'denied'} to {action} {resource}",
            extra={
                "event_type": "access_control",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "allowed": allowed,
                **extra
            }
        )
    
    def log_data_change(
        self,
        user_id: str,
        entity: str,
        entity_id: str,
        action: str,
        changes: Optional[Dict] = None,
        **extra
    ):
        """Log data modification"""
        self.logger.info(
            f"User {user_id} {action} {entity} {entity_id}",
            extra={
                "event_type": "data_change",
                "user_id": user_id,
                "entity": entity,
                "entity_id": entity_id,
                "action": action,
                "changes": changes,
                **extra
            }
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        **extra
    ):
        """Log security event"""
        level_map = {
            "low": logging.INFO,
            "medium": logging.WARNING,
            "high": logging.ERROR,
            "critical": logging.CRITICAL
        }
        level = level_map.get(severity.lower(), logging.WARNING)
        
        self.logger.log(
            level,
            f"SECURITY [{severity.upper()}]: {description}",
            extra={
                "event_type": f"security_{event_type}",
                "severity": severity,
                **extra
            }
        )


# =============================================================================
# Global Instances
# =============================================================================

# Setup default logging
_default_config = LogConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=os.getenv("LOG_FORMAT", "").lower() == "json"
)
setup_logging(_default_config)

# Create loggers
perf_logger = PerformanceLogger()
audit_logger = AuditLogger()

# Create application logger
def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module"""
    return logging.getLogger(name)
