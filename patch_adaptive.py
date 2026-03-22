import sys
import re

def patch():
    path = 'backend/core/adaptive_agent.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Search for context initialization
    # It might be `context: Dict[str, Any] = None` or inside `def run`

    # Actually look at what we've seen: `context = {}` isn't clearly visible in what we grep'd earlier.
    # Let me check `run` body!
    # I'll just regex replace inside `def run` where `context={}` might be.
    # If not found, I'll print the relevant code snippet.
    
    match = re.search(r"context\s*=\s*\{[^\}]*\}", content)
    if match:
        print(f"Found context initialization: {match.group(0)}")
        new_content = content.replace("context = {}", "context = {'user_id': user_id, 'session_id': session_id}")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Patched.")
    else:
        print("Could not find context initialization.")

if __name__ == '__main__':
    patch()
