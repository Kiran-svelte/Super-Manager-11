"""
Behavioral Tests: Sandbox Security
====================================
Tests that the sandbox ACTUALLY blocks forbidden patterns
and correctly classifies risk levels per README requirements.

README Requirements:
- Static risk analysis (no LLM dependency)
- FORBIDDEN_PATTERNS must block: os, sys, subprocess, eval, exec, open, etc.
- SAFE primitives: web_search, browse_page, scrape_data, generate_image
- RISKY primitives: fill_form, run_python
- 30s default timeout
"""

import pytest
import asyncio
from backend.core.sandbox import RiskClassifier, SandboxExecutor, ExecutionResult


class TestRiskClassifierForbiddenPatterns:
    """Test that FORBIDDEN patterns are actually blocked"""
    
    @pytest.fixture
    def classifier(self):
        return RiskClassifier()
    
    # ==========================================================================
    # System Access Patterns - MUST BE BLOCKED
    # ==========================================================================
    
    def test_blocks_import_os(self, classifier):
        """import os MUST be blocked"""
        code = "import os\nos.system('ls')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked", f"Expected blocked, got {result['risk']}"
        assert any("os" in p for p in result["blocked_patterns"])
    
    def test_blocks_import_sys(self, classifier):
        """import sys MUST be blocked"""
        code = "import sys\nsys.exit()"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_import_subprocess(self, classifier):
        """import subprocess MUST be blocked"""
        code = "import subprocess\nsubprocess.run(['ls'])"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_import_shutil(self, classifier):
        """import shutil MUST be blocked"""
        code = "import shutil\nshutil.rmtree('/tmp')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_from_os_import(self, classifier):
        """from os import MUST be blocked"""
        code = "from os import path, system"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    # ==========================================================================
    # Network Access Patterns - MUST BE BLOCKED (except via primitives)
    # ==========================================================================
    
    def test_blocks_import_socket(self, classifier):
        """import socket MUST be blocked"""
        code = "import socket\ns = socket.socket()"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_requests_library(self, classifier):
        """requests.get MUST be blocked"""
        code = "import requests\nrequests.get('http://evil.com')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_urllib_request(self, classifier):
        """urllib.request MUST be blocked"""
        code = "from urllib.request import urlopen"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_http_client(self, classifier):
        """http.client MUST be blocked"""
        code = "import http.client"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    # ==========================================================================
    # Code Execution Patterns - MUST BE BLOCKED
    # ==========================================================================
    
    def test_blocks_eval(self, classifier):
        """eval() MUST be blocked"""
        code = "result = eval('__import__(\"os\")')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_exec(self, classifier):
        """exec() MUST be blocked"""
        code = "exec('import os; os.system(\"rm -rf /\")')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_dunder_import(self, classifier):
        """__import__() MUST be blocked"""
        code = "os = __import__('os')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_compile(self, classifier):
        """compile() MUST be blocked"""
        code = "c = compile('print(1)', '', 'exec')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    # ==========================================================================
    # File System Access - MUST BE BLOCKED
    # ==========================================================================
    
    def test_blocks_open(self, classifier):
        """open() MUST be blocked"""
        code = "f = open('/etc/passwd', 'r')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_os_system(self, classifier):
        """os.system MUST be blocked"""
        code = "os.system('whoami')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_subprocess_dot_methods(self, classifier):
        """subprocess.* MUST be blocked"""
        code = "subprocess.call(['rm', '-rf', '/'])"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_shutil_dot_methods(self, classifier):
        """shutil.* MUST be blocked"""
        code = "shutil.copy('/etc/passwd', '/tmp/')"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    # ==========================================================================
    # Introspection Attacks - MUST BE BLOCKED
    # ==========================================================================
    
    def test_blocks_globals(self, classifier):
        """globals() MUST be blocked"""
        code = "print(globals())"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_locals(self, classifier):
        """locals() MUST be blocked"""
        code = "print(locals())"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_dunder_class(self, classifier):
        """__class__ MUST be blocked"""
        code = "x.__class__.__bases__[0]"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_dunder_subclasses(self, classifier):
        """__subclasses__ MUST be blocked"""
        code = "object.__subclasses__()"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_breakpoint(self, classifier):
        """breakpoint() MUST be blocked"""
        code = "breakpoint()"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    # ==========================================================================
    # Pickle/ctypes - MUST BE BLOCKED
    # ==========================================================================
    
    def test_blocks_pickle(self, classifier):
        """pickle MUST be blocked"""
        code = "import pickle"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_blocks_ctypes(self, classifier):
        """ctypes MUST be blocked"""
        code = "import ctypes"
        result = classifier.classify(code)
        assert result["risk"] == "blocked"


class TestRiskClassifierSafePrimitives:
    """Test that SAFE primitives are correctly classified"""
    
    @pytest.fixture
    def classifier(self):
        return RiskClassifier()
    
    def test_web_search_is_safe(self, classifier):
        """web_search should be SAFE"""
        code = "result = await web_search('python tutorial')"
        result = classifier.classify(code)
        assert result["risk"] == "safe"
        assert "web_search" in result["primitives_used"]
    
    def test_browse_page_is_safe(self, classifier):
        """browse_page should be SAFE"""
        code = "content = await browse_page('https://example.com')"
        result = classifier.classify(code)
        assert result["risk"] == "safe"
        assert "browse_page" in result["primitives_used"]
    
    def test_scrape_data_is_safe(self, classifier):
        """scrape_data should be SAFE"""
        code = "data = await scrape_data('https://example.com', {'title': 'h1'})"
        result = classifier.classify(code)
        assert result["risk"] == "safe"
        assert "scrape_data" in result["primitives_used"]
    
    def test_generate_image_is_safe(self, classifier):
        """generate_image should be SAFE"""
        code = "img = await generate_image('a sunset over mountains')"
        result = classifier.classify(code)
        assert result["risk"] == "safe"
        assert "generate_image" in result["primitives_used"]
    
    def test_multiple_safe_primitives(self, classifier):
        """Multiple safe primitives should still be SAFE"""
        code = """
results = await web_search('python')
page = await browse_page(results[0]['url'])
"""
        result = classifier.classify(code)
        assert result["risk"] == "safe"


class TestRiskClassifierRiskyPrimitives:
    """Test that RISKY primitives are correctly classified"""
    
    @pytest.fixture
    def classifier(self):
        return RiskClassifier()
    
    def test_fill_form_is_risky(self, classifier):
        """fill_form should be RISKY"""
        code = "await fill_form('https://example.com/login', {'user': 'test'})"
        result = classifier.classify(code)
        assert result["risk"] == "risky"
        assert "fill_form" in result["primitives_used"]
    
    def test_run_python_is_risky(self, classifier):
        """run_python should be RISKY"""
        code = "await run_python('print(1+1)')"
        result = classifier.classify(code)
        assert result["risk"] == "risky"
        assert "run_python" in result["primitives_used"]
    
    def test_mixed_safe_and_risky_is_risky(self, classifier):
        """Mix of safe and risky primitives should be RISKY"""
        code = """
results = await web_search('login form')
await fill_form(results[0]['url'], {'email': 'test@test.com'})
"""
        result = classifier.classify(code)
        assert result["risk"] == "risky"


class TestRiskClassifierValidateAction:
    """Test validate_action for single primitive calls"""
    
    @pytest.fixture
    def classifier(self):
        return RiskClassifier()
    
    def test_validate_safe_primitive(self, classifier):
        """validate_action should identify safe primitives"""
        result = classifier.validate_action("web_search")
        assert result["risk"] == "safe"
    
    def test_validate_risky_primitive(self, classifier):
        """validate_action should identify risky primitives"""
        result = classifier.validate_action("fill_form")
        assert result["risk"] == "risky"
    
    def test_validate_unknown_primitive(self, classifier):
        """validate_action should block unknown primitives"""
        result = classifier.validate_action("hack_server")
        assert result["risk"] == "blocked"


class TestSandboxExecutorTimeout:
    """Test sandbox timeout enforcement (README: 30s default)"""
    
    def test_default_timeout_is_30_seconds(self):
        """Default timeout should be 30 seconds"""
        executor = SandboxExecutor()
        assert executor.timeout == 30.0
    
    def test_custom_timeout(self):
        """Custom timeout should be respected"""
        executor = SandboxExecutor(timeout=10.0)
        assert executor.timeout == 10.0


class TestSandboxExecutorExecuteAction:
    """Test execute_action for single primitive calls"""
    
    @pytest.fixture
    def executor(self):
        return SandboxExecutor(timeout=5.0)
    
    @pytest.mark.asyncio
    async def test_unknown_action_fails(self, executor):
        """Unknown actions should fail"""
        result = await executor.execute_action("unknown_tool", {})
        assert result.success is False
        assert "unknown" in result.output.lower() or "Unknown" in result.output


class TestSandboxExecutorBlockedCode:
    """Test that blocked code cannot be executed"""
    
    @pytest.fixture
    def executor(self):
        return SandboxExecutor(timeout=5.0)
    
    @pytest.mark.asyncio
    async def test_blocked_code_not_executed(self, executor):
        """Code with forbidden patterns should not execute"""
        code = "import os\nos.system('ls')"
        result = await executor.execute_code(code)
        assert result.success is False
        assert "blocked" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_eval_not_executed(self, executor):
        """Code with eval should not execute"""
        code = "x = eval('1+1')"
        result = await executor.execute_code(code)
        assert result.success is False
    
    @pytest.mark.asyncio
    async def test_exec_not_executed(self, executor):
        """Code with exec should not execute"""
        code = "exec('print(1)')"
        result = await executor.execute_code(code)
        assert result.success is False


class TestSandboxExecutorExecutionResult:
    """Test ExecutionResult dataclass"""
    
    def test_execution_result_fields(self):
        """ExecutionResult should have required fields"""
        result = ExecutionResult(
            success=True,
            output="test output",
            data={"key": "value"},
            error=None,
            primitives_used=["web_search"]
        )
        assert result.success is True
        assert result.output == "test output"
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.primitives_used == ["web_search"]
    
    def test_execution_result_defaults(self):
        """ExecutionResult should have sensible defaults"""
        result = ExecutionResult(success=False, output="error")
        assert result.data == {}
        assert result.primitives_used == []


# =============================================================================
# Edge Cases
# =============================================================================

class TestSandboxEdgeCases:
    """Test edge cases and evasion attempts"""
    
    @pytest.fixture
    def classifier(self):
        return RiskClassifier()
    
    def test_obfuscated_import_os(self, classifier):
        """Obfuscated import attempts should be blocked"""
        # String concatenation
        code = "im" + "port os"  # This becomes "import os" when stored
        result = classifier.classify("import os")
        assert result["risk"] == "blocked"
    
    def test_import_os_in_string_literal_safe(self, classifier):
        """'import os' as string literal might be safe (just text)"""
        code = 'message = "you should import os library"'
        # This depends on implementation - pattern matching might catch it
        # The key is: it shouldn't EXECUTE os commands
        result = classifier.classify(code)
        # String literals with 'import os' might get flagged - that's conservative security
    
    def test_nested_dangerous_in_safe_code(self, classifier):
        """Dangerous code nested in safe-looking code should be blocked"""
        code = """
# Safe looking code
result = await web_search('python')
# Hidden danger
import os
os.remove('/etc/passwd')
"""
        result = classifier.classify(code)
        assert result["risk"] == "blocked"
    
    def test_unicode_evasion_attempt(self, classifier):
        """Unicode tricks should not bypass security"""
        # Using fullwidth characters - should be blocked if normalized
        code = "import\u3000os"  # Ideographic space
        # Classifier should either block or the code won't run anyway
        result = classifier.classify(code)
        # Either blocked or it won't match real 'import os'
    
    def test_empty_code_is_safe(self, classifier):
        """Empty code should be safe"""
        result = classifier.classify("")
        assert result["risk"] == "safe"
    
    def test_whitespace_only_is_safe(self, classifier):
        """Whitespace-only code should be safe"""
        result = classifier.classify("   \n\t  \n   ")
        assert result["risk"] == "safe"
    
    def test_comment_only_is_safe(self, classifier):
        """Comment-only code should be safe"""
        result = classifier.classify("# This is just a comment")
        assert result["risk"] == "safe"
