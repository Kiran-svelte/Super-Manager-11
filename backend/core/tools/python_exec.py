"""
Python Execution Tool - Sandboxed
===================================
Run simple Python code for calculations and data processing.
Sandboxed to prevent dangerous operations.
"""

import io
import sys
import traceback

from .base import Tool, ToolResult


# Allowed built-in modules for sandboxed execution
ALLOWED_MODULES = {"math", "random", "datetime", "json", "re", "statistics", "collections", "itertools", "functools"}

# Blocked names that should never be accessible
BLOCKED_NAMES = {
    "exec", "eval", "compile", "__import__", "open", "input",
    "breakpoint", "exit", "quit", "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "dir",
    "os", "sys", "subprocess", "shutil", "pathlib",
}


class PythonExecTool(Tool):
    name = "run_python"
    description = "Execute Python code for calculations, math, or data processing (sandboxed)"
    parameters = {
        "code": {"description": "Python code to execute", "required": True, "type": "string"},
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        code = params.get("code", "")

        if not code:
            return ToolResult(success=False, output="No code provided.", error="missing_code")

        # Safety check
        for blocked in BLOCKED_NAMES:
            if blocked in code:
                return ToolResult(
                    success=False,
                    output=f"Code contains blocked operation: {blocked}. Only math, data processing, and calculations are allowed.",
                    error="blocked_operation",
                )

        # Check for import statements - only allow safe modules
        import re
        imports = re.findall(r"(?:import|from)\s+([\w.]+)", code)
        for mod in imports:
            base_mod = mod.split(".")[0]
            if base_mod not in ALLOWED_MODULES:
                return ToolResult(
                    success=False,
                    output=f"Module '{base_mod}' is not allowed. Allowed modules: {', '.join(sorted(ALLOWED_MODULES))}",
                    error="blocked_module",
                )

        # Execute in sandboxed environment
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout

        safe_globals = {"__builtins__": {}}
        # Add safe builtins
        safe_builtins = [
            "abs", "all", "any", "bin", "bool", "chr", "dict", "divmod",
            "enumerate", "filter", "float", "format", "frozenset", "hash",
            "hex", "int", "isinstance", "issubclass", "iter", "len", "list",
            "map", "max", "min", "next", "oct", "ord", "pow", "print",
            "range", "repr", "reversed", "round", "set", "slice", "sorted",
            "str", "sum", "tuple", "type", "zip",
        ]
        import builtins
        for name in safe_builtins:
            safe_globals["__builtins__"][name] = getattr(builtins, name)

        # Allow safe imports
        import math, random, datetime, json as json_mod
        import statistics, collections, itertools, functools
        safe_globals["math"] = math
        safe_globals["random"] = random
        safe_globals["datetime"] = datetime
        safe_globals["json"] = json_mod
        safe_globals["re"] = re
        safe_globals["statistics"] = statistics
        safe_globals["collections"] = collections
        safe_globals["itertools"] = itertools
        safe_globals["functools"] = functools

        try:
            sys.stdout = stdout_capture
            exec(code, safe_globals)
            sys.stdout = old_stdout

            output = stdout_capture.getvalue()
            if not output:
                # Try to get the last expression value
                try:
                    lines = code.strip().split("\n")
                    last_line = lines[-1].strip()
                    if not last_line.startswith(("def ", "class ", "if ", "for ", "while ", "import ", "from ", "#", "print(")):
                        result = eval(last_line, safe_globals)
                        if result is not None:
                            output = str(result)
                except Exception:
                    pass

            if not output:
                output = "(Code executed successfully, no output)"

            return ToolResult(
                success=True,
                output=f"Python output:\n{output}",
                data={"code": code, "output": output},
            )

        except Exception as e:
            sys.stdout = old_stdout
            error_msg = traceback.format_exc().split("\n")[-2] if traceback.format_exc() else str(e)
            return ToolResult(
                success=False,
                output=f"Python error: {error_msg}",
                error=str(e),
            )
        finally:
            sys.stdout = old_stdout
