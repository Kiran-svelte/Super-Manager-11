"""
Security Tests - Test for common vulnerabilities
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInputValidation:
    """Test input validation and sanitization"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    
    def test_sql_injection_protection(self, client):
        """Test SQL injection attempts are handled"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "'; DELETE FROM tasks WHERE '1'='1"
        ]
        
        for payload in malicious_inputs:
            response = client.post("/api/agent/process", json={
                "message": payload,
                "user_id": "test"
            })
            # Should not crash the server
            assert response.status_code != 500
    
    def test_xss_protection(self, client):
        """Test XSS payloads are handled"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>"
        ]
        
        for payload in xss_payloads:
            response = client.post("/api/agent/process", json={
                "message": payload,
                "user_id": "test"
            })
            # Should handle gracefully
            assert response.status_code != 500
    
    def test_path_traversal_protection(self, client):
        """Test path traversal attempts are blocked"""
        traversal_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for payload in traversal_payloads:
            response = client.get(f"/api/tasks/{payload}")
            # Should not expose filesystem
            assert response.status_code in [400, 404, 422]


class TestAuthenticationSecurity:
    """Test authentication-related security"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    
    def test_endpoints_accept_valid_requests(self, client):
        """Test endpoints work with valid requests"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_missing_user_id_handled(self, client):
        """Test requests without user_id are handled"""
        response = client.post("/api/agent/process", json={
            "message": "Hello"
            # Missing user_id
        })
        # Should return validation error, not crash
        assert response.status_code in [200, 400, 422]


class TestCORSSecurity:
    """Test CORS configuration"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    
    def test_cors_allowed_origins(self, client):
        """Test CORS allows configured origins"""
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173"
        ]
        
        for origin in allowed_origins:
            response = client.options(
                "/api/health",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET"
                }
            )
            # Should be allowed
            assert response.status_code in [200, 204]


class TestSecretsExposure:
    """Test that secrets are not exposed"""
    
    def test_env_file_not_committed(self):
        """Test .env is in .gitignore"""
        gitignore_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".gitignore"
        )
        
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                content = f.read()
            assert ".env" in content, ".env should be in .gitignore"
    
    def test_api_keys_not_in_code(self):
        """Test API keys are not hardcoded in source files"""
        dangerous_patterns = [
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI key pattern
            r'gsk_[a-zA-Z0-9]{20,}',  # Groq key pattern
            r'password\s*=\s*["\'][^"\']{8,}["\']',  # Hardcoded passwords
        ]
        
        source_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
        
        for root, dirs, files in os.walk(source_dir):
            # Skip __pycache__ and node_modules
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git']]
            
            for file in files:
                if file.endswith('.py') and file != '.env':
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern in dangerous_patterns:
                        matches = re.findall(pattern, content)
                        # Filter out example/placeholder patterns
                        real_matches = [m for m in matches if 'example' not in m.lower() and 'placeholder' not in m.lower()]
                        assert len(real_matches) == 0, f"Potential secret found in {filepath}"
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    
    def test_error_messages_no_secrets(self, client):
        """Test error messages don't expose secrets"""
        # Trigger an error
        response = client.get("/api/nonexistent")
        
        if response.status_code >= 400:
            response_text = response.text.lower()
            # Should not contain sensitive info
            assert "api_key" not in response_text
            assert "password" not in response_text
            assert "secret" not in response_text


class TestRateLimiting:
    """Test rate limiting (if implemented)"""
    
    @pytest.fixture
    def client(self):
        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    
    def test_rapid_requests_handled(self, client):
        """Test rapid requests don't crash the server"""
        # Send 20 rapid requests
        for i in range(20):
            response = client.get("/api/health")
            # Should handle all requests
            assert response.status_code == 200
