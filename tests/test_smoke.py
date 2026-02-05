"""
Smoke Tests - Basic startup and health verification
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSmokeBasic:
    """Basic smoke tests that don't require full app startup"""
    
    def test_imports(self):
        """Test that all main modules can be imported"""
        # Core imports
        from backend import main
        from backend.core import agent
        from backend.core import intent_classifier
        from backend.core import plugins
        
        assert main is not None
        assert agent is not None
    
    def test_ai_providers_import(self):
        """Test AI providers can be imported"""
        from backend.core.ai_providers import base_provider
        from backend.core.ai_providers import router
        from backend.core.ai_providers import ollama_provider
        from backend.core.ai_providers import groq_provider
        
        assert base_provider.BaseAIProvider is not None
        assert router.AIRouter is not None
    
    def test_realtime_import(self):
        """Test realtime module imports"""
        from backend.core.realtime import websocket_manager
        
        assert websocket_manager.ConnectionManager is not None
        assert websocket_manager.EventType is not None
    
    def test_database_import(self):
        """Test database module can be imported"""
        try:
            from backend import database_supabase
            assert True
        except ImportError as e:
            # Supabase not installed is acceptable
            assert "supabase" in str(e).lower()


class TestSmokeAPI:
    """API smoke tests using TestClient"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        # Import here to avoid startup issues
        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    
    def test_root_endpoint(self, client):
        """Test root endpoint responds"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "operational"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_status_endpoint(self, client):
        """Test status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "2.0.0"
    
    def test_docs_available(self, client):
        """Test API documentation is accessible"""
        response = client.get("/api/docs")
        assert response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # Should not get 405 Method Not Allowed
        assert response.status_code in [200, 204]


class TestConfiguration:
    """Test configuration and environment"""
    
    def test_env_file_exists(self):
        """Test .env file exists"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        # Either .env or backend/.env should exist
        backend_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", ".env")
        assert os.path.exists(env_path) or os.path.exists(backend_env), "No .env file found"
    
    def test_requirements_exist(self):
        """Test requirements.txt exists"""
        req_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "requirements.txt")
        assert os.path.exists(req_path), "requirements.txt not found"
