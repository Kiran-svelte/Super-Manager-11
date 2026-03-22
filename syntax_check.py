import ast
import sys
import os

files = [
    r"d:\GOOGLE PROJECT\backend\routes\messaging.py",
    r"d:\GOOGLE PROJECT\backend\core\strategy_store.py",
    r"d:\GOOGLE PROJECT\backend\core\task_classifier.py",
    r"d:\GOOGLE PROJECT\backend\core\adaptive_agent.py",
    r"d:\GOOGLE PROJECT\backend\core\brain.py",
    r"d:\GOOGLE PROJECT\backend\routes\api.py",
    r"d:\GOOGLE PROJECT\backend\main.py"
]

print("=" * 80)
print("PYTHON SYNTAX VERIFICATION")
print("=" * 80)
print()

errors_found = False

for file_path in files:
    try:
        if not os.path.exists(file_path):
            print(f"✗ {file_path}")
            print(f"  ERROR: FILE NOT FOUND")
            errors_found = True
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print(f"✓ {file_path}")
    except SyntaxError as e:
        print(f"✗ {file_path}")
        print(f"  SYNTAX ERROR at Line {e.lineno}: {e.msg}")
        if e.text:
            print(f"  Code: {e.text.strip()}")
        errors_found = True
    except Exception as e:
        print(f"✗ {file_path}")
        print(f"  ERROR: {type(e).__name__}: {e}")
        errors_found = True

print()
print("=" * 80)
if errors_found:
    print("RESULT: Some files have errors or are missing")
    sys.exit(1)
else:
    print("RESULT: All files passed syntax verification!")
    sys.exit(0)
