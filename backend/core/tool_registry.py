"""
Tool Registry - Unified Dynamic Tool Management
=================================================
Replaces hardcoded PRIMITIVES dict with a dynamic registry that
aggregates tools from multiple sources:
- Legacy primitives (web_search, browse_page, etc.)
- MCP servers (dynamic discovery)
- Stealth browser tools
- Payment link generation
- Human fallback
- Taught workflows

Each tool has a standard ToolDef interface and is callable through
registry.execute(name, params, context).
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Union

from .primitives import PRIMITIVES, PrimitiveResult
from .integration_manager.integration_store import integration_store

logger = logging.getLogger(__name__)


@dataclass
class ToolDef:
    """Definition of a tool available to the agent"""
    name: str
    description: str
    parameters: str              # Human-readable param description for LLM prompt
    returns: str                 # Human-readable return description
    risk_level: str              # "safe", "risky", "blocked"
    source: str                  # "primitive", "mcp", "stealth", "payment", "fallback", "workflow"
    handler: Optional[Callable] = None  # async function(params, context) -> PrimitiveResult
    parameter_schema: Optional[Dict[str, Any]] = None  # JSON Schema (for MCP tools)
    required_integration: Optional[str] = None  # Needed integration (e.g. 'gmail', 'google_calendar')


class ToolRegistry:
    """
    Central registry for all tools available to the agent.
    Supports dynamic registration/unregistration at runtime.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDef] = {}
        self._initialized = False

    def initialize(self):
        """Register all built-in primitives"""
        if self._initialized:
            return

        for name, info in PRIMITIVES.items():
            req_int = None
            if name == "send_email":
                req_int = "gmail"
            elif name == "create_meeting":
                req_int = "zoom"  # Zoom integration required for Zoom meetings
            elif name == "send_telegram":
                req_int = None  # Telegram works without integration (bot token in env)
            
            self.register(ToolDef(
                name=name,
                description=info["description"],
                parameters=info["params"],
                returns=info["returns"],
                risk_level=info["risk"],
                source="primitive",
                handler=info["function"],
                required_integration=req_int
            ))

        self._initialized = True
        logger.info(f"[TOOL_REGISTRY] Initialized with {len(self._tools)} built-in primitives")

    def register(self, tool: ToolDef):
        """Register a tool. Overwrites if same name exists."""
        self._tools[tool.name] = tool
        logger.info(f"[TOOL_REGISTRY] Registered: {tool.name} (source={tool.source}, risk={tool.risk_level})")

    def unregister(self, name: str):
        """Remove a tool from the registry"""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"[TOOL_REGISTRY] Unregistered: {name}")

    def get(self, name: str) -> Optional[ToolDef]:
        """Get a tool definition by name"""
        return self._tools.get(name)

    def list_tools(self, source: str = None) -> List[ToolDef]:
        """List all tools, optionally filtered by source"""
        if source:
            return [t for t in self._tools.values() if t.source == source]
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """Get all registered tool names"""
        return list(self._tools.keys())

    def get_risk_level(self, name: str) -> str:
        """Get risk level for a tool. Returns 'blocked' if not found."""
        tool = self._tools.get(name)
        if tool:
            return tool.risk_level
        return "blocked"

    def get_prompt_section(self) -> str:
        """
        Generate the tools documentation for the agent system prompt.
        Replaces primitives.get_primitives_prompt().
        Groups tools by source for clarity.
        """
        if not self._tools:
            return "No tools available."

        # Group by source
        by_source: Dict[str, List[ToolDef]] = {}
        for tool in self._tools.values():
            by_source.setdefault(tool.source, []).append(tool)

        lines = ["AVAILABLE TOOLS:"]

        # Show primitives first (most important / familiar)
        source_order = ["primitive", "stealth", "payment", "fallback", "workflow", "mcp"]
        source_labels = {
            "primitive": "CORE PRIMITIVES",
            "stealth": "STEALTH BROWSER",
            "payment": "PAYMENT LINKS",
            "fallback": "HUMAN FALLBACK",
            "workflow": "LEARNED WORKFLOWS",
            "mcp": "MCP TOOLS (dynamically discovered)",
        }

        for source in source_order:
            tools = by_source.get(source, [])
            if not tools:
                continue

            label = source_labels.get(source, source.upper())
            lines.append(f"\n--- {label} ---")

            for tool in tools:
                risk_tag = " [REQUIRES CONFIRMATION]" if tool.risk_level == "risky" else ""
                lines.append(f"- {tool.name}({tool.parameters}){risk_tag}")
                lines.append(f"  {tool.description}")
                lines.append(f"  Returns: {tool.returns}")
                lines.append("")

        # Include any unlisted sources
        for source, tools in by_source.items():
            if source not in source_order:
                lines.append(f"\n--- {source.upper()} ---")
                for tool in tools:
                    risk_tag = " [REQUIRES CONFIRMATION]" if tool.risk_level == "risky" else ""
                    lines.append(f"- {tool.name}({tool.parameters}){risk_tag}")
                    lines.append(f"  {tool.description}")
                    lines.append(f"  Returns: {tool.returns}")
                    lines.append("")

        return "\n".join(lines)

    async def execute(self, name: str, params: Dict[str, Any], context: Dict[str, Any] = None) -> PrimitiveResult:
        """
        Execute a tool by name with given parameters.
        Returns PrimitiveResult for consistency.
        """
        tool = self._tools.get(name)
        if not tool:
            return PrimitiveResult(
                success=False,
                output=f"Tool '{name}' not found. Available: {', '.join(self._tools.keys())}",
                error="tool_not_found",
            )

        if not tool.handler:
            return PrimitiveResult(
                success=False,
                output=f"Tool '{name}' has no handler registered.",
                error="no_handler",
            )

        # 🔐 LAYER 6: INTEGRATION MANAGER CHECK
        if tool.required_integration:
            user_id = (context or {}).get("user_id", "default")
            connected = integration_store.is_connected(user_id, tool.required_integration)
            if not connected:
                # Tell the agent that OAuth is required
                return PrimitiveResult(
                    success=False,
                    output=f"Error: Missing integration. You MUST ask the user to connect '{tool.required_integration}' before proceeding.",
                    error="integration_required",
                    data={"required_integration": tool.required_integration}
                )

        try:
            result = await tool.handler(**params)
            if isinstance(result, PrimitiveResult):
                return result
            # Wrap non-PrimitiveResult returns
            return PrimitiveResult(
                success=True,
                output=str(result),
                data={"raw": result} if not isinstance(result, str) else {},
            )
        except TypeError as e:
            return PrimitiveResult(
                success=False,
                output=f"Tool '{name}' parameter error: {str(e)}",
                error=str(e),
            )
        except Exception as e:
            return PrimitiveResult(
                success=False,
                output=f"Tool '{name}' execution failed: {str(e)}",
                error=str(e),
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        by_source: Dict[str, int] = {}
        by_risk: Dict[str, int] = {}
        for tool in self._tools.values():
            by_source[tool.source] = by_source.get(tool.source, 0) + 1
            by_risk[tool.risk_level] = by_risk.get(tool.risk_level, 0) + 1

        return {
            "total_tools": len(self._tools),
            "by_source": by_source,
            "by_risk": by_risk,
            "tool_names": list(self._tools.keys()),
        }


# =============================================================================
# GLOBAL SINGLETON
# =============================================================================

_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.initialize()
    return _registry
