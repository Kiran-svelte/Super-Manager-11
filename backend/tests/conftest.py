"""
Super Manager - Test Configuration
==================================

Pytest configuration and fixtures for testing the Super Manager application.
"""

import os
import sys
import pytest
import asyncio
from typing import Generator, Dict, Any
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Async Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Environment Configuration
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["APP_ENV"] = "testing"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["GROQ_API_KEY"] = "test-api-key"
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_KEY"] = "test-supabase-key"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
    yield
    # Cleanup if needed


# =============================================================================
# FastAPI Test Client
# =============================================================================

@pytest.fixture
def app():
    """Create FastAPI app instance"""
    from main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app):
    """Create test client"""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Create async test client"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock = MagicMock()
    
    # Mock table operations
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[])
    
    mock.table.return_value = mock_table
    
    return mock


@pytest.fixture
def mock_database():
    """Mock database connection"""
    with patch("database_supabase.get_supabase_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


# =============================================================================
# AI/LLM Fixtures
# =============================================================================

@pytest.fixture
def mock_groq_response():
    """Mock Groq API response"""
    return {
        "id": "chatcmpl-test-123",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from the AI."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70
        }
    }


@pytest.fixture
def mock_groq_client(mock_groq_response):
    """Mock Groq client"""
    with patch("core.brain.Groq") as mock:
        mock_instance = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="Test AI response"))
        ]
        mock_instance.chat.completions.create.return_value = mock_completion
        mock.return_value = mock_instance
        yield mock_instance


# =============================================================================
# User and Auth Fixtures
# =============================================================================

@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    return {
        "Authorization": "Bearer test-token-12345",
        "Content-Type": "application/json"
    }


# =============================================================================
# Request/Message Fixtures
# =============================================================================

@pytest.fixture
def sample_chat_request():
    """Sample chat request"""
    return {
        "message": "Hello, can you help me with a task?",
        "conversation_id": "conv-123",
        "user_id": "user-123"
    }


@pytest.fixture
def sample_email_request():
    """Sample email request"""
    return {
        "to": "recipient@example.com",
        "subject": "Test Email",
        "body": "This is a test email body.",
        "user_id": "user-123"
    }


@pytest.fixture
def sample_meeting_request():
    """Sample meeting request"""
    return {
        "title": "Test Meeting",
        "participants": ["user1@example.com", "user2@example.com"],
        "start_time": "2025-01-01T10:00:00Z",
        "duration_minutes": 60
    }


@pytest.fixture
def sample_task_request():
    """Sample task creation request"""
    return {
        "title": "Complete project documentation",
        "description": "Write comprehensive docs for the API",
        "priority": "high",
        "due_date": "2025-01-15T00:00:00Z"
    }


# =============================================================================
# Cache Fixtures
# =============================================================================

@pytest.fixture
def mock_cache():
    """Mock cache client"""
    cache_storage = {}
    
    mock = MagicMock()
    mock.get = lambda k, d=None: cache_storage.get(k, d)
    mock.set = lambda k, v, **kw: cache_storage.update({k: v})
    mock.delete = lambda k: cache_storage.pop(k, None)
    mock.clear = lambda: cache_storage.clear()
    
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch("core.cache.RedisCache") as mock:
        mock_instance = MagicMock()
        mock_instance.available = True
        mock.return_value = mock_instance
        yield mock_instance


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external API calls"""
    with patch("httpx.AsyncClient") as mock:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"status": "ok"})
        )
        mock_instance.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"success": True})
        )
        mock.return_value.__aenter__.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def capture_logs(caplog):
    """Capture log output for assertions"""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = 0
        
        def start(self):
            self.start_time = time.perf_counter()
            return self
        
        def stop(self):
            self.end_time = time.perf_counter()
            self.elapsed = self.end_time - self.start_time
            return self.elapsed
        
        def __enter__(self):
            self.start()
            return self
        
        def __exit__(self, *args):
            self.stop()
    
    return Timer


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Add any cleanup logic here
    pass
