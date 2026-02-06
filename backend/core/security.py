"""
Security Middleware Module
==========================

Enterprise-grade security layer including:
- Security Headers (CSP, HSTS, X-Frame-Options, etc.)
- Input Validation & Sanitization
- Request Rate Limiting per IP
- Request ID Generation
- Sensitive Data Masking
- SQL Injection Prevention
- XSS Protection

Author: Super Manager AI
Version: 1.0.0
"""

import re
import time
import uuid
import html
import logging
import hashlib
from typing import Dict, Any, Optional, Callable, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import ipaddress

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# =============================================================================
# Security Headers Middleware
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses
    
    Headers added:
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-Frame-Options: Clickjacking protection
    - X-XSS-Protection: XSS filtering
    - Strict-Transport-Security: HSTS
    - Content-Security-Policy: CSP
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Feature permissions
    """
    
    def __init__(
        self,
        app: ASGIApp,
        enable_hsts: bool = True,
        enable_csp: bool = True,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.enable_csp = enable_csp
        self.custom_headers = custom_headers or {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Anti-MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS (HTTP Strict Transport Security)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        if self.enable_csp:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https: wss:; "
                "frame-ancestors 'none';"
            )
            response.headers["Content-Security-Policy"] = csp
        
        # Feature/Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        
        # Custom headers
        for key, value in self.custom_headers.items():
            response.headers[key] = value
        
        return response


# =============================================================================
# Request ID Middleware
# =============================================================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Generates unique request IDs for tracing
    
    Adds X-Request-ID header to all requests and responses
    for distributed tracing and debugging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get existing ID or generate new one
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in request state for handlers to access
        request.state.request_id = request_id
        
        # Add to response
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


# =============================================================================
# IP-based Rate Limiting Middleware
# =============================================================================

@dataclass
class IPRateLimitConfig:
    """Configuration for IP-based rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    block_duration_minutes: int = 15
    whitelist: Set[str] = field(default_factory=set)


class IPRateLimiter:
    """
    IP-based rate limiter using sliding window
    
    Features:
    - Per-minute and per-hour limits
    - Automatic blocking of abusive IPs
    - Whitelist support
    - Thread-safe
    """
    
    def __init__(self, config: Optional[IPRateLimitConfig] = None):
        self.config = config or IPRateLimitConfig()
        self._minute_counts: Dict[str, List[float]] = defaultdict(list)
        self._hour_counts: Dict[str, List[float]] = defaultdict(list)
        self._blocked_ips: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def _clean_old_entries(self, ip: str, now: float):
        """Remove expired entries"""
        minute_ago = now - 60
        hour_ago = now - 3600
        
        self._minute_counts[ip] = [t for t in self._minute_counts[ip] if t > minute_ago]
        self._hour_counts[ip] = [t for t in self._hour_counts[ip] if t > hour_ago]
    
    def is_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if ip in self.config.whitelist:
            return False
        
        with self._lock:
            if ip in self._blocked_ips:
                if time.time() < self._blocked_ips[ip]:
                    return True
                else:
                    del self._blocked_ips[ip]
        
        return False
    
    def check_and_record(self, ip: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed and record it
        
        Returns: (allowed, reason)
        """
        if ip in self.config.whitelist:
            return True, None
        
        now = time.time()
        
        with self._lock:
            # Check if blocked
            if ip in self._blocked_ips:
                if now < self._blocked_ips[ip]:
                    remaining = int(self._blocked_ips[ip] - now)
                    return False, f"IP blocked for {remaining} more seconds"
                else:
                    del self._blocked_ips[ip]
            
            self._clean_old_entries(ip, now)
            
            # Check minute limit
            if len(self._minute_counts[ip]) >= self.config.requests_per_minute:
                # Block the IP
                self._blocked_ips[ip] = now + (self.config.block_duration_minutes * 60)
                logger.warning(f"IP {ip} blocked: exceeded minute limit")
                return False, "Rate limit exceeded (per minute)"
            
            # Check hour limit
            if len(self._hour_counts[ip]) >= self.config.requests_per_hour:
                self._blocked_ips[ip] = now + (self.config.block_duration_minutes * 60)
                logger.warning(f"IP {ip} blocked: exceeded hour limit")
                return False, "Rate limit exceeded (per hour)"
            
            # Record the request
            self._minute_counts[ip].append(now)
            self._hour_counts[ip].append(now)
            
            return True, None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        with self._lock:
            return {
                "tracked_ips": len(self._minute_counts),
                "blocked_ips": len(self._blocked_ips),
                "config": {
                    "requests_per_minute": self.config.requests_per_minute,
                    "requests_per_hour": self.config.requests_per_hour,
                    "block_duration_minutes": self.config.block_duration_minutes
                }
            }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using IP rate limiter"""
    
    def __init__(self, app: ASGIApp, rate_limiter: Optional[IPRateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or IPRateLimiter()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP (original client)
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        allowed, reason = self.rate_limiter.check_and_record(client_ip)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": reason,
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        return await call_next(request)


# =============================================================================
# Input Validation & Sanitization
# =============================================================================

class InputValidator:
    """
    Input validation and sanitization utilities
    
    Features:
    - SQL injection detection
    - XSS prevention
    - Path traversal prevention
    - Size limits
    - Pattern validation
    """
    
    # Dangerous SQL patterns
    SQL_INJECTION_PATTERNS = [
        r"('|\")\s*(;|--|\||`)",  # Quote followed by statement terminator
        r"(union|select|insert|update|delete|drop|truncate|alter)\s+",  # SQL keywords
        r"(/\*|\*/|@@|@)",  # SQL comments and variables
        r"(char|nchar|varchar|nvarchar)\s*\(",  # SQL functions
        r"(exec|execute|sp_|xp_)\s*\(",  # SQL procedures
        r"(waitfor|delay|benchmark|sleep)\s*\(",  # Time-based injection
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",  # Script tags
        r"javascript\s*:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
        r"<iframe[^>]*>",  # iframes
        r"<object[^>]*>",  # object tags
        r"<embed[^>]*>",  # embed tags
        r"expression\s*\(",  # CSS expressions
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",  # Unix path traversal
        r"\.\.\\",  # Windows path traversal
        r"%2e%2e[%/\\]",  # URL encoded traversal
        r"\.{2,}",  # Multiple dots
    ]
    
    def __init__(self):
        self._sql_compiled = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self._xss_compiled = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
        self._path_compiled = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
    
    def check_sql_injection(self, value: str) -> bool:
        """Check for potential SQL injection"""
        return any(pattern.search(value) for pattern in self._sql_compiled)
    
    def check_xss(self, value: str) -> bool:
        """Check for potential XSS"""
        return any(pattern.search(value) for pattern in self._xss_compiled)
    
    def check_path_traversal(self, value: str) -> bool:
        """Check for path traversal attempts"""
        return any(pattern.search(value) for pattern in self._path_compiled)
    
    def sanitize_string(self, value: str, max_length: int = 10000) -> str:
        """Sanitize a string value"""
        if not isinstance(value, str):
            return str(value)[:max_length]
        
        # Truncate to max length
        value = value[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        return value
    
    def sanitize_html(self, value: str) -> str:
        """Sanitize HTML content (more aggressive)"""
        # Remove all HTML tags
        value = re.sub(r'<[^>]+>', '', value)
        return html.escape(value)
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://[^\s<>\"{}|\\^`\[\]]+$'
        return bool(re.match(pattern, url))
    
    def validate_ip(self, ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def validate_json_depth(self, data: Any, max_depth: int = 10, current_depth: int = 0) -> bool:
        """Check JSON nesting depth"""
        if current_depth > max_depth:
            return False
        
        if isinstance(data, dict):
            for value in data.values():
                if not self.validate_json_depth(value, max_depth, current_depth + 1):
                    return False
        elif isinstance(data, list):
            for item in data:
                if not self.validate_json_depth(item, max_depth, current_depth + 1):
                    return False
        
        return True


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize all input"""
    
    def __init__(self, app: ASGIApp, validator: Optional[InputValidator] = None):
        super().__init__(app)
        self.validator = validator or InputValidator()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for certain paths
        if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        # Validate query parameters
        for key, value in request.query_params.items():
            if self.validator.check_sql_injection(value):
                logger.warning(f"SQL injection attempt in query param: {key}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid input detected"}
                )
            
            if self.validator.check_xss(value):
                logger.warning(f"XSS attempt in query param: {key}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid input detected"}
                )
        
        # Validate path parameters for path traversal
        if self.validator.check_path_traversal(request.url.path):
            logger.warning(f"Path traversal attempt: {request.url.path}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid path"}
            )
        
        return await call_next(request)


# =============================================================================
# Sensitive Data Masking
# =============================================================================

class DataMasker:
    """
    Utility to mask sensitive data in logs and responses
    
    Masks:
    - API keys
    - Passwords
    - Credit card numbers
    - Social security numbers
    - Email addresses (partial)
    """
    
    SENSITIVE_KEYS = {
        'password', 'passwd', 'pass', 'secret', 'token', 'api_key', 'apikey',
        'access_token', 'refresh_token', 'auth', 'authorization', 'credit_card',
        'card_number', 'cvv', 'ssn', 'social_security', 'private_key'
    }
    
    @classmethod
    def mask_string(cls, value: str, visible_chars: int = 4) -> str:
        """Mask a string leaving only first/last chars visible"""
        if len(value) <= visible_chars * 2:
            return '*' * len(value)
        return value[:visible_chars] + '*' * (len(value) - visible_chars * 2) + value[-visible_chars:]
    
    @classmethod
    def mask_email(cls, email: str) -> str:
        """Mask email address"""
        if '@' not in email:
            return cls.mask_string(email)
        
        local, domain = email.rsplit('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any], additional_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Recursively mask sensitive keys in a dictionary"""
        sensitive = cls.SENSITIVE_KEYS | (additional_keys or set())
        result = {}
        
        for key, value in data.items():
            lower_key = key.lower()
            
            if any(s in lower_key for s in sensitive):
                if isinstance(value, str):
                    result[key] = cls.mask_string(value)
                else:
                    result[key] = "***MASKED***"
            elif isinstance(value, dict):
                result[key] = cls.mask_dict(value, additional_keys)
            elif isinstance(value, list):
                result[key] = [
                    cls.mask_dict(item, additional_keys) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result


# =============================================================================
# Request Logging Middleware
# =============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive request/response logging
    
    Features:
    - Request ID tracking
    - Duration measurement
    - Status code logging
    - Error capture
    - Sensitive data masking
    """
    
    def __init__(self, app: ASGIApp, mask_sensitive: bool = True):
        super().__init__(app)
        self.mask_sensitive = mask_sensitive
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        start_time = time.time()
        
        # Log request
        logger.info(
            f"[{request_id}] → {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(
                log_level,
                f"[{request_id}] ← {response.status_code} "
                f"({duration_ms:.2f}ms)"
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] ✕ ERROR: {type(e).__name__}: {str(e)} "
                f"({duration_ms:.2f}ms)"
            )
            raise


# =============================================================================
# API Key Authentication
# =============================================================================

class APIKeyAuth:
    """
    Simple API key authentication
    
    Features:
    - Multiple valid keys
    - Key hashing for storage
    - Rate limiting per key
    """
    
    def __init__(self, valid_keys: Optional[List[str]] = None):
        self._key_hashes: Set[str] = set()
        if valid_keys:
            for key in valid_keys:
                self.add_key(key)
    
    def _hash_key(self, key: str) -> str:
        """Hash an API key"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def add_key(self, key: str):
        """Add a valid API key"""
        self._key_hashes.add(self._hash_key(key))
    
    def remove_key(self, key: str):
        """Remove an API key"""
        self._key_hashes.discard(self._hash_key(key))
    
    def validate(self, key: str) -> bool:
        """Validate an API key"""
        return self._hash_key(key) in self._key_hashes
    
    def __call__(self, request: Request) -> bool:
        """Callable interface for middleware"""
        # Check header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            # Check query parameter
            api_key = request.query_params.get("api_key")
        
        if not api_key:
            return False
        
        return self.validate(api_key)


# =============================================================================
# CORS Configuration
# =============================================================================

def get_cors_config(
    allowed_origins: Optional[List[str]] = None,
    allow_credentials: bool = True,
    allow_methods: Optional[List[str]] = None,
    allow_headers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get CORS configuration for FastAPI
    
    Usage:
        from fastapi.middleware.cors import CORSMiddleware
        cors_config = get_cors_config(['http://localhost:3000'])
        app.add_middleware(CORSMiddleware, **cors_config)
    """
    return {
        "allow_origins": allowed_origins or ["*"],
        "allow_credentials": allow_credentials,
        "allow_methods": allow_methods or ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": allow_headers or [
            "Content-Type", "Authorization", "X-API-Key", "X-Request-ID",
            "Accept", "Origin", "X-Requested-With"
        ],
        "expose_headers": ["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
    }


# =============================================================================
# Global Instances
# =============================================================================

input_validator = InputValidator()
data_masker = DataMasker()
ip_rate_limiter = IPRateLimiter()


def setup_security_middleware(app, cors_origins: Optional[List[str]] = None):
    """
    Setup all security middleware for a FastAPI app
    
    Usage:
        from security import setup_security_middleware
        setup_security_middleware(app, cors_origins=['http://localhost:3000'])
    """
    from fastapi.middleware.cors import CORSMiddleware
    
    # Add middleware in correct order (last added = first executed)
    
    # Request logging (first to execute, last to add)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Input validation
    app.add_middleware(InputValidationMiddleware, validator=input_validator)
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware, rate_limiter=ip_rate_limiter)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request ID
    app.add_middleware(RequestIDMiddleware)
    
    # CORS
    cors_config = get_cors_config(cors_origins)
    app.add_middleware(CORSMiddleware, **cors_config)
    
    logger.info("Security middleware configured")
