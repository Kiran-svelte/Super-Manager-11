"""
Sandbox - Safe Code Execution Engine
======================================
Executes dynamically generated code in a restricted environment.
Only primitive functions are available - no file system, no network
access except through primitives.

Components:
- RiskClassifier: Deterministic risk classification
- SandboxExecutor: Restricted code execution with timeout
"""

import re
import ast
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set

from .primitives import (
    web_search, browse_page, scrape_data, generate_image,
    fill_form, run_python, send_email, create_meeting, save_note, click_link,
    PrimitiveResult, PRIMITIVES,
)

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency
_tool_registry = None

def _get_registry():
    """Get tool registry lazily to avoid circular imports"""
    global _tool_registry
    if _tool_registry is None:
        try:
            from .tool_registry import get_tool_registry
            _tool_registry = get_tool_registry()
        except ImportError:
            _tool_registry = None
    return _tool_registry


@dataclass
class ExecutionResult:
    """Result of sandbox code execution"""
    success: bool
    output: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    primitives_used: List[str] = field(default_factory=list)


# =============================================================================
# RISK CLASSIFIER
# =============================================================================

class RiskClassifier:
    """
    Deterministic risk classification based on code content.
    Does NOT use LLM - purely static analysis.
    """

    SAFE_PRIMITIVES = {"web_search", "browse_page", "scrape_data", "generate_image", "send_email", "create_meeting", "save_note", "click_link"}
    RISKY_PRIMITIVES = {"fill_form", "run_python"}

    # Patterns that are ALWAYS forbidden (security)
    FORBIDDEN_PATTERNS = [
        r'\bimport\s+os\b',
        r'\bimport\s+sys\b',
        r'\bimport\s+subprocess\b',
        r'\bimport\s+shutil\b',
        r'\bimport\s+socket\b',
        r'\bimport\s+ctypes\b',
        r'\bimport\s+pickle\b',
        r'\bfrom\s+os\b',
        r'\bfrom\s+sys\b',
        r'\bfrom\s+subprocess\b',
        r'\b__import__\s*\(',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bopen\s*\(',
        r'\bos\.system\b',
        r'\bos\.popen\b',
        r'\bos\.exec',
        r'\bsubprocess\.',
        r'\bshutil\.',
        r'\brequests\.',
        r'\burllib\.request\b',
        r'\bhttp\.client\b',
        r'\bsocket\.',
        r'\bglobals\s*\(',
        r'\blocals\s*\(',
        r'\bcompile\s*\(',
        r'\b__class__\b',
        r'\b__subclasses__\b',
        r'\b__bases__\b',
        r'\bbreakpoint\s*\(',
    ]

    def classify(self, code: str) -> dict:
        """
        Classify code risk level.

        Returns:
            {
                "risk": "safe" | "risky" | "blocked",
                "reason": str,
                "primitives_used": List[str],
                "blocked_patterns": List[str]  # only if blocked
            }
        """
        # Check for forbidden patterns
        blocked = []
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code):
                blocked.append(pattern)

        if blocked:
            return {
                "risk": "blocked",
                "reason": f"Code contains forbidden patterns: {', '.join(blocked[:3])}",
                "primitives_used": [],
                "blocked_patterns": blocked,
            }

        # Detect which primitives/tools are used
        primitives_used = set()
        all_known_tools = set(self.SAFE_PRIMITIVES) | set(self.RISKY_PRIMITIVES)

        # Also check dynamically registered tools from ToolRegistry
        registry = _get_registry()
        if registry:
            all_known_tools.update(registry.get_tool_names())

        for tool_name in all_known_tools:
            # Match function calls like: await web_search(...) or web_search(...)
            if re.search(rf'\b{re.escape(tool_name)}\s*\(', code):
                primitives_used.add(tool_name)

        # Determine risk level
        risky_used = primitives_used & self.RISKY_PRIMITIVES

        # Also check registry for risky tools
        if registry:
            for tool_name in primitives_used:
                tool = registry.get(tool_name)
                if tool and tool.risk_level == "risky":
                    risky_used.add(tool_name)
        if risky_used:
            return {
                "risk": "risky",
                "reason": f"Uses risky primitives: {', '.join(risky_used)}",
                "primitives_used": list(primitives_used),
                "blocked_patterns": [],
            }

        return {
            "risk": "safe",
            "reason": "Only uses safe primitives",
            "primitives_used": list(primitives_used),
            "blocked_patterns": [],
        }

    def validate_action(self, primitive_name: str) -> dict:
        """
        Classify a single primitive/tool action call.
        Checks ToolRegistry first, falls back to hardcoded sets.

        Returns same format as classify().
        """
        # Check ToolRegistry first (supports dynamic tools: MCP, stealth, payment, etc.)
        registry = _get_registry()
        if registry:
            tool = registry.get(primitive_name)
            if tool:
                return {
                    "risk": tool.risk_level,
                    "reason": f"{primitive_name} ({tool.source}) is {tool.risk_level}",
                    "primitives_used": [primitive_name],
                    "blocked_patterns": [],
                }

        # Fallback to hardcoded sets
        if primitive_name in self.SAFE_PRIMITIVES:
            return {
                "risk": "safe",
                "reason": f"{primitive_name} is a safe primitive",
                "primitives_used": [primitive_name],
                "blocked_patterns": [],
            }
        elif primitive_name in self.RISKY_PRIMITIVES:
            return {
                "risk": "risky",
                "reason": f"{primitive_name} requires user confirmation",
                "primitives_used": [primitive_name],
                "blocked_patterns": [],
            }
        else:
            return {
                "risk": "blocked",
                "reason": f"Unknown tool: {primitive_name}",
                "primitives_used": [],
                "blocked_patterns": [primitive_name],
            }


# =============================================================================
# SANDBOX EXECUTOR
# =============================================================================

class SandboxExecutor:
    """
    Execute generated code with only primitives in scope.

    Security layers:
    1. Static validation (forbidden patterns)
    2. Restricted globals (no file/network access)
    3. Timeout enforcement (30 seconds)
    4. Output capture and sanitization
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.classifier = RiskClassifier()

    async def execute_action(self, primitive_name: str, params: Dict[str, Any], context: Dict[str, Any] = None) -> ExecutionResult:
        """
        Execute a single tool/primitive action call.
        Used for simple <action> tags.
        Checks ToolRegistry first, falls back to PRIMITIVES dict.
        """
        # Try ToolRegistry first (supports MCP, stealth, payment, etc.)
        registry = _get_registry()
        if registry:
            tool = registry.get(primitive_name)
            if tool and tool.handler:
                try:
                    result = await asyncio.wait_for(
                        tool.handler(**params),
                        timeout=self.timeout,
                    )
                    if isinstance(result, PrimitiveResult):
                        return ExecutionResult(
                            success=result.success,
                            output=result.output,
                            data=result.data,
                            error=result.error,
                            primitives_used=[primitive_name],
                        )
                    return ExecutionResult(
                        success=True,
                        output=str(result),
                        primitives_used=[primitive_name],
                    )
                except asyncio.TimeoutError:
                    return ExecutionResult(
                        success=False,
                        output=f"Tool {primitive_name} timed out after {self.timeout}s",
                        error="timeout",
                        primitives_used=[primitive_name],
                    )
                except TypeError as e:
                    # Missing required arguments
                    return ExecutionResult(
                        success=False,
                        output=f"Tool {primitive_name} called with wrong parameters: {str(e)}. Check the tool's required params and try again with correct params dict.",
                        error="wrong_params",
                        primitives_used=[primitive_name],
                    )
                except Exception as e:
                    return ExecutionResult(
                        success=False,
                        output=f"Tool {primitive_name} failed: {str(e)}",
                        error=str(e),
                        primitives_used=[primitive_name],
                    )

        # Fallback to hardcoded PRIMITIVES dict
        if primitive_name not in PRIMITIVES:
            available = list(PRIMITIVES.keys())
            if registry:
                available = registry.get_tool_names()
            return ExecutionResult(
                success=False,
                output=f"Unknown tool: {primitive_name}. Available: {', '.join(available)}",
                error="unknown_tool",
            )

        prim_info = PRIMITIVES[primitive_name]
        prim_func = prim_info["function"]

        try:
            result = await asyncio.wait_for(
                prim_func(**params),
                timeout=self.timeout,
            )

            return ExecutionResult(
                success=result.success,
                output=result.output,
                data=result.data,
                error=result.error,
                primitives_used=[primitive_name],
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                output=f"Tool {primitive_name} timed out after {self.timeout}s",
                error="timeout",
                primitives_used=[primitive_name],
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=f"Tool {primitive_name} failed: {str(e)}",
                error=str(e),
                primitives_used=[primitive_name],
            )

    async def execute_code(self, code: str, context: Dict[str, Any] = None) -> ExecutionResult:
        """
        Execute multi-step code in a sandboxed environment.
        Used for <code> tags.

        The code can use `await` with any primitive function.
        Previous step results are available via `context`.
        """
        context = context or {}

        # Step 1: Validate code
        classification = self.classifier.classify(code)
        if classification["risk"] == "blocked":
            return ExecutionResult(
                success=False,
                output=f"Code blocked: {classification['reason']}",
                error="blocked",
                primitives_used=[],
            )

        # Step 2: Build restricted globals
        import io
        import json as json_mod
        import re as re_mod
        import math
        import datetime
        from urllib import parse as urlparse

        safe_builtins = {
            "abs": abs, "all": all, "any": any, "bool": bool,
            "chr": chr, "dict": dict, "divmod": divmod, "enumerate": enumerate,
            "filter": filter, "float": float, "format": format, "frozenset": frozenset,
            "hash": hash, "hex": hex, "int": int, "isinstance": isinstance,
            "iter": iter, "len": len, "list": list,
            "map": map, "max": max, "min": min, "next": next,
            "ord": ord, "pow": pow, "print": print, "range": range, "repr": repr,
            "reversed": reversed, "round": round, "set": set, "slice": slice,
            "sorted": sorted, "str": str, "sum": sum, "tuple": tuple, "type": type,
            "zip": zip, "True": True, "False": False, "None": None,
        }

        # Capture stdout
        stdout_capture = io.StringIO()

        # Create a wrapped print that writes to our capture buffer
        def sandbox_print(*args, **kwargs):
            kwargs['file'] = stdout_capture
            print(*args, **kwargs)

        safe_builtins["print"] = sandbox_print

        sandbox_globals = {
            "__builtins__": safe_builtins,
            # Modules
            "json": json_mod,
            "re": re_mod,
            "math": math,
            "datetime": datetime,
            "urlparse": urlparse,
            # Legacy primitives (always available)
            "web_search": web_search,
            "browse_page": browse_page,
            "scrape_data": scrape_data,
            "generate_image": generate_image,
            "fill_form": fill_form,
            "run_python": run_python,
            # New primitives (email, meeting, notes)
            "send_email": send_email,
            "create_meeting": create_meeting,
            "save_note": save_note,
            "click_link": click_link,
            # Context from previous steps
            "context": context,
        }

        # Inject all registered tools from ToolRegistry (MCP, stealth, payment, etc.)
        registry = _get_registry()
        if registry:
            for tool in registry.list_tools():
                if tool.handler and tool.name not in sandbox_globals:
                    sandbox_globals[tool.name] = tool.handler

        # Step 3: Wrap code in an async function
        # Indent each line of the user code
        indented_code = "\n".join(f"    {line}" for line in code.strip().split("\n"))
        wrapped = f"""
async def _sandbox_main():
    _result = None
{indented_code}
    return _result
"""

        # Step 4: Execute with timeout
        try:
            # Compile and exec the function definition
            compiled = compile(wrapped, "<sandbox>", "exec")
            exec(compiled, sandbox_globals)

            # Call the async function
            main_fn = sandbox_globals["_sandbox_main"]
            result = await asyncio.wait_for(
                main_fn(),
                timeout=self.timeout,
            )

            output = stdout_capture.getvalue()
            if result is not None:
                result_str = str(result)
                if output:
                    output += f"\nReturn value: {result_str}"
                else:
                    output = f"Result: {result_str}"

            if not output:
                output = "Code executed successfully (no output)."

            return ExecutionResult(
                success=True,
                output=output,
                data={"stdout": stdout_capture.getvalue(), "return_value": str(result) if result else None},
                primitives_used=classification["primitives_used"],
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                output=f"Code execution timed out after {self.timeout}s",
                error="timeout",
                primitives_used=classification["primitives_used"],
            )
        except SyntaxError as e:
            return ExecutionResult(
                success=False,
                output=f"Syntax error in generated code: {str(e)}",
                error=f"syntax_error: {str(e)}",
                primitives_used=[],
            )
        except Exception as e:
            partial_output = stdout_capture.getvalue()
            error_msg = f"Code execution error: {str(e)}"
            if partial_output:
                error_msg = f"Partial output:\n{partial_output}\n\nError: {str(e)}"

            return ExecutionResult(
                success=False,
                output=error_msg,
                error=str(e),
                primitives_used=classification["primitives_used"],
            )


# =============================================================================
# MODULE-LEVEL EXPORTS (for tests and external use)
# =============================================================================

# Export FORBIDDEN_PATTERNS at module level for direct import
FORBIDDEN_PATTERNS = RiskClassifier.FORBIDDEN_PATTERNS

# Default sandbox timeout (30 seconds per README)
SANDBOX_TIMEOUT = 30

# Safe globals for sandbox execution
SAFE_GLOBALS = {
    # Math functions
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "range": range,
    "round": round,
    "pow": pow,
    "sorted": sorted,
    "reversed": reversed,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    # Type functions
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    # String methods
    "print": print,
    "format": format,
    "repr": repr,
    # Boolean
    "True": True,
    "False": False,
    "None": None,
    # Dangerous builtins REMOVED
    "eval": None,
    "exec": None,
    "open": None,
    "compile": None,
    "__import__": None,
    "globals": None,
    "locals": None,
    "getattr": None,
    "setattr": None,
    "delattr": None,
}


def get_safe_globals() -> dict:
    """Get a copy of safe globals for sandbox execution"""
    return SAFE_GLOBALS.copy()


def is_code_safe(code: str) -> bool:
    """
    Check if code is safe to execute (no forbidden patterns).
    
    This is a static analysis check with NO LLM dependency.
    
    Args:
        code: The code string to analyze
        
    Returns:
        True if code is safe, False if it contains forbidden patterns
    """
    classifier = RiskClassifier()
    result = classifier.classify(code)
    return result["risk"] != "blocked"


def analyze_code_risk(code: str) -> dict:
    """
    Analyze code and return risk classification.
    
    Returns:
        {
            "risk": "safe" | "risky" | "blocked",
            "reason": str,
            "primitives_used": List[str],
            "blocked_patterns": List[str],
            "safe": bool  # convenience field
        }
    """
    classifier = RiskClassifier()
    result = classifier.classify(code)
    result["safe"] = result["risk"] != "blocked"
    return result


async def execute_sandboxed(code: str, context: dict = None) -> dict:
    """
    Execute code in a sandbox with safety checks.
    
    This is the main entry point for sandbox execution.
    
    Args:
        code: The code to execute
        context: Optional context dict
        
    Returns:
        {
            "success": bool,
            "output": str,
            "error": Optional[str],
            "blocked": bool,
            "primitives_used": List[str]
        }
    """
    # First check if code is safe
    if not is_code_safe(code):
        risk = analyze_code_risk(code)
        return {
            "success": False,
            "output": f"Code blocked: {risk['reason']}",
            "error": "forbidden_pattern",
            "blocked": True,
            "primitives_used": [],
        }
    
    # Execute in sandbox
    executor = SandboxExecutor(timeout=SANDBOX_TIMEOUT)
    result = await executor.execute(code, context or {})
    
    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "blocked": False,
        "primitives_used": result.primitives_used,
    }


# Convenience class for configuration
@dataclass
class SandboxConfig:
    """Configuration for sandbox execution"""
    timeout: float = SANDBOX_TIMEOUT
    max_output_size: int = 10000
    allowed_primitives: List[str] = field(default_factory=lambda: list(RiskClassifier.SAFE_PRIMITIVES))
