import sys

def patch():
    path = 'backend/core/adaptive_agent.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old = "context: Dict[str, Any] = {}  # Accumulated results from steps"
    new = "context: Dict[str, Any] = {'user_id': user_id, 'session_id': session_id}  # Accumulated results from steps"
    
    new_content = content.replace(old, new)

    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Patched AdaptiveAgent.")
    else:
        print("Not Found.")

if __name__ == '__main__':
    patch()
