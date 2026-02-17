"""
Test ToolRegistry
=================
Tests for the unified tool management system (v6).
"""

import pytest
import asyncio
from backend.core.tool_registry import ToolRegistry, ToolDef, get_tool_registry, reset_tool_registry
from backend.core.primitives import PrimitiveResult


@pytest.fixture
def registry():
    """Create a fresh ToolRegistry for each test"""
    reset_tool_registry()  # Clear global instance
    return ToolRegistry()


@pytest.fixture
async def sample_tool_handler():
    """Sample async tool handler for testing"""
    async def handler(param1: str, param2: int = 5) -> PrimitiveResult:
        return PrimitiveResult(
            success=True,
            output=f"Handler called with {param1}, {param2}",
            data={"param1": param1, "param2": param2},
        )
    return handler


class TestToolRegistry:
    """Test ToolRegistry CRUD operations"""
    
    def test_init_registers_primitives(self, registry):
        """Test that ToolRegistry auto-registers all 6 core primitives"""
        primitives = registry.list_tools(source="primitive")
        assert len(primitives) == 6
        
        primitive_names = [t.name for t in primitives]
        assert "web_search" in primitive_names
        assert "browse_page" in primitive_names
        assert "scrape_data" in primitive_names
        assert "generate_image" in primitive_names
        assert "fill_form" in primitive_names
        assert "run_python" in primitive_names
    
    def test_primitives_risk_levels(self, registry):
        """Test that primitives have correct risk levels"""
        safe_tools = registry.list_tools(source="primitive", risk_level="safe")
        risky_tools = registry.list_tools(source="primitive", risk_level="risky")
        
        safe_names = [t.name for t in safe_tools]
        risky_names = [t.name for t in risky_tools]
        
        assert "web_search" in safe_names
        assert "browse_page" in safe_names
        assert "scrape_data" in safe_names
        assert "generate_image" in safe_names
        
        assert "fill_form" in risky_names
        assert "run_python" in risky_names
    
    @pytest.mark.asyncio
    async def test_register_new_tool(self, registry, sample_tool_handler):
        """Test registering a new tool"""
        tool = ToolDef(
            name="test_tool",
            description="A test tool",
            parameters={"param1": {"type": "string"}, "param2": {"type": "integer"}},
            risk_level="safe",
            source="test",
            handler=sample_tool_handler,
        )
        
        registry.register(tool)
        
        # Verify tool is registered
        retrieved = registry.get("test_tool")
        assert retrieved is not None
        assert retrieved.name == "test_tool"
        assert retrieved.source == "test"
        assert retrieved.risk_level == "safe"
    
    def test_unregister_tool(self, registry, sample_tool_handler):
        """Test unregistering a tool"""
        tool = ToolDef(
            name="temp_tool",
            description="Temporary tool",
            parameters={},
            risk_level="safe",
            source="test",
            handler=sample_tool_handler,
        )
        
        registry.register(tool)
        assert registry.has_tool("temp_tool")
        
        # Unregister
        success = registry.unregister("temp_tool")
        assert success
        assert not registry.has_tool("temp_tool")
    
    def test_cannot_unregister_primitive(self, registry):
        """Test that core primitives cannot be unregistered"""
        success = registry.unregister("web_search")
        assert not success
        assert registry.has_tool("web_search")
    
    def test_get_nonexistent_tool(self, registry):
        """Test getting a tool that doesn't exist"""
        tool = registry.get("nonexistent_tool")
        assert tool is None
    
    def test_list_tools_by_source(self, registry, sample_tool_handler):
        """Test listing tools filtered by source"""
        # Add tools from different sources
        tool1 = ToolDef(
            name="mcp_test",
            description="MCP tool",
            parameters={},
            risk_level="safe",
            source="mcp",
            handler=sample_tool_handler,
        )
        tool2 = ToolDef(
            name="stealth_test",
            description="Stealth tool",
            parameters={},
            risk_level="safe",
            source="stealth",
            handler=sample_tool_handler,
        )
        
        registry.register(tool1)
        registry.register(tool2)
        
        # Filter by source
        mcp_tools = registry.list_tools(source="mcp")
        stealth_tools = registry.list_tools(source="stealth")
        
        assert len(mcp_tools) == 1
        assert mcp_tools[0].name == "mcp_test"
        
        assert len(stealth_tools) == 1
        assert stealth_tools[0].name == "stealth_test"
    
    def test_list_tools_by_risk_level(self, registry, sample_tool_handler):
        """Test listing tools filtered by risk level"""
        tool1 = ToolDef(
            name="safe_tool",
            description="Safe tool",
            parameters={},
            risk_level="safe",
            source="test",
            handler=sample_tool_handler,
        )
        tool2 = ToolDef(
            name="risky_tool",
            description="Risky tool",
            parameters={},
            risk_level="risky",
            source="test",
            handler=sample_tool_handler,
        )
        
        registry.register(tool1)
        registry.register(tool2)
        
        # Filter by risk level
        safe_tools = registry.list_tools(risk_level="safe")
        risky_tools = registry.list_tools(risk_level="risky")
        
        # Should include primitives + our test tools
        assert any(t.name == "safe_tool" for t in safe_tools)
        assert any(t.name == "risky_tool" for t in risky_tools)
    
    def test_get_risk_level(self, registry):
        """Test getting risk level of a tool"""
        assert registry.get_risk_level("web_search") == "safe"
        assert registry.get_risk_level("fill_form") == "risky"
        assert registry.get_risk_level("nonexistent") is None
    
    def test_has_tool(self, registry):
        """Test checking if a tool exists"""
        assert registry.has_tool("web_search")
        assert registry.has_tool("browse_page")
        assert not registry.has_tool("fake_tool")


class TestPromptGeneration:
    """Test prompt section generation"""
    
    def test_get_prompt_section_includes_primitives(self, registry):
        """Test that prompt section includes all primitives"""
        prompt = registry.get_prompt_section()
        
        assert "AVAILABLE TOOLS:" in prompt
        assert "=== Core Primitives ===" in prompt
        assert "web_search" in prompt
        assert "browse_page" in prompt
        assert "scrape_data" in prompt
        assert "generate_image" in prompt
        assert "fill_form" in prompt
        assert "run_python" in prompt
    
    def test_get_prompt_section_shows_risk_tags(self, registry):
        """Test that risky tools are tagged with [REQUIRES CONFIRMATION]"""
        prompt = registry.get_prompt_section()
        
        # Risky tools should have confirmation tag
        assert "[REQUIRES CONFIRMATION]" in prompt
        
        # Check that risky tools are tagged
        lines = prompt.split("\n")
        fill_form_lines = [l for l in lines if "fill_form" in l]
        run_python_lines = [l for l in lines if "run_python" in l]
        
        assert any("[REQUIRES CONFIRMATION]" in l for l in fill_form_lines)
        assert any("[REQUIRES CONFIRMATION]" in l for l in run_python_lines)
    
    def test_get_prompt_section_groups_by_source(self, registry, sample_tool_handler):
        """Test that prompt section groups tools by source"""
        # Add tools from different sources
        tool1 = ToolDef(
            name="payment_test",
            description="Payment tool",
            parameters={},
            risk_level="risky",
            source="payment",
            handler=sample_tool_handler,
        )
        registry.register(tool1)
        
        prompt = registry.get_prompt_section()
        
        # Should have sections for different sources
        assert "=== Core Primitives ===" in prompt
        assert "=== Payment Tools ===" in prompt


class TestExecution:
    """Test tool execution"""
    
    @pytest.mark.asyncio
    async def test_execute_primitive(self, registry):
        """Test executing a core primitive through registry"""
        # Note: web_search requires network, so we just test the routing
        result = await registry.execute("nonexistent_tool", {})
        
        assert not result.success
        assert "Unknown tool" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_custom_tool(self, registry, sample_tool_handler):
        """Test executing a custom registered tool"""
        tool = ToolDef(
            name="custom_tool",
            description="Custom tool",
            parameters={"param1": {"type": "string"}, "param2": {"type": "integer"}},
            risk_level="safe",
            source="test",
            handler=sample_tool_handler,
        )
        registry.register(tool)
        
        result = await registry.execute("custom_tool", {"param1": "test", "param2": 10})
        
        assert result.success
        assert "Handler called with test, 10" in result.output
        assert result.data["param1"] == "test"
        assert result.data["param2"] == 10
    
    @pytest.mark.asyncio
    async def test_execute_with_context(self, registry):
        """Test executing a tool with context"""
        async def context_aware_handler(value: str, context: dict = None) -> PrimitiveResult:
            context = context or {}
            return PrimitiveResult(
                success=True,
                output=f"Value: {value}, Context keys: {list(context.keys())}",
                data={"value": value, "context_keys": list(context.keys())},
            )
        
        tool = ToolDef(
            name="context_tool",
            description="Context-aware tool",
            parameters={"value": {"type": "string"}},
            risk_level="safe",
            source="test",
            handler=context_aware_handler,
        )
        registry.register(tool)
        
        context = {"step_1": {"result": "previous"}}
        result = await registry.execute("context_tool", {"value": "test"}, context)
        
        assert result.success
        assert "step_1" in result.data["context_keys"]


class TestGlobalRegistry:
    """Test global registry singleton"""
    
    def test_get_tool_registry_singleton(self):
        """Test that get_tool_registry returns the same instance"""
        reset_tool_registry()
        
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        
        assert registry1 is registry2
    
    def test_reset_tool_registry(self):
        """Test that reset_tool_registry creates a new instance"""
        registry1 = get_tool_registry()
        reset_tool_registry()
        registry2 = get_tool_registry()
        
        assert registry1 is not registry2
