import sys

def process():
    with open('backend/routes/integrations.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # The goal is to replace the mock IntegrationStore with our new one
    # while preserving the API surface layer. 
    # Notice that `backend.core.integration_manager.integration_store` is exactly what we need.
    new_content = content.replace(
        "from typing import Optional, List, Dict, Any",
        "from typing import Optional, List, Dict, Any\nfrom ..core.integration_manager.integration_store import integration_store"
    )

    # Now let's remove the mock IntegrationStore class and just leave the dictionary `AVAILABLE_INTEGRATIONS`
    with open('update_integrations.py_out', 'w', encoding='utf-8') as f:
        pass
    
if __name__ == '__main__':
    process()
