"""
Zoom Plugin for Meeting Scheduling
Integrates with Zoom API to create meetings
"""
from typing import Dict, Any, List
import os
import asyncio
from datetime import datetime, timedelta
import hashlib

from .plugins import BasePlugin

class ZoomPlugin(BasePlugin):
    """Zoom meeting integration plugin"""
    
    def __init__(self):
        super().__init__("zoom", "Zoom meeting scheduling and management")
        self.api_key = os.getenv("ZOOM_API_KEY", "")
        self.api_secret = os.getenv("ZOOM_API_SECRET", "")
        self.scheduled_meetings = []  # In production, use actual Zoom API
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute Zoom action"""
        action = step.get("action", "").lower()
        parameters = step.get("parameters", {})
        
        if "schedule" in action or "create" in action:
            return await self._schedule_meeting(parameters)
        elif "cancel" in action or "delete" in action:
            return await self._cancel_meeting(parameters)
        elif "list" in action:
            return await self._list_meetings(parameters)
        else:
            return {
                "status": "failed",
                "error": f"Unknown Zoom action: {action}"
            }
    
    async def _schedule_meeting(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a Zoom meeting"""
        try:
            # Extract parameters
            topic = parameters.get("topic", "Meeting")
            date_str = parameters.get("date", "")
            time_str = parameters.get("time", "")
            duration = parameters.get("duration", 60)  # minutes
            attendees = parameters.get("attendees", [])
            
            # Parse date and time
            meeting_datetime = self._parse_datetime(date_str, time_str)
            
            # In production, call actual Zoom API
            # For now, simulate meeting creation
            meeting = {
                "id": self._generate_meeting_id(),
                "topic": topic,
                "start_time": meeting_datetime,
                "duration": duration,
                "join_url": f"https://zoom.us/j/{self._generate_meeting_id()}",
                "password": self._generate_password(),
                "attendees": attendees,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.scheduled_meetings.append(meeting)
            
            # Simulate API delay
            await asyncio.sleep(0.3)
            
            return {
                "status": "completed",
                "result": f"Zoom meeting scheduled: {topic}",
                "meeting": meeting,
                "output": {
                    "meeting_id": meeting["id"],
                    "join_url": meeting["join_url"],
                    "password": meeting["password"]
                }
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Failed to schedule Zoom meeting: {str(e)}"
            }
    
    async def _cancel_meeting(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a Zoom meeting"""
        meeting_id = parameters.get("meeting_id", "")
        
        # Find and remove meeting
        for i, meeting in enumerate(self.scheduled_meetings):
            if meeting["id"] == meeting_id:
                self.scheduled_meetings.pop(i)
                return {
                    "status": "completed",
                    "result": f"Meeting {meeting_id} cancelled"
                }
        
        return {
            "status": "failed",
            "error": f"Meeting {meeting_id} not found"
        }
    
    async def _list_meetings(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List scheduled meetings"""
        return {
            "status": "completed",
            "result": f"Found {len(self.scheduled_meetings)} meetings",
            "meetings": self.scheduled_meetings
        }
    
    def _parse_datetime(self, date_str: str, time_str: str) -> str:
        """Parse date and time strings into ISO format"""
        # Handle relative dates like "tomorrow"
        if "tomorrow" in date_str.lower():
            target_date = datetime.now() + timedelta(days=1)
        elif "today" in date_str.lower():
            target_date = datetime.now()
        else:
            # Try to parse date string
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d")
            except:
                target_date = datetime.now() + timedelta(days=1)
        
        # Parse time
        try:
            # Handle formats like "2pm", "14:00", "2:00 PM"
            time_str = time_str.lower().replace(" ", "")
            if "pm" in time_str:
                hour = int(time_str.replace("pm", "").split(":")[0])
                if hour != 12:
                    hour += 12
                minute = 0
                if ":" in time_str:
                    minute = int(time_str.split(":")[1].replace("pm", ""))
            elif "am" in time_str:
                hour = int(time_str.replace("am", "").split(":")[0])
                if hour == 12:
                    hour = 0
                minute = 0
                if ":" in time_str:
                    minute = int(time_str.split(":")[1].replace("am", ""))
            else:
                # 24-hour format
                parts = time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
            
            target_date = target_date.replace(hour=hour, minute=minute, second=0)
        except:
            # Default to 2 PM
            target_date = target_date.replace(hour=14, minute=0, second=0)
        
        return target_date.isoformat()
    
    def _generate_meeting_id(self) -> str:
        """Generate a meeting ID"""
        timestamp = str(datetime.utcnow().timestamp())
        return hashlib.md5(timestamp.encode()).hexdigest()[:10]
    
    def _generate_password(self) -> str:
        """Generate a meeting password"""
        return hashlib.md5(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:6]
    
    def get_capabilities(self) -> List[str]:
        return ["zoom", "meeting", "video_call", "schedule_meeting", "create_meeting"]
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate Zoom meeting parameters"""
        required = ["topic", "date", "time"]
        return all(key in parameters for key in required)
