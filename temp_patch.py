import re
import os

with open(r'd:\GOOGLE PROJECT\backend\routes\integrations.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('async def connect_integration(integration_id: str, request: IntegrationConnectRequest):', 'async def connect_integration(integration_id: str, request: IntegrationConnectRequest, req: Request):')

old_auth = '''        auth_url = oauth_manager.get_authorization_url(
            provider=integration_id,
            user_id=request.user_id
        )'''

new_auth = '''        base_url = str(req.base_url).rstrip("/")
        if "onrender.com" in base_url and base_url.startswith("http://"):
            base_url = base_url.replace("http://", "https://")
        redirect_uri = f"{base_url}/api/oauth/callback"
        
        auth_url = oauth_manager.get_authorization_url(
            provider=integration_id,
            user_id=request.user_id,
            override_redirect_uri=redirect_uri
        )'''

content = content.replace(old_auth, new_auth)

with open(r'd:\GOOGLE PROJECT\backend\routes\integrations.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("done")
