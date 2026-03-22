import sys

def patch():
    with open('backend/core/integration_manager/integration_store.py', 'r', encoding='utf-8') as f:
        old_store = f.read()

    insert_text = """
    AVAILABLE_INTEGRATIONS = {
        "google_calendar": {
            "name": "Google Calendar",
            "icon": "📅",
            "description": "Schedule meetings, manage events",
            "provider": "google",
            "scopes": ["calendar.events", "calendar.readonly"],
            "category": "productivity"
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
"""
    if 'AVAILABLE_INTEGRATIONS' not in old_store:
        new_store = old_store.replace('self.table_name = "user_integrations"', 'self.table_name = "user_integrations"\n' + insert_text)
        with open('backend/core/integration_manager/integration_store.py', 'w', encoding='utf-8') as f:
            f.write(new_store)

if __name__ == '__main__':
    patch()
