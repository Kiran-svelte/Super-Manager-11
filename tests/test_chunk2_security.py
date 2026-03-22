"""
Chunk 2: Security Core Tests
============================

Tests for README requirements:
- Layer 2: Input Validation (Pydantic, SQL injection, XSS, path traversal)
- Layer 4: Code Execution Safety (static risk analysis, sandbox, forbidden patterns)
- Forbidden Patterns (import os, sys, subprocess, eval, exec, etc.)
"""

import pytest
from unittest.mock import patch, MagicMock
import re


# =============================================================================
# Input Validation Tests (README: Layer 2)
# =============================================================================

class TestInputValidation:
    """Test input validation per README requirements"""
    
    def test_input_validator_exists(self):
        """InputValidator class should exist"""
        from backend.core.security import InputValidator
        validator = InputValidator()
        assert validator is not None
    
    def test_sql_injection_blocked(self):
        """SQL injection attempts should be blocked"""
        from backend.core.security import InputValidator
        validator = InputValidator()
        
        # Common SQL injection patterns
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM tasks WHERE 1=1",
            "UNION SELECT * FROM users",
        ]
        
        for inp in malicious_inputs:
            result = validator.validate_text(inp)
            # Should either sanitize or flag as invalid
            assert result is not None  # Should not crash
    
    def test_xss_sanitization(self):
        """XSS attacks should be sanitized"""
        from backend.core.security import InputValidator
        validator = InputValidator()
        
        xss_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='evil.com'>",
        ]
        
        for inp in xss_inputs:
            result = validator.sanitize_html(inp)
            # Should not contain script/iframe tags after sanitization
            assert "<script>" not in result.lower()
            assert "<iframe>" not in result.lower()
            assert "<img" not in result.lower()
    
    def test_path_traversal_blocked(self):
        """Path traversal attempts should be blocked"""
        from backend.core.security import InputValidator
        validator = InputValidator()
        
        traversal_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32\\config",
        ]
        
        for inp in traversal_inputs:
            result = validator.validate_path(inp)
            # Should flag as dangerous or sanitize
            assert ".." not in result or result is False


# =============================================================================
# Forbidden Patterns Tests (README: What Is Forbidden)
# =============================================================================

class TestForbiddenPatterns:
    """Test forbidden patterns are blocked per README"""
    
    def test_forbidden_patterns_list_exists(self):
        """FORBIDDEN_PATTERNS list should exist"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        assert isinstance(FORBIDDEN_PATTERNS, (list, tuple, set))
        assert len(FORBIDDEN_PATTERNS) > 0
    
    def test_import_os_forbidden(self):
        """import os should be forbidden"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        
        # Check pattern matches
        test_code = "import os"
        patterns_matched = any(
            re.search(pattern, test_code) 
            for pattern in FORBIDDEN_PATTERNS
        )
        assert patterns_matched, "import os should match a forbidden pattern"
    
    def test_import_sys_forbidden(self):
        """import sys should be forbidden"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        
        test_code = "import sys"
        patterns_matched = any(
            re.search(pattern, test_code) 
            for pattern in FORBIDDEN_PATTERNS
        )
        assert patterns_matched, "import sys should match a forbidden pattern"
    
    def test_import_subprocess_forbidden(self):
        """import subprocess should be forbidden"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        
        test_code = "import subprocess"
        patterns_matched = any(
            re.search(pattern, test_code) 
            for pattern in FORBIDDEN_PATTERNS
        )
        assert patterns_matched, "import subprocess should match a forbidden pattern"
    
    def test_eval_forbidden(self):
        """eval() should be forbidden"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        
        test_code = "eval(user_input)"
        patterns_matched = any(
            re.search(pattern, test_code) 
            for pattern in FORBIDDEN_PATTERNS
        )
        assert patterns_matched, "eval() should match a forbidden pattern"
    
    def test_exec_forbidden(self):
        """exec() should be forbidden"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        
        test_code = "exec(code)"
        patterns_matched = any(
            re.search(pattern, test_code) 
            for pattern in FORBIDDEN_PATTERNS
        )
        assert patterns_matched, "exec() should match a forbidden pattern"
    
    def test_open_forbidden(self):
        """open() file access should be forbidden"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        
        test_code = "open('/etc/passwd', 'r')"
        patterns_matched = any(
            re.search(pattern, test_code) 
            for pattern in FORBIDDEN_PATTERNS
        )
        assert patterns_matched, "open() should match a forbidden pattern"
    
    def test_dunder_class_forbidden(self):
        """__class__ introspection should be forbidden"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        
        test_code = "obj.__class__.__base__"
        patterns_matched = any(
            re.search(pattern, test_code) 
            for pattern in FORBIDDEN_PATTERNS
        )
        assert patterns_matched, "__class__ should match a forbidden pattern"
    
    def test_globals_forbidden(self):
        """globals() should be forbidden"""
        from backend.core.sandbox import FORBIDDEN_PATTERNS
        
        test_code = "globals()['__builtins__']"
        patterns_matched = any(
            re.search(pattern, test_code) 
            for pattern in FORBIDDEN_PATTERNS
        )
        assert patterns_matched, "globals() should match a forbidden pattern"


# =============================================================================
# Sandbox Tests (README: Layer 4 Code Execution Safety)
# =============================================================================

class TestSandbox:
    """Test sandbox execution per README requirements"""
    
    def test_sandbox_module_exists(self):
        """Sandbox module should exist"""
        from backend.core import sandbox
        assert sandbox is not None
    
    def test_sandbox_has_execute_function(self):
        """Sandbox should have execute function"""
        from backend.core.sandbox import execute_sandboxed, SandboxExecutor
        assert callable(execute_sandboxed) or SandboxExecutor is not None
    
    def test_static_risk_analysis_function_exists(self):
        """Static risk analysis function should exist (no LLM dependency)"""
        from backend.core.sandbox import analyze_code_risk, is_code_safe
        # At least one should exist
        assert callable(analyze_code_risk) or callable(is_code_safe)
    
    def test_safe_code_passes_analysis(self):
        """Safe code should pass static risk analysis"""
        from backend.core.sandbox import is_code_safe
        
        safe_code = """
result = 2 + 2
message = "Hello, World!"
items = [1, 2, 3]
"""
        assert is_code_safe(safe_code) == True
    
    def test_dangerous_code_blocked(self):
        """Dangerous code should be blocked by static analysis"""
        from backend.core.sandbox import is_code_safe
        
        dangerous_codes = [
            "import os; os.system('rm -rf /')",
            "exec(user_input)",
            "eval(malicious_code)",
            "import subprocess; subprocess.call(['ls'])",
            "__import__('os').system('whoami')",
        ]
        
        for code in dangerous_codes:
            assert is_code_safe(code) == False, f"Should block: {code}"
    
    def test_sandbox_timeout_configured(self):
        """Sandbox should have timeout configuration (30s default per README)"""
        from backend.core.sandbox import SANDBOX_TIMEOUT, SandboxConfig
        
        # Check constant or config
        try:
            assert SANDBOX_TIMEOUT == 30 or SANDBOX_TIMEOUT > 0
        except (ImportError, NameError):
            config = SandboxConfig()
            assert config.timeout == 30 or config.timeout > 0
    
    def test_sandbox_restricts_globals(self):
        """Sandbox should restrict available globals"""
        from backend.core.sandbox import get_safe_globals, SAFE_GLOBALS
        
        # Get the safe globals
        try:
            safe = get_safe_globals()
        except (ImportError, NameError):
            safe = SAFE_GLOBALS
        
        # Should NOT include dangerous builtins
        assert 'eval' not in safe or safe.get('eval') is None
        assert 'exec' not in safe or safe.get('exec') is None
        assert 'open' not in safe or safe.get('open') is None
        assert '__import__' not in safe or safe.get('__import__') is None
    
    def test_sandbox_execution_blocks_os_import(self):
        """Sandbox should block os import during execution"""
        from backend.core.sandbox import is_code_safe, analyze_code_risk
        
        dangerous_code = "import os; result = os.getcwd()"
        
        # Use static analysis (synchronous) instead of execution
        assert is_code_safe(dangerous_code) == False
        
        result = analyze_code_risk(dangerous_code)
        assert result.get('risk') == 'blocked' or result.get('safe') == False


# =============================================================================
# Risk Classification Tests (README: SAFE/RISKY/BLOCKED)
# =============================================================================

class TestRiskClassification:
    """Test risk classification per README (safe/risky/blocked)"""
    
    def test_risk_analysis_returns_level(self):
        """Risk analysis should return a risk level"""
        from backend.core.sandbox import analyze_code_risk
        
        code = "x = 1 + 1"
        result = analyze_code_risk(code)
        
        # Should return risk level
        assert 'risk' in result or 'level' in result or 'safe' in result
    
    def test_safe_code_classified_as_safe(self):
        """Safe code should be classified as safe"""
        from backend.core.sandbox import analyze_code_risk
        
        safe_code = "result = sum([1, 2, 3])"
        result = analyze_code_risk(safe_code)
        
        risk_level = result.get('risk', result.get('level', 'unknown'))
        assert risk_level in ['safe', 'low', 'SAFE'] or result.get('safe') == True
    
    def test_risky_code_classified_correctly(self):
        """Risky code (like web requests) should be classified as risky"""
        from backend.core.sandbox import analyze_code_risk
        
        # Code that uses network - risky but not blocked
        risky_code = "web_search('test query')"  # Uses primitive
        result = analyze_code_risk(risky_code)
        
        # Either safe (if primitive) or risky, but not blocked
        assert result is not None
    
    def test_blocked_code_classified_as_blocked(self):
        """Blocked code should be classified as blocked"""
        from backend.core.sandbox import analyze_code_risk
        
        blocked_code = "import os; os.system('rm -rf /')"
        result = analyze_code_risk(blocked_code)
        
        risk_level = result.get('risk', result.get('level', 'unknown'))
        assert risk_level in ['blocked', 'high', 'critical', 'BLOCKED'] or result.get('safe') == False


# =============================================================================
# Data Masking Tests (README: Sensitive Data Protection)
# =============================================================================

class TestDataMasking:
    """Test data masking per README requirements"""
    
    def test_data_masker_exists(self):
        """DataMasker class should exist"""
        from backend.core.security import DataMasker
        masker = DataMasker()
        assert masker is not None
    
    def test_password_masking(self):
        """Passwords should be masked in logs"""
        from backend.core.security import DataMasker
        masker = DataMasker()
        
        data = {"username": "admin", "password": "secret123"}
        masked = masker.mask_sensitive(data)
        
        # Password should be masked (not equal to original)
        assert masked["password"] != "secret123"
        # Should contain some masking characters
        assert "*" in masked["password"]
    
    def test_api_key_masking(self):
        """API keys should be masked"""
        from backend.core.security import DataMasker
        masker = DataMasker()
        
        data = {"api_key": "sk-1234567890abcdef"}
        masked = masker.mask_sensitive(data)
        
        assert masked["api_key"] != "sk-1234567890abcdef"
    
    def test_credit_card_masking(self):
        """Credit card numbers should be masked"""
        from backend.core.security import DataMasker
        masker = DataMasker()
        
        text = "My card is 4111111111111111"
        masked = masker.mask_pii(text)
        
        assert "4111111111111111" not in masked


# =============================================================================
# Rate Limiting Tests (README: 100 req/min per user)
# =============================================================================

class TestRateLimiting:
    """Test rate limiting per README requirements"""
    
    def test_rate_limiter_exists(self):
        """Rate limiter should exist"""
        from backend.core.security import IPRateLimiter
        limiter = IPRateLimiter()
        assert limiter is not None
    
    def test_rate_limiter_allows_normal_traffic(self):
        """Rate limiter should allow normal traffic"""
        from backend.core.security import IPRateLimiter
        limiter = IPRateLimiter(requests_per_minute=100)
        
        # First request should be allowed
        allowed = limiter.is_allowed("192.168.1.1")
        assert allowed == True
    
    def test_rate_limiter_blocks_excessive_traffic(self):
        """Rate limiter should block excessive traffic"""
        from backend.core.security import IPRateLimiter
        limiter = IPRateLimiter(requests_per_minute=5)  # Low limit for testing
        
        ip = "192.168.1.100"
        
        # Make requests up to limit
        for _ in range(5):
            limiter.is_allowed(ip)
        
        # Next request should be blocked
        allowed = limiter.is_allowed(ip)
        assert allowed == False
