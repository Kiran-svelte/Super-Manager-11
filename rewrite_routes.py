import sys

def rewrite_integrations():
    with open('backend/routes/integrations.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Drop the Mock Integration Store code completely
    # It starts at class IntegrationStore: and ends around global integration store singleton
    
    import re
    # We will just replace from class IntegrationStore to get_integration_store
    
    # Actually it's easier to just do simple string replacements.
    part1_marker = "# ============================================================================= \n# In-Memory Integration Store (production would use Supabase)"
    part2_marker = "# ============================================================================= \n# Fallback Router"
    
    if part1_marker in content and part2_marker in content:
        start_idx = content.find(part1_marker)
        end_idx = content.find(part2_marker)
        
        replacement = """# ============================================================================= 
# Integration Store (Supabase backed)
# ============================================================================= 

from ..core.integration_manager.integration_store import integration_store

def get_integration_store():
    return integration_store

"""
        new_content = content[:start_idx] + replacement + content[end_idx:]
        
        with open('backend/routes/integrations.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully rewrote backend/routes/integrations.py")
    else:
        print("Markers not found!")

if __name__ == '__main__':
    rewrite_integrations()
