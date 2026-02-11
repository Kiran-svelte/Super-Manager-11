"""
Tool Registry
==============
Auto-registers all available tools and provides lookup/prompt generation.
"""

from typing import Dict, Optional

from .base import Tool, ToolResult
from .web_search import WebSearchTool
from .browse_website import BrowseWebsiteTool
from .image_gen import ImageGenerationTool
from .email_tool import SendEmailTool
from .meeting import CreateMeetingTool
from .payment import PaymentLinkTool
from .python_exec import PythonExecTool
from .memory_tool import MemoryTool
from .reminder_tool import ReminderTool
from .document_tool import DocumentTool
from .weather_tool import WeatherTool
from .datetime_tool import DateTimeTool


class ToolRegistry:
    """Registry of all available tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register all built-in tools"""
        default_tools = [
            WebSearchTool(),
            BrowseWebsiteTool(),
            ImageGenerationTool(),
            SendEmailTool(),
            CreateMeetingTool(),
            PaymentLinkTool(),
            PythonExecTool(),
            MemoryTool(),
            ReminderTool(),
            DocumentTool(),
            WeatherTool(),
            DateTimeTool(),
        ]
        for tool in default_tools:
            self.tools[tool.name] = tool

    def register(self, tool: Tool):
        """Register a custom tool"""
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def get_tools_prompt(self) -> str:
        """Generate the tools section of the system prompt"""
        return "\n\n".join(tool.get_schema() for tool in self.tools.values())

    def list_tools(self) -> list:
        """List all registered tool names"""
        return list(self.tools.keys())


__all__ = ["Tool", "ToolResult", "ToolRegistry"]
