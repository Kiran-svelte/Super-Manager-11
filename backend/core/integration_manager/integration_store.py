from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.database_supabase import get_supabase_client
from backend.core.integration_manager.crypto_vault import vault
import logging

logger = logging.getLogger(__name__)

class IntegrationStore:
    """
    Manages secure storage and retrieval of OAuth integration tokens 
    from the Supabase database.
    """
    def __init__(self):
        self.supabase = get_supabase_client()
        self.table_name = "user_integrations"

    AVAILABLE_INTEGRATIONS = {
        "google_calendar": {
            "name": "Google Calendar",
            "icon": "📅",
            "description": "Schedule meetings, manage events",
            "provider": "google",
            "scopes": ["calendar.events", "calendar.readonly"],
            "category": "productivity"
        },
        "zoom": {
            "name": "Zoom",
            "icon": "📹",
            "description": "Video conferencing",
            "provider": "zoom",
            "scopes": ["meeting:write", "meeting:read"],
            "category": "communication"
        },
        "gmail": {
            "name": "Gmail",
            "icon": "📧",
            "description": "Send and read emails",
            "provider": "google",
            "scopes": ["gmail.send", "gmail.readonly"],
            "category": "communication"
        },
        "outlook": {
            "name": "Outlook",
            "icon": "📧",
            "description": "Microsoft email and calendar",
            "provider": "microsoft",
            "scopes": ["Mail.Send", "Calendars.ReadWrite"],
            "category": "communication"
        },
        "google_drive": {
            "name": "Google Drive",
            "icon": "📂",
            "description": "Access and share files",
            "provider": "google",
            "scopes": ["drive.readonly", "drive.file"],
            "category": "storage"
        },
        "slack": {
            "name": "Slack",
            "icon": "💬",
            "description": "Send messages to channels",
            "provider": "slack",
            "scopes": ["chat:write", "channels:read"],
            "category": "communication"
        },
        "github": {
            "name": "GitHub",
            "icon": "🐙",
            "description": "Manage repos and issues",
            "provider": "github",
            "scopes": ["repo", "issues"],
            "category": "development"
        },
        "trello": {
            "name": "Trello",
            "icon": "📋",
            "description": "Manage project boards",
            "provider": "trello",
            "scopes": ["read", "write"],
            "category": "project_management"
        },
        "razorpay": {
            "name": "Razorpay",
            "icon": "💳",
            "description": "Create payment links",
            "provider": "razorpay",
            "scopes": ["payments"],
            "category": "payments"
        },
        "stripe": {
            "name": "Stripe",
            "icon": "💳",
            "description": "Process payments",
            "provider": "stripe",
            "scopes": ["payments"],
            "category": "payments"
        }
    }

    def get_user_integrations(self, user_id: str) -> List[Dict]:
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table(self.table_name).select("*").eq("user_id", user_id).execute()
            connected = []
            if response.data:
                for record in response.data:
                    if record.get("status") == "connected":
                        service_name = record.get("provider")
                        connected.append({
                            "id": record.get("id"),
                            "service": service_name,
                            "name": self.AVAILABLE_INTEGRATIONS.get(service_name, {}).get("name", service_name),
                            "icon": self.AVAILABLE_INTEGRATIONS.get(service_name, {}).get("icon", "🔗"),
                            "status": record.get("status"),
                            "connected_at": record.get("updated_at"),
                            "last_used_at": record.get("updated_at"),
                            "provider": service_name,
                            "scopes": record.get("scopes", []),
                        })
            return connected
        except Exception as e:
            logger.error(f"Error fetching integrations for user {user_id}: {e}")
            return []

    def get_available_integrations(self, user_id: str) -> List[Dict]:
        connected_services = set(item['service'] for item in self.get_user_integrations(user_id))
        available = []
        for service_name, info in self.AVAILABLE_INTEGRATIONS.items():
            if service_name not in connected_services:
                available.append({
                    "service": service_name,
                    "name": info["name"],
                    "icon": info["icon"],
                    "description": info["description"],
                    "provider": info["provider"],
                    "category": info["category"],
                })
        return available

    def is_connected(self, user_id: str, service: str) -> bool:
        record = self.get_integration(user_id, service)
        return record is not None and record.get("status") == "connected"


    def _encrypt_token_data(self, token_data: Dict[str, Any]) -> str:
        """Encrypts the OAuth payload (JSON) using AES-256-GCM."""
        import json
        json_str = json.dumps(token_data)
        return vault.encrypt(json_str)

    def _decrypt_token_data(self, encrypted_str: str) -> Dict[str, Any]:
        """Decrypts the OAuth payload back to JSON."""
        import json
        json_str = vault.decrypt(encrypted_str)
        return json.loads(json_str)

    def store_integration(
        self, 
        user_id: str, 
        provider: str, 
        token_data: Dict[str, Any],
        scopes: list,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Securely stores an integration token. 
        Replaces the old token if the connection exists.
        """
        if not self.supabase:
            logger.error("Supabase client not available")
            return False

        encrypted_tokens = self._encrypt_token_data(token_data)
        
        data = {
            "user_id": user_id,
            "provider": provider,
            "encrypted_tokens": encrypted_tokens,
            "scopes": scopes,
            "metadata": metadata or {},
            "status": "connected",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Using upsert requires provider + user_id primary/unique composite key
            self.supabase.table(self.table_name).upsert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error storing integration {provider} for user {user_id}: {e}")
            return False

    def get_integration(self, user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves and decrypts the integration token data.
        """
        if not self.supabase:
            return None

        try:
            response = self.supabase.table(self.table_name).select("*").match({
                "user_id": user_id, 
                "provider": provider
            }).execute()
            
            if response.data and len(response.data) > 0:
                record = response.data[0]
                if record.get("status") != "connected":
                    return None
                    
                encrypted_str = record.get("encrypted_tokens")
                if encrypted_str:
                    record["tokens"] = self._decrypt_token_data(encrypted_str)
                    del record["encrypted_tokens"]
                return record
                
        except Exception as e:
            logger.error(f"Error fetching integration {provider} for user {user_id}: {e}")
            
        return None

    def revoke_integration(self, user_id: str, provider: str) -> bool:
        """
        Revokes an integration by changing its status to revoked and removing tokens.
        """
        if not self.supabase:
            return False

        data = {
            "user_id": user_id,
            "provider": provider,
            "encrypted_tokens": None,
            "status": "revoked",
            "updated_at": datetime.utcnow().isoformat()
        }

        try:
            self.supabase.table(self.table_name).upsert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error revoking integration {provider} for user {user_id}: {e}")
            return False





    def connect_integration(
        self, user_id: str, service: str,
        access_token: str = None, refresh_token: str = None,
        scopes: list = None, expires_at: str = None
    ) -> Dict[str, Any]:
        """Alias to maintain compatibility with original API routes."""
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
        """Alias for revoke_integration to map to older API requirements"""
        return self.revoke_integration(user_id, service)


integration_store = IntegrationStore()
