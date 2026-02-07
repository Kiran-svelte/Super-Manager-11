"""
Input Validation & Sanitization Module
======================================

Comprehensive input validation for all API endpoints:
- Request body validation
- Email/URL/phone validation
- XSS/SQL injection prevention
- Input length limits
- Type coercion and normalization

Author: Super Manager
Version: 1.0.0
"""

import re
import html
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum


# =============================================================================
# Constants
# =============================================================================

MAX_MESSAGE_LENGTH = 10000
MAX_SESSION_ID_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MAX_NAME_LENGTH = 100
MAX_SUBJECT_LENGTH = 500
MIN_MESSAGE_LENGTH = 1

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'javascript:',  # JavaScript URLs
    r'on\w+\s*=',  # Event handlers
    r'data:[^;]+;base64',  # Data URLs with base64
    r'vbscript:',  # VBScript URLs
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b.*\b(FROM|INTO|SET|TABLE|DATABASE)\b)",
    r"(--|#|/\*|\*/)",  # SQL comments
    r"(\b(OR|AND)\b\s+[\w\d]+\s*=\s*[\w\d]+)",  # OR 1=1 style
]


# =============================================================================
# Validation Functions
# =============================================================================

def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML/JS from text"""
    if not text:
        return ""
    
    # HTML escape special characters
    sanitized = html.escape(text)
    
    # Remove dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized


def check_sql_injection(text: str) -> bool:
    """Check if text contains potential SQL injection"""
    if not text:
        return False
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    if not url:
        return False
    
    pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(pattern, url))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    
    # Remove common separators
    clean = re.sub(r'[\s\-\.\(\)]', '', phone)
    
    # Check if it's a valid number (10-15 digits, optionally starting with +)
    pattern = r'^\+?\d{10,15}$'
    return bool(re.match(pattern, clean))


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format"""
    if not session_id:
        return True  # Optional
    
    if len(session_id) > MAX_SESSION_ID_LENGTH:
        return False
    
    # Alphanumeric with hyphens and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, session_id))


def normalize_message(message: str) -> str:
    """Normalize and clean user message"""
    if not message:
        return ""
    
    # Strip whitespace
    message = message.strip()
    
    # Normalize unicode
    import unicodedata
    message = unicodedata.normalize('NFKC', message)
    
    # Remove null bytes
    message = message.replace('\x00', '')
    
    # Limit consecutive newlines
    message = re.sub(r'\n{3,}', '\n\n', message)
    
    return message


# =============================================================================
# Pydantic Models for Request Validation
# =============================================================================

class ChatRequest(BaseModel):
    """Chat message request validation"""
    message: str = Field(..., min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH)
    session_id: Optional[str] = Field(None, max_length=MAX_SESSION_ID_LENGTH)
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        
        # Normalize
        v = normalize_message(v)
        
        # Check for SQL injection
        if check_sql_injection(v):
            raise ValueError('Invalid message content')
        
        return v
    
    @validator('session_id')
    def validate_session(cls, v):
        if v and not validate_session_id(v):
            raise ValueError('Invalid session ID format')
        return v
    
    class Config:
        extra = 'forbid'  # No extra fields allowed


class EmailRequest(BaseModel):
    """Email sending request validation"""
    to: str = Field(..., max_length=MAX_EMAIL_LENGTH)
    subject: str = Field(..., min_length=1, max_length=MAX_SUBJECT_LENGTH)
    body: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    
    @validator('to')
    def validate_email_to(cls, v):
        if not validate_email(v):
            raise ValueError('Invalid email address')
        return v.lower()
    
    @validator('subject', 'body')
    def sanitize_content(cls, v):
        return sanitize_html(v)
    
    class Config:
        extra = 'forbid'


class MeetingRequest(BaseModel):
    """Meeting creation request validation"""
    title: str = Field(..., min_length=1, max_length=200)
    time: str = Field(..., min_length=1, max_length=100)
    participants: List[str] = Field(default_factory=list)
    description: Optional[str] = Field(None, max_length=2000)
    
    @validator('title')
    def sanitize_title(cls, v):
        return sanitize_html(v)
    
    @validator('participants')
    def validate_participants(cls, v):
        if not v:
            return []
        
        validated = []
        for p in v[:20]:  # Max 20 participants
            p = p.strip()
            if p and len(p) <= MAX_EMAIL_LENGTH:
                if '@' in p:
                    if validate_email(p):
                        validated.append(p.lower())
                else:
                    validated.append(sanitize_html(p))
        
        return validated
    
    class Config:
        extra = 'forbid'


class SearchRequest(BaseModel):
    """Search request validation"""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(5, ge=1, le=20)
    
    @validator('query')
    def validate_query(cls, v):
        v = normalize_message(v)
        
        if check_sql_injection(v):
            raise ValueError('Invalid search query')
        
        return v
    
    class Config:
        extra = 'forbid'


class TaskRequest(BaseModel):
    """Generic task request validation"""
    task_type: str = Field(..., min_length=1, max_length=50)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = Field(None, max_length=MAX_SESSION_ID_LENGTH)
    
    @validator('task_type')
    def validate_task_type(cls, v):
        allowed_types = [
            'email', 'meeting', 'reminder', 'payment', 
            'search', 'shopping', 'translate', 'summarize', 'other'
        ]
        v = v.lower().strip()
        if v not in allowed_types:
            v = 'other'
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v):
        # Deep sanitize all string values
        def sanitize_dict(d):
            if isinstance(d, dict):
                return {k: sanitize_dict(val) for k, val in d.items()}
            elif isinstance(d, list):
                return [sanitize_dict(item) for item in d]
            elif isinstance(d, str):
                return sanitize_html(d)
            return d
        
        return sanitize_dict(v)
    
    class Config:
        extra = 'forbid'


class FeedbackRequest(BaseModel):
    """User feedback request validation"""
    message_id: str = Field(..., min_length=1, max_length=100)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    
    @validator('message_id')
    def validate_message_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid message ID')
        return v
    
    @validator('comment')
    def sanitize_comment(cls, v):
        if v:
            return sanitize_html(v)
        return v
    
    class Config:
        extra = 'forbid'


class UserPreferencesRequest(BaseModel):
    """User preferences update validation"""
    name: Optional[str] = Field(None, max_length=MAX_NAME_LENGTH)
    email: Optional[str] = Field(None, max_length=MAX_EMAIL_LENGTH)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    
    @validator('email')
    def validate_email_field(cls, v):
        if v and not validate_email(v):
            raise ValueError('Invalid email address')
        return v.lower() if v else v
    
    @validator('name')
    def sanitize_name(cls, v):
        if v:
            return sanitize_html(v)
        return v
    
    @validator('timezone')
    def validate_timezone(cls, v):
        if v:
            # Basic timezone validation
            valid_patterns = [
                r'^[A-Z][a-z]+/[A-Z][a-z_]+$',  # America/New_York
                r'^UTC[+-]?\d{1,2}$',  # UTC+5
                r'^[A-Z]{2,4}$'  # EST, PST
            ]
            if not any(re.match(p, v) for p in valid_patterns):
                return 'UTC'
        return v
    
    @validator('language')
    def validate_language(cls, v):
        if v:
            # ISO 639-1 format
            if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', v):
                return 'en'
        return v
    
    class Config:
        extra = 'forbid'


# =============================================================================
# Validation Utilities
# =============================================================================

class ValidationError(Exception):
    """Custom validation error with details"""
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code or 'validation_error'
        super().__init__(message)
    
    def to_dict(self):
        return {
            'error': self.message,
            'field': self.field,
            'code': self.code
        }


def validate_request(model_class: type, data: Dict) -> BaseModel:
    """Validate request data against a model"""
    try:
        return model_class(**data)
    except Exception as e:
        # Extract field and message from Pydantic error
        error_msg = str(e)
        field = None
        
        if hasattr(e, 'errors') and callable(e.errors):
            errors = e.errors()
            if errors:
                field = errors[0].get('loc', [None])[-1]
                error_msg = errors[0].get('msg', str(e))
        
        raise ValidationError(error_msg, field=field)


# =============================================================================
# Rate Limit Tracking
# =============================================================================

class RateLimitTracker:
    """Track rate limits per identifier"""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
    
    def check(self, identifier: str) -> tuple:
        """
        Check if request is allowed
        Returns: (allowed, remaining, reset_time)
        """
        import time
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        if identifier in self._requests:
            self._requests[identifier] = [
                t for t in self._requests[identifier] if t > window_start
            ]
        else:
            self._requests[identifier] = []
        
        count = len(self._requests[identifier])
        remaining = max(0, self.max_requests - count)
        
        if count >= self.max_requests:
            reset_time = min(self._requests[identifier]) + self.window_seconds - now
            return False, 0, int(reset_time)
        
        # Record this request
        self._requests[identifier].append(now)
        return True, remaining - 1, 0
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        if identifier in self._requests:
            del self._requests[identifier]


# Singleton instances for different rate limits
chat_rate_limiter = RateLimitTracker(max_requests=30, window_seconds=60)  # 30 msgs/min
api_rate_limiter = RateLimitTracker(max_requests=100, window_seconds=60)  # 100 requests/min
