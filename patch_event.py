import sys

def patch():
    path = 'backend/core/adaptive_agent.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add 'integration_needed' to docstring
    content = content.replace("          - confirm_needed: Risky action needs user confirmation", "          - confirm_needed: Risky action needs user confirmation\n          - integration_needed: Required OAuth integration missing")

    # Hook into result processing for ACTION
    old_action_res = """                yield AgentEvent(
                    type="action_result",
                    content=result.output[:500] if result.output else "No output",
                    data=result.data,
                )"""

    new_action_res = """                if result.error == "integration_required":
                    yield AgentEvent(
                        type="integration_needed",
                        content=f"Connecting to {result.data.get('required_integration')} is required to proceed.",
                        data={
                            "service": result.data.get("required_integration"),
                            "status": "not_connected"
                        }
                    )
                    return # Pause execution until user connects

                yield AgentEvent(
                    type="action_result",
                    content=result.output[:500] if result.output else "No output",
                    data=result.data,
                )"""

    content = content.replace(old_action_res, new_action_res)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched.")

if __name__ == '__main__':
    patch()
