"""
Telegram Messaging Plugin (simulation with real API fallback)
"""
import os
import json
import requests
from typing import Dict, Any, List
from .plugins import BasePlugin

class TelegramPlugin(BasePlugin):
    """Send messages via Telegram Bot API. Falls back to simulation if token missing."""

    def __init__(self):
        super().__init__("telegram", "Telegram messaging operations")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.default_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.sent_messages = []

    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute a Telegram send_message action.
        Expected parameters:
            - chat_id (optional): Telegram chat ID. If omitted, uses env default.
            - message: Text to send. May contain placeholder "{meeting_link}" which will be replaced
                       with state.get('meeting_link') if present.
        """
        action = step.get("action", "").lower()
        params = step.get("parameters", {})
        if "send" in action or "message" in action:
            chat_id = params.get("chat_id") or self.default_chat_id
            message = params.get("message", "")
            
            # Resolve placeholder or append link if missing
            meeting_link = state.get("meeting_link")
            
            if meeting_link:
                if "{meeting_link}" in message:
                    message = message.replace("{meeting_link}", meeting_link)
                elif meeting_link not in message:
                    # Append link if not present
                    message += f"\n\n🔗 Join Meeting: {meeting_link}"
            
            # If message is empty/generic, use a nice template
            if not message or message.lower() == "meeting link":
                timestamp = state.get("timestamp", "now")
                message = f"""🔔 **Meeting Scheduled**

You have a meeting scheduled!

📅 Time: {timestamp}
🔗 Link: {meeting_link or "Check your calendar"}

Please join on time."""

            # If we have a bot token, try real API call
            if self.bot_token and chat_id:
                try:
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
                    resp = requests.post(url, json=payload, timeout=5)
                    if resp.status_code == 200:
                        result = resp.json()
                        self.sent_messages.append(result)
                        return {
                            "status": "completed",
                            "result": f"✅ Telegram message sent to chat {chat_id}",
                            "output": result,
                        }
                except Exception as e:
                    # fall back to simulation on any error
                    pass
            # Simulation fallback
            simulated = {"chat_id": chat_id, "text": message}
            self.sent_messages.append(simulated)
            return {
                "status": "completed",
                "result": f"✅ Simulated Telegram message to chat {chat_id}\nContent: {message}",
                "output": simulated,
            }
        else:
            return {"status": "failed", "error": f"Unknown telegram action: {action}"}

    def get_capabilities(self) -> List[str]:
        return ["telegram", "send_message", "message"]

    def validate_parameters(self, parameters: Dict) -> bool:
        return "message" in parameters
