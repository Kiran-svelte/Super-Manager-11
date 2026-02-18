"""
ToolRegistry - Unified Tool Management System
==============================================
v6 NEW - Adapter pattern that wraps existing primitives and adds dynamic tool registration.

Architecture:
- ToolDef: Dataclass for tool definition
- ToolRegistry: CRUD + execution router + prompt generation

Design Principles:
- NO breaking changes to existing primitives.py
- Backward compatible: primitives continue working as before
- Dynamic registration: tools can be added/removed at runtime
- Risk classification: centralized safe/risky/blocked checking
- Source tagging: track where tools come from (primitive/mcp/stealth/etc)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from .primitives import PRIMITIVES, PrimitiveResult

logger = logging.getLogger(__name__)


@dataclass
class ToolDef:
    """
    Definition of a tool that can be registered with the ToolRegistry.
    
    Fields:
        name: Unique tool identifier (e.g., "web_search", "mcp__github__create_issue")
        description: Human-readable description of what the tool does
        parameters: JSON Schema dict for parameters (or simplified dict with param names)
        risk_level: "safe" (auto-execute), "risky" (confirmation), or "blocked" (forbidden)
        source: Tool source - "primitive", "mcp", "stealth", "payment", "workflow", "fallback"
        handler: Async callable that executes the tool
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema or simple dict
    risk_level: str  # "safe", "risky", "blocked"
    source: str  # "primitive", "mcp", "stealth", "payment", "workflow", "fallback"
    handler: Callable  # async function: (**kwargs) -> PrimitiveResult


class ToolRegistry:
    """
    Unified tool registry that manages all available tools.
    
    On initialization:
    - Auto-registers all 6 core primitives from PRIMITIVES dict
    
    Features:
    - Register/unregister tools dynamically
    - Get tool by name
    - List tools (optionally filtered by source)
    - Generate prompt section for system prompt
    - Execute tools (routes to appropriate handler)
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDef] = {}
        self._register_primitives()
        logger.info("ToolRegistry initialized with primitives")
    
    def _register_primitives(self):
        """Auto-register all 6 core primitives from primitives.py"""
        for name, info in PRIMITIVES.items():
            tool = ToolDef(
                name=name,
                description=info["description"],
                parameters={"params": info["params"]},  # Simple format
                risk_level=info["risk"],
                source="primitive",
                handler=info["function"],
            )
            self._tools[name] = tool
            logger.debug(f"Registered primitive: {name} (risk: {info['risk']})")
    
    def register(self, tool: ToolDef) -> None:
        """
        Register a new tool or update an existing one.
        
        Args:
            tool: ToolDef instance to register
        """
        if not tool.name:
            logger.warning("Attempted to register tool with empty name")
            return
        
        if tool.name in self._tools:
            logger.info(f"Updating existing tool: {tool.name}")
        else:
            logger.info(f"Registering new tool: {tool.name} (source: {tool.source}, risk: {tool.risk_level})")
        
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool by name.
        
        Args:
            name: Tool name to remove
            
        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            tool = self._tools[name]
            # Don't allow unregistering core primitives
            if tool.source == "primitive":
                logger.warning(f"Cannot unregister core primitive: {name}")
                return False
            
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        else:
            logger.warning(f"Tool not found for unregister: {name}")
            return False
    
    def get(self, name: str) -> Optional[ToolDef]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            ToolDef if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(self, source: str = None, risk_level: str = None) -> List[ToolDef]:
        """
        List all registered tools, optionally filtered.
        
        Args:
            source: Filter by source ("primitive", "mcp", etc.) - optional
            risk_level: Filter by risk level ("safe", "risky", "blocked") - optional
            
        Returns:
            List of ToolDef objects
        """
        tools = list(self._tools.values())
        
        if source:
            tools = [t for t in tools if t.source == source]
        
        if risk_level:
            tools = [t for t in tools if t.risk_level == risk_level]
        
        return tools
    
    def get_prompt_section(self) -> str:
        """
        Generate the tools documentation section for the system prompt.
        Replaces get_primitives_prompt() from primitives.py.
        
        Returns:
            Formatted string with all available tools
        """
        lines = ["AVAILABLE TOOLS:"]
        lines.append("")
        
        # Group by source
        sources = {}
        for tool in self._tools.values():
            if tool.source not in sources:
                sources[tool.source] = []
            sources[tool.source].append(tool)
        
        # Primitives first
        if "primitive" in sources:
            lines.append("=== Core Primitives ===")
            for tool in sources["primitive"]:
                risk_tag = " [REQUIRES CONFIRMATION]" if tool.risk_level == "risky" else ""
                params_str = tool.parameters.get("params", "")
                lines.append(f"- {tool.name}({params_str}){risk_tag}")
                lines.append(f"  {tool.description}")
                
                # Add returns info if available (from PRIMITIVES)
                if tool.name in PRIMITIVES:
                    returns = PRIMITIVES[tool.name].get("returns", "")
                    if returns:
                        lines.append(f"  Returns: {returns}")
                lines.append("")
        
        # Other sources
        for source, tools in sources.items():
            if source == "primitive":
                continue
            
            source_label = source.replace("_", " ").title()
            lines.append(f"=== {source_label} Tools ===")
            
            for tool in tools:
                risk_tag = " [REQUIRES CONFIRMATION]" if tool.risk_level == "risky" else ""
                risk_tag += " [BLOCKED]" if tool.risk_level == "blocked" else ""
                
                # Format parameters
                if isinstance(tool.parameters, dict):
                    params_list = []
                    for key, val in tool.parameters.items():
                        if isinstance(val, dict):
                            param_type = val.get("type", "any")
                            params_list.append(f"{key}: {param_type}")
                        else:
                            params_list.append(str(key))
                    params_str = ", ".join(params_list)
                else:
                    params_str = str(tool.parameters)
                
                lines.append(f"- {tool.name}({params_str}){risk_tag}")
                lines.append(f"  {tool.description}")
                lines.append("")
        
        return "\n".join(lines)
    
    async def execute(self, name: str, params: Dict[str, Any], context: Dict[str, Any] = None) -> PrimitiveResult:
        """
        Execute a tool by name.
        Routes to the appropriate handler function.
        
        Args:
            name: Tool name
            params: Parameters to pass to the tool
            context: Execution context (previous step results)
            
        Returns:
            PrimitiveResult with success status, output, and data
        """
        context = context or {}
        
        tool = self.get(name)
        if not tool:
            return PrimitiveResult(
                success=False,
                output=f"Unknown tool: {name}. Available tools: {', '.join(self._tools.keys())}",
                error="unknown_tool",
            )
        
        try:
            # Call the handler
            # Most handlers expect params as **kwargs, but some may expect context separately
            if tool.source == "primitive":
                # Primitives don't use context
                result = await tool.handler(**params)
            else:
                # Other tools may use context
                try:
                    result = await tool.handler(**params, context=context)
                except TypeError:
                    # Handler doesn't accept context
                    result = await tool.handler(**params)
            
            return result
        
        except Exception as e:
            logger.error(f"Tool execution error ({name}): {e}", exc_info=True)
            return PrimitiveResult(
                success=False,
                output=f"Tool execution failed: {str(e)}",
                error=str(e),
            )
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self._tools
    
    def get_risk_level(self, name: str) -> Optional[str]:
        """
        Get the risk level of a tool.
        
        Args:
            name: Tool name
            
        Returns:
            "safe", "risky", "blocked", or None if not found
        """
        tool = self.get(name)
        return tool.risk_level if tool else None


# =============================================================================
# GLOBAL REGISTRY INSTANCE
# =============================================================================

_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global ToolRegistry instance (singleton pattern).
    Creates it if it doesn't exist yet.
    
    Returns:
        ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def reset_tool_registry():
    """
    Reset the global registry (for testing).
    """
    global _global_registry
    _global_registry = None
