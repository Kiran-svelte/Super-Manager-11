"""
Tool Base Classes
=================
Foundation for the general-purpose tool system.
Each tool is self-describing and independently executable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ToolResult:
    """Result returned by any tool execution"""
    success: bool
    output: str  # Human-readable text for LLM to consume
    data: Dict[str, Any] = field(default_factory=dict)  # Structured data for frontend
    error: Optional[str] = None


class Tool(ABC):
    """
    Abstract base for all tools.

    Each tool must define:
    - name: unique identifier
    - description: what the tool does (shown to LLM)
    - parameters: dict of param_name -> {description, required, type}
    - requires_confirmation: whether user must confirm before execution
    - execute(): the actual implementation
    """
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    requires_confirmation: bool = False

    @abstractmethod
    async def execute(self, **params) -> ToolResult:
        """Execute the tool with given parameters"""
        pass

    def get_schema(self) -> str:
        """Format tool description for the system prompt"""
        lines = [f"- {self.name}: {self.description}"]
        if self.requires_confirmation:
            lines[0] += " (requires user confirmation)"
        lines.append("  Parameters:")
        for param_name, param_info in self.parameters.items():
            req = "required" if param_info.get("required") else "optional"
            desc = param_info.get("description", "")
            default = param_info.get("default")
            line = f"    - {param_name}: {desc} ({req})"
            if default is not None:
                line += f", default: {default}"
            lines.append(line)
        return "\n".join(lines)
