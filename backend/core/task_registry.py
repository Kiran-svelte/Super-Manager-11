"""
Task Registry - Defines all available tasks the system can perform
"""
from typing import Dict, List, Any

class Task:
    def __init__(self, task_id: str, name: str, description: str, required_info: List[str], plugins: List[str]):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.required_info = required_info  # What info we need from user
        self.plugins = plugins  # Which plugins to use
        
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "required_info": self.required_info,
            "plugins": self.plugins
        }

class TaskRegistry:
    """Registry of all available tasks"""
    
    def __init__(self):
        self.tasks = {
            "schedule_meeting": Task(
                task_id="schedule_meeting",
                name="Schedule Meeting",
                description="Schedule a video meeting. Use 'Jitsi' for instant links (no login), or 'Google Meet'/'Zoom' (requires manual link copying).",
                required_info=["time", "participants"],
                plugins=["browser_meeting", "calendar", "email", "telegram"]
            ),
            "book_restaurant": Task(
                task_id="book_restaurant",
                name="Book Restaurant",
                description="Make a restaurant reservation",
                required_info=["restaurant_name", "date", "time", "number_of_people"],
                plugins=["phone_call", "booking"]
            ),
            "plan_trip": Task(
                task_id="plan_trip",
                name="Plan Trip",
                description="Plan a vacation or trip including accommodation and activities",
                required_info=["destination", "dates", "accommodation_type", "activities"],
                plugins=["booking", "search", "phone_call"]
            ),
            "plan_birthday": Task(
                task_id="plan_birthday",
                name="Plan Birthday Party",
                description="Organize a birthday party with venue, cake, and activities",
                required_info=["location", "date", "venue_type", "number_of_guests"],
                plugins=["phone_call", "booking", "search"]
            ),
            "send_message": Task(
                task_id="send_message",
                name="Send Message",
                description="Send a message via email, Telegram, or SMS",
                required_info=["recipient", "message_content", "channel"],
                plugins=["email", "telegram", "sms"]
            ),
            "search_information": Task(
                task_id="search_information",
                name="Search Information",
                description="Search for information on the web",
                required_info=["search_query"],
                plugins=["search"]
            )
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all available tasks"""
        return [task.to_dict() for task in self.tasks.values()]
    
    def get_task(self, task_id: str) -> Task:
        """Get a specific task by ID"""
        return self.tasks.get(task_id)
    
    def get_task_descriptions_for_ai(self) -> str:
        """Get formatted task descriptions for AI matching"""
        descriptions = []
        for task in self.tasks.values():
            descriptions.append(f"- {task.name}: {task.description}")
        return "\n".join(descriptions)

# Global registry instance
_task_registry = None

def get_task_registry() -> TaskRegistry:
    global _task_registry
    if _task_registry is None:
        _task_registry = TaskRegistry()
    return _task_registry
