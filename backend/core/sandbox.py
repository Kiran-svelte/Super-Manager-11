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
    fill_form, run_python, PrimitiveResult, PRIMITIVES,
)

logger = logging.getLogger(__name__)


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

    SAFE_PRIMITIVES = {"web_search", "browse_page", "scrape_data", "generate_image"}
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

        # Detect which primitives are used
        primitives_used = set()
        for prim_name in list(self.SAFE_PRIMITIVES) + list(self.RISKY_PRIMITIVES):
            # Match function calls like: await web_search(...) or web_search(...)
            if re.search(rf'\b{prim_name}\s*\(', code):
                primitives_used.add(prim_name)

        # Determine risk level
        risky_used = primitives_used & self.RISKY_PRIMITIVES
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
        Classify a single primitive action call.

        Returns same format as classify().
        """
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
                "reason": f"Unknown primitive: {primitive_name}",
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
        Execute a single primitive action call.
        Used for simple <action> tags.
        """
        if primitive_name not in PRIMITIVES:
            return ExecutionResult(
                success=False,
                output=f"Unknown primitive: {primitive_name}. Available: {', '.join(PRIMITIVES.keys())}",
                error="unknown_primitive",
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
                output=f"Primitive {primitive_name} timed out after {self.timeout}s",
                error="timeout",
                primitives_used=[primitive_name],
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=f"Primitive {primitive_name} failed: {str(e)}",
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
            # Primitives (the only way to interact with the outside world)
            "web_search": web_search,
            "browse_page": browse_page,
            "scrape_data": scrape_data,
            "generate_image": generate_image,
            "fill_form": fill_form,
            "run_python": run_python,
            # Context from previous steps
            "context": context,
        }

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
