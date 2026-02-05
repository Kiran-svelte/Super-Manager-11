"""
WhatsApp Plugin for Messaging
Integrates with WhatsApp Business API
"""
from typing import Dict, Any, List
import os
import asyncio
from datetime import datetime

from .plugins import BasePlugin

class WhatsAppPlugin(BasePlugin):
    """WhatsApp messaging integration plugin"""
    
    def __init__(self):
        super().__init__("whatsapp", "WhatsApp messaging operations")
        self.api_key = os.getenv("WHATSAPP_API_KEY", "")
        self.phone_number = os.getenv("WHATSAPP_PHONE_NUMBER", "")
        self.sent_messages = []  # In production, use actual WhatsApp API
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute WhatsApp action"""
        action = step.get("action", "").lower()
        parameters = step.get("parameters", {})
        
        if "send" in action or "message" in action:
            return await self._send_message(parameters)
        elif "read" in action or "check" in action:
            return await self._check_messages(parameters)
        else:
            return {
                "status": "failed",
                "error": f"Unknown WhatsApp action: {action}"
            }
    
    async def _send_message(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send a WhatsApp message"""
        try:
            # Extract parameters
            to = parameters.get("to", "")
            message = parameters.get("message", "")
            phone = parameters.get("phone", "")
            
            # Validate
            if not to and not phone:
                return {
                    "status": "failed",
                    "error": "Recipient (to or phone) is required"
                }
            
            if not message:
                return {
                    "status": "failed",
                    "error": "Message content is required"
                }
            
            # In production, call actual WhatsApp Business API
            # For now, simulate message sending
            sent_message = {
                "id": self._generate_message_id(),
                "to": to or phone,
                "message": message,
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }
            
            self.sent_messages.append(sent_message)
            
            # Simulate API delay
            await asyncio.sleep(0.2)
            
            return {
                "status": "completed",
                "result": f"WhatsApp message sent to {sent_message['to']}",
                "message": sent_message,
                "output": {
                    "message_id": sent_message["id"],
                    "recipient": sent_message["to"]
                }
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Failed to send WhatsApp message: {str(e)}"
            }
    
    async def _check_messages(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check sent messages"""
        return {
            "status": "completed",
            "result": f"Found {len(self.sent_messages)} sent messages",
            "messages": self.sent_messages
        }
    
    def _generate_message_id(self) -> str:
        """Generate a message ID"""
        import hashlib
        timestamp = str(datetime.utcnow().timestamp())
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def get_capabilities(self) -> List[str]:
        return ["whatsapp", "message", "send_whatsapp", "chat"]
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate WhatsApp message parameters"""
        has_recipient = "to" in parameters or "phone" in parameters
        has_message = "message" in parameters
        return has_recipient and has_message
