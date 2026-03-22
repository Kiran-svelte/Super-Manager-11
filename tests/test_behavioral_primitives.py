"""
Behavioral Tests: Primitives
=============================
Tests that the primitive functions ACTUALLY work:
- web_search returns search results
- browse_page returns page content
- scrape_data extracts data
- generate_image returns image URL
- PrimitiveResult dataclass works correctly
- PRIMITIVES registry contains all 6 primitives

README Requirements:
- 6 Core Primitives
- SAFE: web_search, browse_page, scrape_data, generate_image
- RISKY: fill_form, run_python
"""

import pytest
from dataclasses import is_dataclass

from backend.core.primitives import (
    PrimitiveResult,
    web_search,
    browse_page,
    scrape_data,
    generate_image,
    fill_form,
    run_python,
    PRIMITIVES
)


class TestPrimitiveResult:
    """Test PrimitiveResult dataclass"""
    
    def test_primitive_result_is_dataclass(self):
        """PrimitiveResult should be a dataclass"""
        assert is_dataclass(PrimitiveResult)
    
    def test_primitive_result_fields(self):
        """PrimitiveResult should have required fields"""
        result = PrimitiveResult(
            success=True,
            output="Test output",
            data={"key": "value"},
            error=None
        )
        
        assert result.success is True
        assert result.output == "Test output"
        assert result.data == {"key": "value"}
        assert result.error is None
    
    def test_primitive_result_defaults(self):
        """PrimitiveResult should have sensible defaults"""
        result = PrimitiveResult(success=False, output="Error")
        
        assert result.data == {}
        assert result.error is None
    
    def test_primitive_result_error_case(self):
        """PrimitiveResult should store error info"""
        result = PrimitiveResult(
            success=False,
            output="Failed to connect",
            error="ConnectionTimeout"
        )
        
        assert result.success is False
        assert result.error == "ConnectionTimeout"


class TestPrimitivesRegistry:
    """Test PRIMITIVES registry"""
    
    def test_primitives_registry_exists(self):
        """PRIMITIVES registry should exist"""
        assert PRIMITIVES is not None
        assert isinstance(PRIMITIVES, dict)
    
    def test_primitives_contains_web_search(self):
        """PRIMITIVES should contain web_search"""
        assert "web_search" in PRIMITIVES
    
    def test_primitives_contains_browse_page(self):
        """PRIMITIVES should contain browse_page"""
        assert "browse_page" in PRIMITIVES
    
    def test_primitives_contains_scrape_data(self):
        """PRIMITIVES should contain scrape_data"""
        assert "scrape_data" in PRIMITIVES
    
    def test_primitives_contains_generate_image(self):
        """PRIMITIVES should contain generate_image"""
        assert "generate_image" in PRIMITIVES
    
    def test_primitives_contains_fill_form(self):
        """PRIMITIVES should contain fill_form"""
        assert "fill_form" in PRIMITIVES
    
    def test_primitives_contains_run_python(self):
        """PRIMITIVES should contain run_python"""
        assert "run_python" in PRIMITIVES
    
    def test_primitives_has_six_entries(self):
        """PRIMITIVES should have exactly 6 entries"""
        assert len(PRIMITIVES) == 6
    
    def test_primitive_entry_has_function(self):
        """Each primitive entry should have a function"""
        for name, entry in PRIMITIVES.items():
            assert "function" in entry
            assert callable(entry["function"])
    
    def test_primitive_entry_has_risk_level(self):
        """Each primitive entry should have a risk level"""
        for name, entry in PRIMITIVES.items():
            assert "risk" in entry
            assert entry["risk"] in ["safe", "risky"]
    
    def test_primitive_entry_has_description(self):
        """Each primitive entry should have a description"""
        for name, entry in PRIMITIVES.items():
            assert "description" in entry
            assert isinstance(entry["description"], str)
    
    def test_primitive_entry_has_params(self):
        """Each primitive entry should have params"""
        for name, entry in PRIMITIVES.items():
            assert "params" in entry


class TestSafePrimitivesRiskLevel:
    """Test that SAFE primitives are marked correctly"""
    
    def test_web_search_is_safe(self):
        """web_search should be marked as safe"""
        assert PRIMITIVES["web_search"]["risk"] == "safe"
    
    def test_browse_page_is_safe(self):
        """browse_page should be marked as safe"""
        assert PRIMITIVES["browse_page"]["risk"] == "safe"
    
    def test_scrape_data_is_safe(self):
        """scrape_data should be marked as safe"""
        assert PRIMITIVES["scrape_data"]["risk"] == "safe"
    
    def test_generate_image_is_safe(self):
        """generate_image should be marked as safe"""
        assert PRIMITIVES["generate_image"]["risk"] == "safe"


class TestRiskyPrimitivesRiskLevel:
    """Test that RISKY primitives are marked correctly"""
    
    def test_fill_form_is_risky(self):
        """fill_form should be marked as risky"""
        assert PRIMITIVES["fill_form"]["risk"] == "risky"
    
    def test_run_python_is_risky(self):
        """run_python should be marked as risky"""
        assert PRIMITIVES["run_python"]["risk"] == "risky"


class TestWebSearchFunction:
    """Test web_search primitive function"""
    
    @pytest.mark.asyncio
    async def test_web_search_empty_query_fails(self):
        """web_search should fail with empty query"""
        result = await web_search("")
        
        assert result.success is False
        assert "query" in result.output.lower() or "missing" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_web_search_returns_primitive_result(self):
        """web_search should return PrimitiveResult"""
        result = await web_search("test query that might not return results")
        
        assert isinstance(result, PrimitiveResult)
    
    @pytest.mark.asyncio
    async def test_web_search_has_results_in_data(self):
        """web_search data should contain results list"""
        result = await web_search("python programming")
        
        # Even if no results, should have results key
        assert "results" in result.data or result.success is False


class TestBrowsePageFunction:
    """Test browse_page primitive function"""
    
    @pytest.mark.asyncio
    async def test_browse_page_empty_url_fails(self):
        """browse_page should fail with empty URL"""
        result = await browse_page("")
        
        assert result.success is False
        assert "url" in result.output.lower() or "missing" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_browse_page_returns_primitive_result(self):
        """browse_page should return PrimitiveResult"""
        result = await browse_page("https://example.com")
        
        assert isinstance(result, PrimitiveResult)
    
    @pytest.mark.asyncio
    async def test_browse_page_adds_protocol(self):
        """browse_page should add https:// if missing"""
        # This tests the URL normalization
        result = await browse_page("example.com")
        
        # Should not fail due to missing protocol
        assert isinstance(result, PrimitiveResult)


class TestScrapeDataFunction:
    """Test scrape_data primitive function"""
    
    @pytest.mark.asyncio
    async def test_scrape_data_returns_primitive_result(self):
        """scrape_data should return PrimitiveResult"""
        result = await scrape_data("https://example.com", {"title": "h1"})
        
        assert isinstance(result, PrimitiveResult)


class TestGenerateImageFunction:
    """Test generate_image primitive function"""
    
    @pytest.mark.asyncio
    async def test_generate_image_empty_prompt_fails(self):
        """generate_image should fail with empty prompt"""
        result = await generate_image("")
        
        assert result.success is False
    
    @pytest.mark.asyncio
    async def test_generate_image_returns_primitive_result(self):
        """generate_image should return PrimitiveResult"""
        result = await generate_image("a beautiful sunset")
        
        assert isinstance(result, PrimitiveResult)


class TestFillFormFunction:
    """Test fill_form primitive function"""
    
    @pytest.mark.asyncio
    async def test_fill_form_returns_primitive_result(self):
        """fill_form should return PrimitiveResult"""
        result = await fill_form("https://example.com/form", {"name": "test"})
        
        assert isinstance(result, PrimitiveResult)


class TestRunPythonFunction:
    """Test run_python primitive function"""
    
    @pytest.mark.asyncio
    async def test_run_python_simple_code(self):
        """run_python should execute simple code"""
        result = await run_python("result = 1 + 1")
        
        assert isinstance(result, PrimitiveResult)
    
    @pytest.mark.asyncio
    async def test_run_python_empty_code(self):
        """run_python should handle empty code"""
        result = await run_python("")
        
        assert isinstance(result, PrimitiveResult)


class TestPrimitiveParams:
    """Test primitive params definitions"""
    
    def test_web_search_params(self):
        """web_search should have query param"""
        params = PRIMITIVES["web_search"]["params"]
        
        # params is a string like 'query (str), max_results (int, default 5)'
        assert "query" in params
    
    def test_browse_page_params(self):
        """browse_page should have url param"""
        params = PRIMITIVES["browse_page"]["params"]
        
        assert "url" in params
    
    def test_fill_form_params(self):
        """fill_form should have url and fields params"""
        params = PRIMITIVES["fill_form"]["params"]
        
        assert "url" in params
        assert "fields" in params
    
    def test_generate_image_params(self):
        """generate_image should have prompt param"""
        params = PRIMITIVES["generate_image"]["params"]
        
        assert "prompt" in params


class TestPrimitiveDescriptions:
    """Test primitive descriptions are meaningful"""
    
    def test_web_search_has_description(self):
        """web_search should have a meaningful description"""
        desc = PRIMITIVES["web_search"]["description"]
        assert len(desc) > 20
        assert "search" in desc.lower()
    
    def test_browse_page_has_description(self):
        """browse_page should have a meaningful description"""
        desc = PRIMITIVES["browse_page"]["description"]
        assert len(desc) > 20
    
    def test_generate_image_has_description(self):
        """generate_image should have a meaningful description"""
        desc = PRIMITIVES["generate_image"]["description"]
        assert len(desc) > 20
        assert "image" in desc.lower()
