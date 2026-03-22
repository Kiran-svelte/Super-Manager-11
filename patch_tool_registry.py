import sys

def patch():
    path = 'backend/core/tool_registry.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old = "    parameter_schema: Optional[Dict[str, Any]] = None  # JSON Schema (for MCP tools)"
    new = "    parameter_schema: Optional[Dict[str, Any]] = None  # JSON Schema (for MCP tools)\n    required_integration: Optional[str] = None  # Needed integration (e.g. 'gmail', 'google_calendar')"
    new_content = content.replace(old, new)

    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Patched ToolDef.")
    else:
        print("Not Found or already patched.")

if __name__ == '__main__':
    patch()
