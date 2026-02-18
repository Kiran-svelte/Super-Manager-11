"""
MCP Client - Model Context Protocol Integration
==================================================
Connects to MCP servers and discovers tools at runtime.
Uses the official Anthropic MCP Python SDK.

MCP servers provide tools that the agent can use dynamically.
Tools are namespaced as mcp__{server}__{tool} to avoid collisions.
"""

import os
import json
import logging
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path

from .primitives import PrimitiveResult

logger = logging.getLogger(__name__)

# Feature detection
MCP_AVAILABLE = False
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    pass


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    enabled: bool = True


# Risk classification patterns for MCP tools
SAFE_PATTERNS = ["list", "get", "read", "search", "find", "show", "describe", "count", "query"]
RISKY_PATTERNS = ["create", "update", "delete", "send", "write", "modify", "set", "add", "remove", "post", "put", "patch"]
BLOCKED_PATTERNS = ["exec", "execute", "run", "eval", "install", "uninstall", "sudo", "rm", "drop"]


def _classify_mcp_tool_risk(tool_name: str, description: str = "") -> str:
    """Classify risk level of an MCP tool based on its name and description"""
    name_lower = tool_name.lower()
    desc_lower = description.lower()

    # Check blocked patterns first
    for pattern in BLOCKED_PATTERNS:
        if pattern in name_lower or (desc_lower and f"{pattern} " in desc_lower):
            return "blocked"

    # Check risky patterns
    for pattern in RISKY_PATTERNS:
        if pattern in name_lower:
            return "risky"

    # Check safe patterns
    for pattern in SAFE_PATTERNS:
        if pattern in name_lower:
            return "safe"

    # Default: risky (safer to ask for confirmation)
    return "risky"


class MCPClientManager:
    """
    Manages connections to MCP servers and discovers tools.
    Tools are automatically registered with the ToolRegistry.
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._sessions: Dict[str, Any] = {}  # name -> (session, read, write)
        self._server_tools: Dict[str, List[str]] = {}  # server_name -> tool_names
        self._initialized = False

    def _load_config(self) -> List[MCPServerConfig]:
        """Load MCP server configurations from mcp_servers.json"""
        config_paths = [
            Path(__file__).parent.parent / "mcp_servers.json",
            Path(__file__).parent.parent.parent / "mcp_servers.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        data = json.load(f)

                    servers = []
                    for name, cfg in data.get("servers", {}).items():
                        # Resolve env var references like ${GITHUB_TOKEN}
                        env = {}
                        for k, v in cfg.get("env", {}).items():
                            if v.startswith("${") and v.endswith("}"):
                                env_var = v[2:-1]
                                env[k] = os.getenv(env_var, "")
                            else:
                                env[k] = v

                        servers.append(MCPServerConfig(
                            name=name,
                            command=cfg["command"],
                            args=cfg.get("args", []),
                            env=env,
                            enabled=cfg.get("enabled", True),
                        ))

                    logger.info(f"[MCP] Loaded {len(servers)} server configs from {config_path}")
                    return servers

                except Exception as e:
                    logger.warning(f"[MCP] Failed to load config from {config_path}: {e}")

        return []

    async def initialize(self):
        """Load config and connect to all enabled MCP servers"""
        if not MCP_AVAILABLE:
            logger.info("[MCP] MCP SDK not installed. Skipping MCP initialization.")
            return

        if self._initialized:
            return

        configs = self._load_config()
        for config in configs:
            if config.enabled:
                try:
                    await self.connect_server(config)
                except Exception as e:
                    logger.warning(f"[MCP] Failed to connect to {config.name}: {e}")

        self._initialized = True

    async def connect_server(self, config: MCPServerConfig):
        """Connect to an MCP server and discover its tools"""
        if not MCP_AVAILABLE:
            logger.warning("[MCP] MCP SDK not available")
            return

        logger.info(f"[MCP] Connecting to server: {config.name} ({config.command} {' '.join(config.args)})")

        try:
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env={**os.environ, **config.env} if config.env else None,
            )

            # Create the stdio client connection
            read, write = await stdio_client(server_params).__aenter__()
            session = ClientSession(read, write)
            await session.__aenter__()
            await session.initialize()

            self._servers[config.name] = config
            self._sessions[config.name] = (session, read, write)

            # Discover and register tools
            await self._discover_and_register_tools(config.name, session)

            logger.info(f"[MCP] Connected to {config.name}")

        except Exception as e:
            logger.error(f"[MCP] Connection to {config.name} failed: {e}")
            raise

    async def _discover_and_register_tools(self, server_name: str, session):
        """Discover tools from MCP server and register them"""
        try:
            from .tool_registry import get_tool_registry, ToolDef

            tools_result = await session.list_tools()
            registry = get_tool_registry()
            tool_names = []

            for tool in tools_result.tools:
                # Namespace the tool name
                namespaced_name = f"mcp__{server_name}__{tool.name}"
                risk_level = _classify_mcp_tool_risk(tool.name, tool.description or "")

                # Build parameter description from input schema
                params_desc = "params (dict)"
                if tool.inputSchema and "properties" in tool.inputSchema:
                    param_parts = []
                    required = tool.inputSchema.get("required", [])
                    for param_name, param_info in tool.inputSchema["properties"].items():
                        param_type = param_info.get("type", "any")
                        req_marker = "" if param_name in required else ", optional"
                        param_parts.append(f"{param_name} ({param_type}{req_marker})")
                    params_desc = ", ".join(param_parts) if param_parts else "no parameters"

                # Create a handler closure for this specific tool
                _server = server_name
                _tool_name = tool.name

                async def make_handler(srv=_server, tn=_tool_name):
                    async def handler(**kwargs):
                        return await self.call_tool(srv, tn, kwargs)
                    return handler

                handler = await make_handler()

                registry.register(ToolDef(
                    name=namespaced_name,
                    description=tool.description or f"MCP tool from {server_name}",
                    parameters=params_desc,
                    returns=f"Result from {server_name}.{tool.name}",
                    risk_level=risk_level,
                    source="mcp",
                    handler=handler,
                    parameter_schema=tool.inputSchema,
                ))

                tool_names.append(namespaced_name)

            self._server_tools[server_name] = tool_names
            logger.info(f"[MCP] Discovered {len(tool_names)} tools from {server_name}: {tool_names}")

        except Exception as e:
            logger.error(f"[MCP] Tool discovery failed for {server_name}: {e}")

    async def call_tool(self, server_name: str, tool_name: str, args: Dict[str, Any]) -> PrimitiveResult:
        """Call a tool on an MCP server"""
        session_data = self._sessions.get(server_name)
        if not session_data:
            return PrimitiveResult(
                success=False,
                output=f"MCP server '{server_name}' not connected.",
                error="server_not_connected",
            )

        session = session_data[0]

        try:
            result = await session.call_tool(tool_name, args)

            # Extract text content from result
            output_parts = []
            data = {}
            for content in result.content:
                if hasattr(content, "text"):
                    output_parts.append(content.text)
                elif hasattr(content, "data"):
                    data["raw"] = content.data

            output = "\n".join(output_parts) if output_parts else "Tool executed (no text output)"

            return PrimitiveResult(
                success=not result.isError if hasattr(result, "isError") else True,
                output=output,
                data={
                    "server": server_name,
                    "tool": tool_name,
                    **data,
                },
            )

        except Exception as e:
            return PrimitiveResult(
                success=False,
                output=f"MCP tool {server_name}.{tool_name} failed: {str(e)}",
                error=str(e),
            )

    async def disconnect_server(self, server_name: str):
        """Disconnect from an MCP server and unregister its tools"""
        session_data = self._sessions.pop(server_name, None)
        if session_data:
            session = session_data[0]
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass

        # Unregister tools
        tool_names = self._server_tools.pop(server_name, [])
        if tool_names:
            try:
                from .tool_registry import get_tool_registry
                registry = get_tool_registry()
                for name in tool_names:
                    registry.unregister(name)
            except Exception:
                pass

        self._servers.pop(server_name, None)
        logger.info(f"[MCP] Disconnected from {server_name}")

    def get_connected_servers(self) -> List[str]:
        """Get list of connected server names"""
        return list(self._sessions.keys())

    def get_server_tools(self, server_name: str) -> List[str]:
        """Get tools registered by a specific server"""
        return self._server_tools.get(server_name, [])

    def get_status(self) -> Dict[str, Any]:
        """Get MCP client status"""
        return {
            "available": MCP_AVAILABLE,
            "initialized": self._initialized,
            "connected_servers": self.get_connected_servers(),
            "total_tools": sum(len(t) for t in self._server_tools.values()),
            "servers": {
                name: {
                    "tools": self._server_tools.get(name, []),
                    "command": cfg.command,
                }
                for name, cfg in self._servers.items()
            },
        }

    async def shutdown(self):
        """Disconnect from all servers"""
        for server_name in list(self._sessions.keys()):
            await self.disconnect_server(server_name)


# Global singleton
_mcp_client: Optional[MCPClientManager] = None


def get_mcp_client() -> MCPClientManager:
    """Get or create the global MCP client manager"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClientManager()
    return _mcp_client
