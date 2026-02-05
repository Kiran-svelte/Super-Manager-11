"""
Plugin Architecture for Extensibility
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import asyncio

class BasePlugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
    
    @abstractmethod
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute plugin action"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        pass
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate input parameters"""
        return True

class GeneralPlugin(BasePlugin):
    """General purpose plugin"""
    
    def __init__(self):
        super().__init__("general", "General purpose actions")
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute general action"""
        action = step.get("action", "")
        parameters = step.get("parameters", {})
        
        # Simulate execution
        await asyncio.sleep(0.1)
        
        return {
            "status": "completed",
            "result": f"Executed: {action}",
            "output": parameters
        }
    
    def get_capabilities(self) -> List[str]:
        return ["general", "process", "execute"]

class CalendarPlugin(BasePlugin):
    """Calendar integration plugin"""
    
    def __init__(self):
        super().__init__("calendar", "Calendar and scheduling operations")
        self.events = []  # In production, connect to actual calendar API
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute calendar action"""
        action = step.get("action", "").lower()
        parameters = step.get("parameters", {})
        
        if "check" in action and "availability" in action:
            return self._check_availability(parameters)
        elif "schedule" in action or "book" in action or "add" in action:
            # Check availability first
            if not self._is_available(parameters.get("date"), parameters.get("time")):
                return {
                    "status": "failed",
                    "error": "Conflict detected: Time slot is already booked."
                }
            
            event = {
                "title": parameters.get("title", "Event"),
                "date": parameters.get("date"),
                "time": parameters.get("time"),
                "duration": parameters.get("duration", "1 hour")
            }
            self.events.append(event)
            return {
                "status": "completed",
                "result": f"Scheduled: {event['title']}",
                "event": event
            }
        elif "list" in action or "show" in action:
            return {
                "status": "completed",
                "result": f"Found {len(self.events)} events",
                "events": self.events
            }
        else:
            return {
                "status": "failed",
                "error": f"Unknown calendar action: {action}"
            }

    def _is_available(self, date: str, time: str) -> bool:
        """Check if a slot is free (simple exact match for now)"""
        for event in self.events:
            if event.get("date") == date and event.get("time") == time:
                return False
        return True

    def _check_availability(self, parameters: Dict) -> Dict[str, Any]:
        """Check availability action"""
        date = parameters.get("date")
        time = parameters.get("time")
        is_free = self._is_available(date, time)
        return {
            "status": "completed",
            "available": is_free,
            "result": "Slot available" if is_free else "Slot busy"
        }
    
    def get_capabilities(self) -> List[str]:
        return ["schedule", "book", "calendar", "appointment", "meeting"]

class EmailPlugin(BasePlugin):
    """Email integration plugin"""
    
    def __init__(self):
        super().__init__("email", "Email operations")
        self.sent_emails = []  # In production, connect to actual email API
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute email action"""
        action = step.get("action", "").lower()
        parameters = step.get("parameters", {})
        
        if "send" in action:
            with open("debug_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[PLUGIN] Email params: {parameters}\n")
            
            email = {
                "to": parameters.get("to"),
                "subject": parameters.get("subject", ""),
                "body": parameters.get("body", ""),
                "sent_at": "now"
            }
            self.sent_emails.append(email)
            return {
                "status": "completed",
                "result": f"Email sent to {email['to']}",
                "email": email
            }
        elif "read" in action or "check" in action:
            return {
                "status": "completed",
                "result": f"Found {len(self.sent_emails)} emails",
                "emails": self.sent_emails
            }
        else:
            return {
                "status": "failed",
                "error": f"Unknown email action: {action}"
            }
    
    def get_capabilities(self) -> List[str]:
        return ["send_email", "read_email", "email", "message"]

class SearchPlugin(BasePlugin):
    """Search plugin"""
    
    def __init__(self):
        super().__init__("search", "Search operations")
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute search action"""
        parameters = step.get("parameters", {})
        query = parameters.get("query", "")
        
        # Simulate search
        await asyncio.sleep(0.2)
        
        results = [
            {"title": f"Result for: {query}", "url": f"https://example.com/{query}"},
            {"title": f"Another result: {query}", "url": f"https://example.com/{query}-2"}
        ]
        
        return {
            "status": "completed",
            "result": f"Found {len(results)} results",
            "results": results
        }
    
    def get_capabilities(self) -> List[str]:
        return ["search", "find", "lookup"]

class PluginManager:
    """Manages all plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self._register_default_plugins()

    def _register_default_plugins(self):
        """Register default plugins"""
        from .browser_meeting_plugin import BrowserMeetingPlugin
        from .real_email_plugin import RealEmailPlugin
        from .whatsapp_plugin import WhatsAppPlugin
        from .phone_booking_plugin import PhoneCallPlugin, BookingPlugin
        from .zoom_real_plugin import ZoomMeetingPlugin
        from .telegram_plugin import TelegramPlugin
        
        default_plugins = [
            GeneralPlugin(),
            CalendarPlugin(),
            RealEmailPlugin(),
            SearchPlugin(),
            ZoomMeetingPlugin(),
            BrowserMeetingPlugin(),
            WhatsAppPlugin(),
            TelegramPlugin(),  # New Telegram plugin
            PhoneCallPlugin(),
            BookingPlugin()
        ]
        
        for plugin in default_plugins:
            self.register(plugin)

    def register(self, plugin: BasePlugin):
        """Register a plugin"""
        self.plugins[plugin.name] = plugin
    
    def get_plugin(self, name: str) -> BasePlugin:
        """Get plugin by name"""
        return self.plugins.get(name, self.plugins.get("general"))
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all registered plugins"""
        return self.plugins
    
    def get_available_capabilities(self) -> List[str]:
        """Get all available capabilities"""
        capabilities = set()
        for plugin in self.plugins.values():
            if plugin.enabled:
                capabilities.update(plugin.get_capabilities())
        return list(capabilities)
