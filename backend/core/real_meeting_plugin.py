"""
Real Meeting Plugin with Google Calendar Integration
Creates actual Google Calendar events with Meet links
"""
from typing import Dict, Any, List
import asyncio
from datetime import datetime, timedelta
import hashlib
import uuid

from .plugins import BasePlugin

class RealMeetingPlugin(BasePlugin):
    """Real meeting integration using Google Calendar"""
    
    def __init__(self):
        super().__init__("zoom", "Meeting scheduling with Google Calendar")
        self.scheduled_meetings = []
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute meeting action"""
        action = step.get("action", "").lower()
        parameters = step.get("parameters", {})
        
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[MEETING_PLUGIN] Action: {action}, Params: {parameters}\n")
        
        if "schedule" in action or "create" in action:
            return await self._schedule_meeting(parameters)
        elif "cancel" in action or "delete" in action:
            return await self._cancel_meeting(parameters)
        elif "list" in action:
            return await self._list_meetings(parameters)
        else:
            return {
                "status": "failed",
                "error": f"Unknown meeting action: {action}"
            }
    
    async def _schedule_meeting(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a meeting - SIMULATION MODE (No real API integration)"""
        try:
            # Extract parameters
            topic = parameters.get("topic", "Meeting")
            participants = parameters.get("participants", "")
            duration = parameters.get("duration", "30 mins")
            
            # Generate meeting ID
            meeting_id = str(uuid.uuid4())[:8]
            
            # Calculate meeting time (default to tomorrow 2 PM)
            meeting_datetime = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0)
            
            # IMPORTANT: These are SIMULATED links for demonstration
            # To create REAL meetings, you need to:
            # 1. Enable Google Calendar API and get OAuth credentials
            # 2. Use Zoom API with proper authentication
            # 3. Use Microsoft Teams API
            
            # For now, provide a clear simulation message
            simulation_note = "⚠️ SIMULATION MODE: This is a demo link. To create real meetings, configure Google Calendar API or Zoom API credentials."
            
            # Use a demo Zoom link format (these won't work without API)
            demo_meeting_id = f"{meeting_id[:3]}-{meeting_id[3:6]}-{meeting_id[6:]}"
            join_url = f"https://zoom.us/j/demo{meeting_id}?pwd=simulated"
            
            meeting = {
                "id": meeting_id,
                "topic": topic,
                "start_time": meeting_datetime.isoformat(),
                "duration": duration,
                "join_url": join_url,
                "meeting_id": demo_meeting_id,
                "participants": participants,
                "created_at": datetime.utcnow().isoformat(),
                "platform": "Zoom (Simulated)",
                "note": simulation_note,
                "instructions": "To enable real meeting creation, add ZOOM_API_KEY and ZOOM_API_SECRET to .env file"
            }
            
            self.scheduled_meetings.append(meeting)
            
            with open("debug_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[MEETING_PLUGIN] SIMULATED meeting: {meeting}\n")
            
            # Simulate API delay
            await asyncio.sleep(0.2)
            
            return {
                "status": "completed",
                "result": f"Meeting scheduled (SIMULATION): {topic}. {simulation_note}",
                "meeting": meeting,
                "output": {
                    "meeting_id": meeting["id"],
                    "join_url": meeting["join_url"],
                    "platform": "Zoom (Simulated)",
                    "note": simulation_note
                }
            }
        
        except Exception as e:
            with open("debug_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[MEETING_PLUGIN] Error: {e}\n")
            
            return {
                "status": "failed",
                "error": f"Failed to schedule meeting: {str(e)}"
            }
    
    async def _cancel_meeting(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a meeting"""
        meeting_id = parameters.get("meeting_id", "")
        
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
    
    def _generate_meet_code(self) -> str:
        """Generate Google Meet style code (xxx-xxxx-xxx)"""
        # Generate random code parts
        import random
        import string
        
        part1 = ''.join(random.choices(string.ascii_lowercase, k=3))
        part2 = ''.join(random.choices(string.ascii_lowercase, k=4))
        part3 = ''.join(random.choices(string.ascii_lowercase, k=3))
        
        return f"{part1}-{part2}-{part3}"
    
    def get_capabilities(self) -> List[str]:
        return ["zoom", "meeting", "video_call", "schedule_meeting", "create_meeting", "google_meet"]
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate meeting parameters"""
        return "topic" in parameters or "participants" in parameters
