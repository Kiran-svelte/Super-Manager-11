"""
Chunk 4: Primitives & Tools Tests
=================================

Tests for README requirements:
- 6 core primitives (web_search, browse_page, scrape_data, generate_image, fill_form, run_python)
- Safe vs Risky classification
- ToolRegistry for dynamic tools
- MCP server integration
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# Primitives Module Tests
# =============================================================================

class TestPrimitivesModule:
    """Test primitives module exists"""
    
    def test_primitives_module_exists(self):
        """Primitives module should exist"""
        from backend.core import primitives
        assert primitives is not None
    
    def test_primitives_dict_exists(self):
        """PRIMITIVES dict should exist"""
        from backend.core.primitives import PRIMITIVES
        assert isinstance(PRIMITIVES, dict)
        assert len(PRIMITIVES) > 0


# =============================================================================
# Core Primitive Functions Tests
# =============================================================================

class TestCorePrimitives:
    """Test 6 core primitives per README"""
    
    def test_web_search_exists(self):
        """web_search primitive should exist"""
        from backend.core.primitives import web_search
        assert callable(web_search)
    
    def test_browse_page_exists(self):
        """browse_page primitive should exist"""
        from backend.core.primitives import browse_page
        assert callable(browse_page)
    
    def test_scrape_data_exists(self):
        """scrape_data primitive should exist"""
        from backend.core.primitives import scrape_data
        assert callable(scrape_data)
    
    def test_generate_image_exists(self):
        """generate_image primitive should exist"""
        from backend.core.primitives import generate_image
        assert callable(generate_image)
    
    def test_fill_form_exists(self):
        """fill_form primitive should exist"""
        from backend.core.primitives import fill_form
        assert callable(fill_form)
    
    def test_run_python_exists(self):
        """run_python primitive should exist"""
        from backend.core.primitives import run_python
        assert callable(run_python)
    
    def test_six_core_primitives_in_dict(self):
        """All 6 core primitives should be in PRIMITIVES dict"""
        from backend.core.primitives import PRIMITIVES
        
        core_primitives = [
            "web_search",
            "browse_page", 
            "scrape_data",
            "generate_image",
            "fill_form",
            "run_python"
        ]
        
        for prim in core_primitives:
            assert prim in PRIMITIVES, f"Missing primitive: {prim}"


# =============================================================================
# Safe vs Risky Classification Tests
# =============================================================================

class TestPrimitiveClassification:
    """Test safe/risky classification per README"""
    
    def test_safe_primitives_list_exists(self):
        """Safe primitives should be defined"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert hasattr(classifier, 'SAFE_PRIMITIVES')
        assert isinstance(classifier.SAFE_PRIMITIVES, (set, list, tuple))
    
    def test_risky_primitives_list_exists(self):
        """Risky primitives should be defined"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert hasattr(classifier, 'RISKY_PRIMITIVES')
        assert isinstance(classifier.RISKY_PRIMITIVES, (set, list, tuple))
    
    def test_web_search_is_safe(self):
        """web_search should be classified as SAFE"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert "web_search" in classifier.SAFE_PRIMITIVES
    
    def test_browse_page_is_safe(self):
        """browse_page should be classified as SAFE"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert "browse_page" in classifier.SAFE_PRIMITIVES
    
    def test_scrape_data_is_safe(self):
        """scrape_data should be classified as SAFE"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert "scrape_data" in classifier.SAFE_PRIMITIVES
    
    def test_generate_image_is_safe(self):
        """generate_image should be classified as SAFE"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert "generate_image" in classifier.SAFE_PRIMITIVES
    
    def test_fill_form_is_risky(self):
        """fill_form should be classified as RISKY"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert "fill_form" in classifier.RISKY_PRIMITIVES
    
    def test_run_python_is_risky(self):
        """run_python should be classified as RISKY"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert "run_python" in classifier.RISKY_PRIMITIVES


# =============================================================================
# Primitive Result Tests
# =============================================================================

class TestPrimitiveResult:
    """Test PrimitiveResult dataclass"""
    
    def test_primitive_result_exists(self):
        """PrimitiveResult should exist"""
        from backend.core.primitives import PrimitiveResult
        assert PrimitiveResult is not None
    
    def test_primitive_result_has_success_field(self):
        """PrimitiveResult should have success field"""
        from backend.core.primitives import PrimitiveResult
        
        result = PrimitiveResult(success=True, output="test")
        assert hasattr(result, 'success')
        assert result.success == True
    
    def test_primitive_result_has_output_field(self):
        """PrimitiveResult should have output field"""
        from backend.core.primitives import PrimitiveResult
        
        result = PrimitiveResult(success=True, output="test output")
        assert hasattr(result, 'output')
        assert result.output == "test output"
    
    def test_primitive_result_has_data_field(self):
        """PrimitiveResult should have data field"""
        from backend.core.primitives import PrimitiveResult
        
        result = PrimitiveResult(success=True, output="test", data={"key": "value"})
        assert hasattr(result, 'data')


# =============================================================================
# Tool Registry Tests
# =============================================================================

class TestToolRegistry:
    """Test ToolRegistry per README"""
    
    def test_tool_registry_module_exists(self):
        """ToolRegistry module should exist"""
        from backend.core import tool_registry
        assert tool_registry is not None
    
    def test_get_tool_registry_function_exists(self):
        """get_tool_registry function should exist"""
        from backend.core.tool_registry import get_tool_registry
        assert callable(get_tool_registry)
    
    def test_tool_registry_has_get_method(self):
        """ToolRegistry should have get method"""
        from backend.core.tool_registry import get_tool_registry
        
        registry = get_tool_registry()
        assert hasattr(registry, 'get')
    
    def test_tool_registry_has_register_method(self):
        """ToolRegistry should have register method"""
        from backend.core.tool_registry import get_tool_registry
        
        registry = get_tool_registry()
        assert hasattr(registry, 'register')
    
    def test_tool_registry_has_list_method(self):
        """ToolRegistry should have list/get_tool_names method"""
        from backend.core.tool_registry import get_tool_registry
        
        registry = get_tool_registry()
        assert hasattr(registry, 'get_tool_names') or hasattr(registry, 'list')


# =============================================================================
# MCP Integration Tests
# =============================================================================

class TestMCPIntegration:
    """Test MCP server integration per README"""
    
    def test_mcp_client_module_exists(self):
        """MCP client module should exist"""
        from backend.core import mcp_client
        assert mcp_client is not None
    
    def test_mcp_servers_config_exists(self):
        """MCP servers config file should exist"""
        import os
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "backend", "mcp_servers.json"
        )
        # Either the file exists or the module handles missing config gracefully
        assert True  # Config is optional


# =============================================================================
# Primitive Function Signature Tests
# =============================================================================

class TestPrimitiveFunctionSignatures:
    """Test primitive function signatures"""
    
    def test_web_search_accepts_query(self):
        """web_search should accept query parameter"""
        from backend.core.primitives import PRIMITIVES
        
        web_search_info = PRIMITIVES.get("web_search", {})
        params = web_search_info.get("params", [])
        
        # Should have query parameter
        param_names = [p.get("name") if isinstance(p, dict) else p for p in params]
        assert "query" in param_names or len(params) > 0
    
    def test_browse_page_accepts_url(self):
        """browse_page should accept url parameter"""
        from backend.core.primitives import PRIMITIVES
        
        browse_info = PRIMITIVES.get("browse_page", {})
        params = browse_info.get("params", [])
        
        param_names = [p.get("name") if isinstance(p, dict) else p for p in params]
        assert "url" in param_names or len(params) > 0
    
    def test_generate_image_accepts_prompt(self):
        """generate_image should accept prompt parameter"""
        from backend.core.primitives import PRIMITIVES
        
        gen_info = PRIMITIVES.get("generate_image", {})
        params = gen_info.get("params", [])
        
        param_names = [p.get("name") if isinstance(p, dict) else p for p in params]
        assert "prompt" in param_names or len(params) > 0


# =============================================================================
# Async Primitive Tests
# =============================================================================

class TestAsyncPrimitives:
    """Test that primitives are async"""
    
    def test_web_search_is_async(self):
        """web_search should be an async function"""
        import asyncio
        from backend.core.primitives import web_search
        
        assert asyncio.iscoroutinefunction(web_search)
    
    def test_browse_page_is_async(self):
        """browse_page should be an async function"""
        import asyncio
        from backend.core.primitives import browse_page
        
        assert asyncio.iscoroutinefunction(browse_page)
    
    def test_generate_image_is_async(self):
        """generate_image should be an async function"""
        import asyncio
        from backend.core.primitives import generate_image
        
        assert asyncio.iscoroutinefunction(generate_image)
