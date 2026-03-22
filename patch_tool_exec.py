import sys

def patch():
    path = 'backend/core/tool_registry.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Import Integration Manager at top
    import_block = "from .primitives import PRIMITIVES, PrimitiveResult\nfrom .integration_manager.integration_store import integration_store"
    content = content.replace("from .primitives import PRIMITIVES, PrimitiveResult", import_block)

    old_execute = """        if not tool.handler:
            return PrimitiveResult(
                success=False,
                output=f"Tool '{name}' has no handler registered.",
                error="no_handler",
            )

        try:
"""
    new_execute = """        if not tool.handler:
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
"""
    new_content = content.replace(old_execute, new_execute)

    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Patched ToolRegistry.execute")
    else:
        print("Not Found or already patched.")

if __name__ == '__main__':
    patch()
