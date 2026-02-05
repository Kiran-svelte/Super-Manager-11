"""
Pytest Configuration and Fixtures
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_messages():
    """Sample messages for AI testing"""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in exactly 5 words."}
    ]


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "user_id": "test-user-123",
        "intent": "Send an email to john@example.com about the meeting tomorrow",
        "context": {
            "user_name": "Test User",
            "user_email": "test@example.com"
        }
    }
