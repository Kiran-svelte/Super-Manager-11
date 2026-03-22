import sys

def rewrite_integrations():
    with open('backend/routes/integrations.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # The goal is to drop from class IntegrationStore: until class FallbackRouter:
    import re
    # Match the entire block safely
    pattern = re.compile(
        r'# ==.*?# In-Memory Integration Store.*?def get_integration_store\(\).*?return _integration_store\n+',
        re.DOTALL
    )
    
    replacement = """# ============================================================================= 
# Integration Store (Supabase backed)
# ============================================================================= 

from ..core.integration_manager.integration_store import integration_store

def get_integration_store():
    return integration_store

"""
    
    new_content, count = pattern.subn(replacement, content)
    if count > 0:
        with open('backend/routes/integrations.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully replaced block in integrations.py!")
    else:
        print("Pattern not found!")

if __name__ == '__main__':
    rewrite_integrations()
