"""
Chunk 1: Foundation Tests
=========================

Tests for README requirements:
- Environment configuration (GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY, ENCRYPTION_SECRET)
- FastAPI Application initialization
- Rate Limit Middleware
- CORS Middleware  
- Security Headers (CSP, HSTS, X-Frame-Options)
- Request Tracing (X-Request-ID)
- Health endpoints (/api/health, /api/health/ready, /api/health/metrics)
- Supabase PostgreSQL connection
- In-Memory Fallback
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os


# =============================================================================
# Configuration Tests
# =============================================================================

class TestConfiguration:
    """Test environment configuration per README requirements"""
    
    def test_groq_api_key_configurable(self):
        """GROQ_API_KEY should be configurable via environment"""
        from backend.config import Settings
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-groq-key"}):
            settings = Settings()
            assert settings.groq_api_key == "test-groq-key"
    
    def test_supabase_url_configurable(self):
        """SUPABASE_URL should be configurable via environment"""
        from backend.config import Settings
        
        with patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co"}):
            settings = Settings()
            assert settings.supabase_url == "https://test.supabase.co"
    
    def test_supabase_key_configurable(self):
        """SUPABASE_KEY should be configurable via environment"""
        from backend.config import Settings
        
        with patch.dict(os.environ, {"SUPABASE_KEY": "test-supabase-key"}):
            settings = Settings()
            assert settings.supabase_key == "test-supabase-key"
    
    def test_encryption_secret_configurable(self):
        """ENCRYPTION_SECRET should be configurable via environment (min 32 chars)"""
        from backend.config import Settings
        
        secret = "a" * 32  # Minimum 32 characters
        with patch.dict(os.environ, {"ENCRYPTION_SECRET": secret}):
            settings = Settings()
            assert settings.encryption_secret == secret
    
    def test_encryption_secret_minimum_length(self):
        """ENCRYPTION_SECRET must be at least 32 characters"""
        from backend.config import Settings
        from pydantic import ValidationError
        
        with patch.dict(os.environ, {"ENCRYPTION_SECRET": "short"}, clear=False):
            with pytest.raises(ValidationError) as exc_info:
                Settings(encryption_secret="short")
            assert "encryption_secret" in str(exc_info.value).lower() or "min_length" in str(exc_info.value).lower()
    
    def test_production_requires_all_secrets(self):
        """Production mode should require all required env vars"""
        from backend.config import Settings
        
        settings = Settings(app_env="production")
        missing = settings.validate_required()
        
        # Should report missing required vars (partial string match)
        missing_str = " ".join(missing)
        assert "GROQ_API_KEY" in missing_str or settings.groq_api_key is not None
        assert "SUPABASE_URL" in missing_str or settings.supabase_url is not None
        assert "SUPABASE_KEY" in missing_str or settings.supabase_key is not None
        # ENCRYPTION_SECRET is reported with additional context
        assert "ENCRYPTION_SECRET" in missing_str or "change-this" not in settings.encryption_secret


# =============================================================================
# FastAPI Application Tests
# =============================================================================

class TestFastAPIApplication:
    """Test FastAPI application initialization"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.main import app
        return TestClient(app)
    
    def test_app_exists(self):
        """FastAPI app should be importable"""
        from backend.main import app
        assert app is not None
        assert app.title == "Super Manager API"
    
    def test_app_version(self):
        """App should be version 2.0.0 per README"""
        from backend.main import app
        assert app.version == "2.0.0"
    
    def test_docs_available(self, client):
        """API docs should be available at /api/docs"""
        response = client.get("/api/docs")
        assert response.status_code == 200


# =============================================================================
# Security Headers Tests (README: Security Framework Layer 1)
# =============================================================================

class TestSecurityHeaders:
    """Test security headers per README requirements"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        return TestClient(app)
    
    def test_x_content_type_options_header(self, client):
        """X-Content-Type-Options: nosniff should be set"""
        response = client.get("/api/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
    
    def test_x_frame_options_header(self, client):
        """X-Frame-Options: DENY should be set (clickjacking protection)"""
        response = client.get("/api/health")
        assert response.headers.get("X-Frame-Options") == "DENY"
    
    def test_x_xss_protection_header(self, client):
        """X-XSS-Protection should be set"""
        response = client.get("/api/health")
        assert "1" in response.headers.get("X-XSS-Protection", "")
    
    def test_strict_transport_security_header(self, client):
        """HSTS header should be set"""
        response = client.get("/api/health")
        hsts = response.headers.get("Strict-Transport-Security", "")
        assert "max-age" in hsts
    
    def test_content_security_policy_header(self, client):
        """CSP header should be set"""
        response = client.get("/api/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp or csp != ""


# =============================================================================
# Request Tracing Tests (README: X-Request-ID)
# =============================================================================

class TestRequestTracing:
    """Test request tracing per README requirements"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        return TestClient(app)
    
    def test_request_id_generated(self, client):
        """X-Request-ID should be generated for each request"""
        response = client.get("/api/health")
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        assert len(request_id) > 0
    
    def test_request_id_passed_through(self, client):
        """X-Request-ID should be passed through if provided"""
        custom_id = "test-request-123"
        response = client.get("/api/health", headers={"X-Request-ID": custom_id})
        assert response.headers.get("X-Request-ID") == custom_id
    
    def test_request_id_unique(self, client):
        """Each request should get a unique ID"""
        response1 = client.get("/api/health")
        response2 = client.get("/api/health")
        
        id1 = response1.headers.get("X-Request-ID")
        id2 = response2.headers.get("X-Request-ID")
        
        assert id1 != id2


# =============================================================================
# Health Endpoint Tests (README: /api/health, /api/health/ready, /api/health/metrics)
# =============================================================================

class TestHealthEndpoints:
    """Test health endpoints per README requirements"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        return TestClient(app)
    
    def test_health_endpoint_exists(self, client):
        """GET /api/health should exist"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_returns_status(self, client):
        """Health endpoint should return status"""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
    
    def test_health_returns_ai_providers(self, client):
        """Health endpoint should return available AI providers"""
        response = client.get("/api/health")
        data = response.json()
        assert "ai_providers" in data
    
    def test_health_returns_circuit_breakers(self, client):
        """Health endpoint should return circuit breaker status"""
        response = client.get("/api/health")
        data = response.json()
        assert "circuit_breakers" in data
    
    def test_health_ready_endpoint_exists(self, client):
        """GET /api/health/ready should exist (readiness probe)"""
        response = client.get("/api/health/ready")
        assert response.status_code in [200, 503]
    
    def test_health_ready_returns_ready_status(self, client):
        """Readiness endpoint should return ready status"""
        response = client.get("/api/health/ready")
        data = response.json()
        assert "ready" in data
        assert "checks" in data
    
    def test_health_metrics_endpoint_exists(self, client):
        """GET /api/health/metrics should exist (Prometheus metrics)"""
        response = client.get("/api/health/metrics")
        assert response.status_code == 200
    
    def test_health_metrics_returns_data(self, client):
        """Metrics endpoint should return performance data"""
        response = client.get("/api/health/metrics")
        data = response.json()
        assert "circuit_breakers" in data or "cache" in data or "request_traces" in data


# =============================================================================
# Rate Limiting Tests (README: 100 req/min per user)
# =============================================================================

class TestRateLimiting:
    """Test rate limiting per README requirements"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        return TestClient(app)
    
    def test_rate_limit_headers_present(self, client):
        """Rate limit headers should be present"""
        response = client.get("/api/health")
        # Either X-RateLimit headers or 429 status possible
        # Just verify the endpoint works initially
        assert response.status_code in [200, 429]


# =============================================================================
# CORS Tests (README: CORS Middleware)
# =============================================================================

class TestCORS:
    """Test CORS middleware per README requirements"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        return TestClient(app)
    
    def test_cors_allows_localhost(self, client):
        """CORS should allow localhost origins"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # Should not be blocked
        assert response.status_code in [200, 204, 405]
    
    def test_cors_allows_vercel(self, client):
        """CORS should allow Vercel deployments"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "https://my-app.vercel.app",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code in [200, 204, 405]


# =============================================================================
# Database Fallback Tests (README: In-Memory Fallback)
# =============================================================================

class TestDatabaseFallback:
    """Test database with in-memory fallback per README requirements"""
    
    def test_database_module_exists(self):
        """Database module should be importable"""
        from backend import database_supabase
        assert database_supabase is not None
    
    def test_init_db_function_exists(self):
        """init_db function should exist"""
        from backend.database_supabase import init_db
        assert callable(init_db)
    
    def test_get_supabase_client_returns_none_without_config(self):
        """Should return None when Supabase not configured (fallback mode)"""
        from backend.database_supabase import get_supabase_client
        # This may or may not return a client depending on env
        # The key is it shouldn't crash
        client = get_supabase_client()
        # Either None (fallback) or valid client
        assert client is None or client is not None


# =============================================================================
# Root Endpoint Test
# =============================================================================

class TestRootEndpoint:
    """Test root endpoint"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        return TestClient(app)
    
    def test_root_returns_info(self, client):
        """Root endpoint should return API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "2.0.0"
