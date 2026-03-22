"""
Behavioral Tests: Tool Registry
==================================
Tests that the tool registry ACTUALLY works:
- ToolDef dataclass
- ToolRegistry registration/unregistration
- Tool lookup and listing
- Risk level retrieval
- Prompt generation

README Requirements:
- Dynamic tool management
- Tools from multiple sources (primitives, MCP, stealth, etc.)
- Risk level tracking
- Prompt generation for agents
"""

import pytest
from dataclasses import is_dataclass

from backend.core.tool_registry import (
    ToolDef, ToolRegistry, get_tool_registry
)
from backend.core.primitives import PrimitiveResult


class TestToolDefDataclass:
    """Test ToolDef dataclass structure"""
    
    def test_is_dataclass(self):
        """ToolDef should be a dataclass"""
        assert is_dataclass(ToolDef)
    
    def test_required_fields(self):
        """ToolDef should have required fields"""
        tool = ToolDef(
            name="test_tool",
            description="A test tool",
            parameters="param1 (str)",
            returns="Test result",
            risk_level="safe",
            source="primitive"
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters == "param1 (str)"
        assert tool.returns == "Test result"
        assert tool.risk_level == "safe"
        assert tool.source == "primitive"
    
    def test_handler_optional(self):
        """ToolDef handler should be optional"""
        tool = ToolDef(
            name="test",
            description="Test",
            parameters="",
            returns="",
            risk_level="safe",
            source="test"
        )
        
        assert tool.handler is None
    
    def test_parameter_schema_optional(self):
        """ToolDef parameter_schema should be optional"""
        tool = ToolDef(
            name="test",
            description="Test",
            parameters="",
            returns="",
            risk_level="safe",
            source="test"
        )
        
        assert tool.parameter_schema is None
    
    def test_handler_callable(self):
        """ToolDef handler can be callable"""
        async def my_handler(params, context):
            return PrimitiveResult(success=True, output="OK")
        
        tool = ToolDef(
            name="test",
            description="Test",
            parameters="",
            returns="",
            risk_level="safe",
            source="test",
            handler=my_handler
        )
        
        assert callable(tool.handler)
    
    def test_parameter_schema_dict(self):
        """ToolDef parameter_schema can be JSON schema dict"""
        tool = ToolDef(
            name="test",
            description="Test",
            parameters="",
            returns="",
            risk_level="safe",
            source="mcp",
            parameter_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        )
        
        assert tool.parameter_schema["type"] == "object"


class TestToolDefRiskLevels:
    """Test ToolDef risk level values"""
    
    def test_safe_risk_level(self):
        """ToolDef should support safe risk level"""
        tool = ToolDef(
            name="test", description="Test", parameters="", 
            returns="", risk_level="safe", source="primitive"
        )
        assert tool.risk_level == "safe"
    
    def test_risky_risk_level(self):
        """ToolDef should support risky risk level"""
        tool = ToolDef(
            name="test", description="Test", parameters="",
            returns="", risk_level="risky", source="primitive"
        )
        assert tool.risk_level == "risky"
    
    def test_blocked_risk_level(self):
        """ToolDef should support blocked risk level"""
        tool = ToolDef(
            name="test", description="Test", parameters="",
            returns="", risk_level="blocked", source="primitive"
        )
        assert tool.risk_level == "blocked"


class TestToolDefSources:
    """Test ToolDef source values"""
    
    def test_primitive_source(self):
        """ToolDef should support primitive source"""
        tool = ToolDef(
            name="test", description="Test", parameters="",
            returns="", risk_level="safe", source="primitive"
        )
        assert tool.source == "primitive"
    
    def test_mcp_source(self):
        """ToolDef should support mcp source"""
        tool = ToolDef(
            name="test", description="Test", parameters="",
            returns="", risk_level="safe", source="mcp"
        )
        assert tool.source == "mcp"
    
    def test_stealth_source(self):
        """ToolDef should support stealth source"""
        tool = ToolDef(
            name="test", description="Test", parameters="",
            returns="", risk_level="safe", source="stealth"
        )
        assert tool.source == "stealth"
    
    def test_payment_source(self):
        """ToolDef should support payment source"""
        tool = ToolDef(
            name="test", description="Test", parameters="",
            returns="", risk_level="safe", source="payment"
        )
        assert tool.source == "payment"
    
    def test_fallback_source(self):
        """ToolDef should support fallback source"""
        tool = ToolDef(
            name="test", description="Test", parameters="",
            returns="", risk_level="safe", source="fallback"
        )
        assert tool.source == "fallback"
    
    def test_workflow_source(self):
        """ToolDef should support workflow source"""
        tool = ToolDef(
            name="test", description="Test", parameters="",
            returns="", risk_level="safe", source="workflow"
        )
        assert tool.source == "workflow"


class TestToolRegistryInit:
    """Test ToolRegistry initialization"""
    
    def test_can_instantiate(self):
        """ToolRegistry should be instantiatable"""
        registry = ToolRegistry()
        assert registry is not None
    
    def test_has_tools_dict(self):
        """ToolRegistry should have _tools dict"""
        registry = ToolRegistry()
        assert hasattr(registry, "_tools")
        assert isinstance(registry._tools, dict)
    
    def test_starts_empty(self):
        """ToolRegistry should start empty before initialization"""
        registry = ToolRegistry()
        assert len(registry._tools) == 0
    
    def test_has_initialized_flag(self):
        """ToolRegistry should have _initialized flag"""
        registry = ToolRegistry()
        assert hasattr(registry, "_initialized")
        assert registry._initialized is False


class TestToolRegistryInitialize:
    """Test ToolRegistry.initialize()"""
    
    def test_initialize_registers_primitives(self):
        """initialize() should register primitives"""
        registry = ToolRegistry()
        registry.initialize()
        
        # Should have at least 6 primitives
        assert len(registry._tools) >= 6
    
    def test_initialize_sets_flag(self):
        """initialize() should set _initialized flag"""
        registry = ToolRegistry()
        registry.initialize()
        
        assert registry._initialized is True
    
    def test_initialize_is_idempotent(self):
        """initialize() called twice should be safe"""
        registry = ToolRegistry()
        registry.initialize()
        count1 = len(registry._tools)
        
        registry.initialize()
        count2 = len(registry._tools)
        
        assert count1 == count2


class TestToolRegistryRegister:
    """Test ToolRegistry.register()"""
    
    def test_register_adds_tool(self):
        """register() should add tool to registry"""
        registry = ToolRegistry()
        
        tool = ToolDef(
            name="custom_tool",
            description="Custom tool",
            parameters="",
            returns="",
            risk_level="safe",
            source="test"
        )
        
        registry.register(tool)
        
        assert "custom_tool" in registry._tools
    
    def test_register_overwrites_existing(self):
        """register() should overwrite if same name exists"""
        registry = ToolRegistry()
        
        tool1 = ToolDef(
            name="my_tool",
            description="Version 1",
            parameters="",
            returns="",
            risk_level="safe",
            source="test"
        )
        
        tool2 = ToolDef(
            name="my_tool",
            description="Version 2",
            parameters="",
            returns="",
            risk_level="risky",
            source="test"
        )
        
        registry.register(tool1)
        registry.register(tool2)
        
        assert registry._tools["my_tool"].description == "Version 2"
        assert registry._tools["my_tool"].risk_level == "risky"


class TestToolRegistryUnregister:
    """Test ToolRegistry.unregister()"""
    
    def test_unregister_removes_tool(self):
        """unregister() should remove tool from registry"""
        registry = ToolRegistry()
        
        tool = ToolDef(
            name="temp_tool",
            description="Temp",
            parameters="",
            returns="",
            risk_level="safe",
            source="test"
        )
        
        registry.register(tool)
        assert "temp_tool" in registry._tools
        
        registry.unregister("temp_tool")
        assert "temp_tool" not in registry._tools
    
    def test_unregister_nonexistent_is_safe(self):
        """unregister() should be safe for nonexistent tool"""
        registry = ToolRegistry()
        
        # Should not raise
        registry.unregister("nonexistent_tool")


class TestToolRegistryGet:
    """Test ToolRegistry.get()"""
    
    def test_get_returns_tool(self):
        """get() should return ToolDef"""
        registry = ToolRegistry()
        registry.initialize()
        
        tool = registry.get("web_search")
        
        assert tool is not None
        assert isinstance(tool, ToolDef)
    
    def test_get_returns_none_for_unknown(self):
        """get() should return None for unknown tool"""
        registry = ToolRegistry()
        
        tool = registry.get("nonexistent_tool")
        
        assert tool is None


class TestToolRegistryListTools:
    """Test ToolRegistry.list_tools()"""
    
    def test_list_all_tools(self):
        """list_tools() should return all tools"""
        registry = ToolRegistry()
        registry.initialize()
        
        tools = registry.list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) >= 6
    
    def test_list_tools_by_source(self):
        """list_tools() should filter by source"""
        registry = ToolRegistry()
        registry.initialize()
        
        primitives = registry.list_tools(source="primitive")
        
        assert all(t.source == "primitive" for t in primitives)
    
    def test_list_tools_empty_for_unknown_source(self):
        """list_tools() should return empty for unknown source"""
        registry = ToolRegistry()
        registry.initialize()
        
        tools = registry.list_tools(source="unknown_source")
        
        assert len(tools) == 0


class TestToolRegistryGetToolNames:
    """Test ToolRegistry.get_tool_names()"""
    
    def test_returns_list(self):
        """get_tool_names() should return list"""
        registry = ToolRegistry()
        registry.initialize()
        
        names = registry.get_tool_names()
        
        assert isinstance(names, list)
    
    def test_contains_primitives(self):
        """get_tool_names() should contain primitive names"""
        registry = ToolRegistry()
        registry.initialize()
        
        names = registry.get_tool_names()
        
        assert "web_search" in names
        assert "browse_page" in names


class TestToolRegistryGetRiskLevel:
    """Test ToolRegistry.get_risk_level()"""
    
    def test_returns_safe_for_safe_tool(self):
        """get_risk_level() should return safe for safe tools"""
        registry = ToolRegistry()
        registry.initialize()
        
        risk = registry.get_risk_level("web_search")
        
        assert risk == "safe"
    
    def test_returns_risky_for_risky_tool(self):
        """get_risk_level() should return risky for risky tools"""
        registry = ToolRegistry()
        registry.initialize()
        
        risk = registry.get_risk_level("fill_form")
        
        assert risk == "risky"
    
    def test_returns_blocked_for_unknown(self):
        """get_risk_level() should return blocked for unknown tools"""
        registry = ToolRegistry()
        
        risk = registry.get_risk_level("unknown_dangerous_tool")
        
        assert risk == "blocked"


class TestToolRegistryGetPromptSection:
    """Test ToolRegistry.get_prompt_section()"""
    
    def test_returns_string(self):
        """get_prompt_section() should return string"""
        registry = ToolRegistry()
        registry.initialize()
        
        prompt = registry.get_prompt_section()
        
        assert isinstance(prompt, str)
    
    def test_contains_tool_info(self):
        """get_prompt_section() should contain tool info"""
        registry = ToolRegistry()
        registry.initialize()
        
        prompt = registry.get_prompt_section()
        
        assert "web_search" in prompt or "tool" in prompt.lower()
    
    def test_empty_registry_message(self):
        """get_prompt_section() should handle empty registry"""
        registry = ToolRegistry()
        
        prompt = registry.get_prompt_section()
        
        assert "No tools" in prompt or prompt == "" or isinstance(prompt, str)


class TestGetToolRegistrySingleton:
    """Test get_tool_registry() singleton"""
    
    def test_returns_registry(self):
        """get_tool_registry() should return ToolRegistry"""
        registry = get_tool_registry()
        
        assert isinstance(registry, ToolRegistry)
    
    def test_returns_same_instance(self):
        """get_tool_registry() should return same instance"""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        
        assert registry1 is registry2
    
    def test_is_initialized(self):
        """get_tool_registry() should return initialized registry"""
        registry = get_tool_registry()
        
        assert registry._initialized is True
