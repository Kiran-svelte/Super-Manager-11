import sys

def patch():
    path = 'backend/core/tool_registry.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_register_block = """            self.register(ToolDef(
                name=name,
                description=info["description"],
                parameters=info["params"],
                returns=info["returns"],
                risk_level=info["risk"],
                source="primitive",
                handler=info["function"],
            ))"""

    new_register_block = """            req_int = None
            if name == "send_email":
                req_int = "gmail"
            elif name == "create_meeting":
                req_int = "google_calendar"
            
            self.register(ToolDef(
                name=name,
                description=info["description"],
                parameters=info["params"],
                returns=info["returns"],
                risk_level=info["risk"],
                source="primitive",
                handler=info["function"],
                required_integration=req_int
            ))"""

    new_content = content.replace(old_register_block, new_register_block)

    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Patched ToolRegistry built-in registrations.")
    else:
        print("Not Found or already patched.")

if __name__ == '__main__':
    patch()
