import sys

def patch():
    with open('backend/core/integration_manager/integration_store.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Add connect_integration alias method
    alias_method = """
    def connect_integration(
        self, user_id: str, service: str,
        access_token: str = None, refresh_token: str = None,
        scopes: list = None, expires_at: str = None
    ) -> Dict[str, Any]:
        \"\"\"Alias to maintain compatibility with original API routes.\"\"\"
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at
        }
        success = self.store_integration(
            user_id=user_id,
            provider=service,
            token_data=token_data,
            scopes=scopes or []
        )
        return {
            "service": service,
            "status": "connected" if success else "failed",
            "provider": self.AVAILABLE_INTEGRATIONS.get(service, {}).get("provider", service)
        }

    def revoke_by_service(self, user_id: str, service: str) -> bool:
        \"\"\"Alias for revoke_integration to map to older API requirements\"\"\"
        return self.revoke_integration(user_id, service)
"""
    
    if 'def connect_integration' not in content:
        # Find the end of the class where we can append this
        content += "\n" + alias_method + "\n"
        with open('backend/core/integration_manager/integration_store.py', 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == '__main__':
    patch()
