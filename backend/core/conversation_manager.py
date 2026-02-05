"""
Conversation manager for multi‑stage planning and meeting scheduling.
"""

from __future__ import annotations

import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from .session_store import get_session_store

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class ConversationStage:
    """Represents a stage in a multi‑turn conversation."""

    def __init__(self, stage_type: str, data: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.stage_type = stage_type  # clarification, option_selection, confirmation, execution
        self.data = data
        self.completed = False
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "id": self.id,
            "stage_type": self.stage_type,
            "data": self.data,
            "completed": self.completed,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ConversationStage":
        """Deserialize from a dictionary produced by :meth:`to_dict`."""
        stage = ConversationStage(data["stage_type"], data["data"])
        stage.id = data["id"]
        stage.completed = data["completed"]
        stage.created_at = data["created_at"]
        return stage


class ConversationSession:
    """Manages a conversation session consisting of multiple stages."""

    def __init__(self, session_id: str, initial_intent: Dict[str, Any]):
        self.session_id = session_id
        self.initial_intent = initial_intent
        self.stages: List[ConversationStage] = []
        self.context: Dict[str, Any] = {}
        self.current_stage_index = 0
        self.created_at = datetime.utcnow().isoformat()

    def add_stage(self, stage: ConversationStage) -> None:
        """Append a new stage to the session."""
        self.stages.append(stage)

    def get_current_stage(self) -> Optional[ConversationStage]:
        """Return the stage currently awaiting user input, or ``None`` if finished."""
        if self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None

    def complete_current_stage(self, result: Dict[str, Any]) -> None:
        """Mark the active stage as completed and merge its result into the session context."""
        if self.current_stage_index < len(self.stages):
            self.stages[self.current_stage_index].completed = True
            self.context.update(result)
            self.current_stage_index += 1

    def is_complete(self) -> bool:
        """Return ``True`` when every stage has been marked completed."""
        return all(stage.completed for stage in self.stages)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the whole session for persistence."""
        return {
            "session_id": self.session_id,
            "initial_intent": self.initial_intent,
            "stages": [stage.to_dict() for stage in self.stages],
            "context": self.context,
            "current_stage_index": self.current_stage_index,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ConversationSession":
        """Recreate a :class:`ConversationSession` from its persisted dictionary form."""
        session = ConversationSession(data["session_id"], data["initial_intent"])
        session.stages = [ConversationStage.from_dict(s) for s in data["stages"]]
        session.context = data["context"]
        session.current_stage_index = data["current_stage_index"]
        session.created_at = data["created_at"]
        return session


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class MultiStageConversationManager:
    """Orchestrates the creation, persistence and execution of conversation sessions."""

    def __init__(self) -> None:
        self.session_store = get_session_store()
        print("[CONV_MANAGER] Initialized with session store")

    def log_debug(self, message: str):
        """Log debug message to file"""
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] [CONV_MANAGER] {message}\n")

    # ---------------------------------------------------------------------
    # Session lifecycle
    # ---------------------------------------------------------------------
    async def create_session(self, intent: Dict[str, Any]) -> ConversationSession:
        """Create a fresh session, build its stages, persist it and return it."""
        session_id = str(uuid.uuid4())
        session = ConversationSession(session_id, intent)
        await self._build_stages(session, intent)
        self.save_session(session)
        print(f"[CONV_MANAGER] Created and saved session {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Load a persisted session from the store, or ``None`` if missing."""
        data = self.session_store.get_session(session_id)
        if data:
            session = ConversationSession.from_dict(data)
            print(f"[CONV_MANAGER] Loaded session {session_id}")
            return session
        print(f"[CONV_MANAGER] Session {session_id} not found")
        return None

    def save_session(self, session: ConversationSession) -> None:
        """Persist the given session."""
        self.session_store.save_session(session.session_id, session.to_dict())
        print(f"[CONV_MANAGER] Saved session {session.session_id}")

    # ---------------------------------------------------------------------
    # Stage building (intent → stages)
    # ---------------------------------------------------------------------
    async def _build_stages(self, session: ConversationSession, intent: Dict[str, Any]) -> None:
        intent_type = intent.get("type", "general")
        if intent_type == "birthday_party":
            await self._build_birthday_party_stages(session, intent)
        elif intent_type == "travel_planning":
            self._build_travel_planning_stages(session, intent)
        elif intent_type == "meeting_scheduling":
            await self._build_meeting_stages(session, intent)
        else:
            await self._build_default_stages(session, intent)

    # ---------------------------------------------------------------------
    # Example stage builders
    # ---------------------------------------------------------------------
    async def _build_birthday_party_stages(self, session: ConversationSession, intent: Dict[str, Any]) -> None:
        entities = intent.get("entities", {})
        user_input = intent.get("original_input", "")
        if "destination" not in entities:
            from .self_healing_ai import get_ai_manager
            ai_manager = get_ai_manager()
            try:
                destinations = await ai_manager.generate_destinations(user_input)
            except Exception as e:
                print(f"[CONV_MANAGER] AI generation failed: {e}")
                destinations = [
                    {"id": "goa", "name": "Goa", "description": "Beach paradise"},
                    {"id": "manali", "name": "Manali", "description": "Mountain retreat"},
                ]
            session.add_stage(
                ConversationStage(
                    "destination_selection",
                    {
                        "question": "Where would you like to celebrate your birthday?",
                        "options": destinations,
                        "type": "single_choice",
                        "user_input": user_input,
                    },
                )
            )
        
        session.add_stage(ConversationStage(
            "accommodation_selection",
            {
                "question": "Choose your accommodation:",
                "options_template": "resorts_and_hotels",
                "type": "single_choice"
            }
        ))
        
        session.add_stage(ConversationStage(
            "activities_selection",
            {
                "question": "What activities would you like to include?",
                "options_template": "activities",
                "type": "multiple_choice"
            }
        ))
        
        session.add_stage(ConversationStage(
            "dining_selection",
            {
                "question": "Any special dining arrangements?",
                "options": [
                    {"id": "cake_bakery", "name": "Order birthday cake from local bakery"},
                    {"id": "restaurant_booking", "name": "Book table at fine dining restaurant"},
                    {"id": "private_chef", "name": "Hire private chef"}
                ],
                "type": "multiple_choice"
            }
        ))
        
        session.add_stage(ConversationStage("final_confirmation", {"question": "Confirm your birthday celebration plan:", "type": "confirmation"}))

    def _build_travel_planning_stages(self, session: ConversationSession, intent: Dict[str, Any]) -> None:
        entities = intent.get("entities", {})
        if "destination" not in entities:
            session.add_stage(
                ConversationStage(
                    "destination_selection",
                    {
                        "question": "Where would you like to travel?",
                        "options": [
                            {"id": "goa", "name": "Goa", "description": "Beaches and nightlife"},
                            {"id": "kerala", "name": "Kerala", "description": "Backwaters and nature"},
                            {"id": "rajasthan", "name": "Rajasthan", "description": "Forts and palaces"},
                            {"id": "himachal", "name": "Himachal", "description": "Mountains and snow"},
                        ],
                        "type": "single_choice",
                    },
                )
            )
        session.add_stage(ConversationStage("accommodation_selection", {"question": "Select your hotel:", "type": "single_choice"}))
        session.add_stage(ConversationStage("activities_selection", {"question": "Select activities:", "type": "multiple_choice"}))
        session.add_stage(ConversationStage("final_confirmation", {"question": "Confirm travel plan:", "type": "confirmation"}))

    async def _build_meeting_stages(self, session: ConversationSession, intent: Dict[str, Any]) -> None:
        user_input = intent.get("original_input", "").lower()
        entities = intent.get("entities", {})
        
        # 1. Detect Platform (be specific to avoid false matches)
        platform = entities.get("platform")
        if not platform:
            if "zoom" in user_input:
                platform = "zoom"
            elif "google meet" in user_input or "gmeet" in user_input:
                platform = "google_meet"
            elif "jitsi" in user_input:
                platform = "jitsi"
            elif "phone" in user_input or "call" in user_input:
                platform = "phone"
            elif "person" in user_input or "in-person" in user_input:
                platform = "in_person"
        
        if platform:
            session.context["platform"] = platform

        # 2. Check for instant meeting intent
        is_instant = (
            ("create" in user_input and "meeting" in user_input) or
            ("start" in user_input and "meeting" in user_input) or
            ("schedule" in user_input and "now" in user_input)
        )
        
        if is_instant:
            if not session.context.get("platform"):
                 session.context["platform"] = "zoom"
            
            session.add_stage(
                ConversationStage(
                    "instant_execution",
                    {
                        "question": "Creating your meeting now...",
                        "type": "execution",
                        "action": "create_instant_meeting"
                    }
                )
            )
        else:
            # Normal flow
            if not platform:
                # Use AI to generate options based on context
                from .self_healing_ai import get_ai_manager
                ai_manager = get_ai_manager()
                
                # Default options as fallback
                options = [
                    {"id": "zoom", "name": "Zoom Meeting"},
                    {"id": "google_meet", "name": "Google Meet"},
                    {"id": "phone", "name": "Phone Call"},
                    {"id": "in_person", "name": "In Person"},
                ]
                
                try:
                    # Ask AI to prioritize/customize options
                    ai_options = await ai_manager.generate_dynamic_response(
                        context=user_input,
                        data_type="meeting_options",
                        schema_description="""Return JSON array of 4 options:
[
  {"id": "zoom" or "google_meet" or "phone" or "in_person", "name": "Display Name (e.g. Zoom Video)", "description": "Why this fits"}
]
Prioritize based on user input (e.g. if 'remote', prioritize Zoom)."""
                    )
                    if ai_options and isinstance(ai_options, list) and len(ai_options) > 0:
                        options = ai_options
                except Exception as e:
                    print(f"AI generation failed, using defaults: {e}")

                session.add_stage(
                    ConversationStage(
                        "platform_selection",
                        {
                            "question": "How would you like to meet?",
                            "options": options,
                            "type": "single_choice",
                        },
                    )
                )
            
            session.add_stage(
                ConversationStage(
                    "participant_details",
                    {"question": "Who are you meeting with? Provide emails or phone numbers or telegram ID's.", "type": "text_input"},
                )
            )
            session.add_stage(
                ConversationStage(
                    "final_confirmation",
                    {
                        "question": "Confirm meeting details:",
                        "type": "confirmation",
                        "actions": ["schedule_zoom", "send_telegram", "add_calendar"],
                    },
                )
            )


    async def _build_default_stages(self, session: ConversationSession, intent: Dict[str, Any]) -> None:
        """Build stages for general/unknown intents using AI to determine the best course of action."""
        user_input = intent.get("original_input", "")
        
        from .self_healing_ai import get_ai_manager
        ai_manager = get_ai_manager()
        
        try:
            # Ask AI what to do
            # It should return a stage definition
            ai_response = await ai_manager.generate_dynamic_response(
                context=user_input,
                data_type="conversation_stage",
                schema_description="""Analyze the user request and generate the next conversation stage.
Return JSON object:
{
  "stage_name": "unique_stage_name",
  "question": "The question to ask the user or the response to give",
  "type": "text_input" or "single_choice" or "multiple_choice" or "confirmation",
  "options": [ {"id": "opt1", "name": "Option 1"} ] (optional, for choice types),
  "actions": ["action_name"] (optional, for confirmation type)
}
If the request is simple (e.g. "Hello"), just ask how to help.
If it's a specific task not covered by other flows, try to structure it."""
            )
            
            if isinstance(ai_response, list):
                if len(ai_response) > 0:
                    stage_data = ai_response[0]
                else:
                    raise Exception("Empty AI response")
            else:
                stage_data = ai_response

            # Validate and sanitize
            stage_name = stage_data.get("stage_name", "general_response")
            question = stage_data.get("question", "How can I help you with that?")
            stage_type = stage_data.get("type", "text_input")
            
            # Construct stage data
            data = {
                "question": question,
                "type": stage_type
            }
            if "options" in stage_data:
                data["options"] = stage_data["options"]
            if "actions" in stage_data:
                data["actions"] = stage_data["actions"]
                
            session.add_stage(ConversationStage(stage_name, data))
            
            # IMPORTANT: Add a final confirmation stage so the conversation can complete
            # This ensures that after the user provides the requested information,
            # the system will ask for confirmation and then execute the action
            if stage_type != "confirmation":
                session.add_stage(
                    ConversationStage(
                        "final_confirmation",
                        {
                            "question": "Confirm action:",
                            "type": "confirmation",
                            "actions": ["execute_task"]
                        }
                    )
                )
            
        except Exception as e:
            print(f"[CONV_MANAGER] AI default stage generation failed: {e}")
            # Fallback
            session.add_stage(ConversationStage("final_confirmation", {"question": f"I understood: '{user_input}'. Confirm action:", "type": "confirmation"}))

    # ---------------------------------------------------------------------
    # Processing Logic
    # ---------------------------------------------------------------------
    async def process_user_response(self, session_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process user response to current stage"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        current_stage = session.get_current_stage()
        if not current_stage:
            return {"error": "No active stage"}
        
        # Process response based on stage type
        result = {"error": "Unknown stage type"}
        
        if current_stage.stage_type == "clarification":
            result = await self._process_destination_selection(session, response)
        elif current_stage.stage_type == "destination_selection":
            result = await self._process_destination_selection(session, response)
        elif current_stage.stage_type == "accommodation_selection":
            result = await self._process_accommodation_selection(session, response)
        elif current_stage.stage_type == "activities_selection":
            result = await self._process_activities_selection(session, response)
        elif current_stage.stage_type == "dining_selection":
            result = self._process_dining_selection(session, response)
        elif current_stage.stage_type == "platform_selection":
            result = self._process_platform_selection(session, response)
        elif current_stage.stage_type == "participant_details":
            result = self._process_participant_details(session, response)
        elif current_stage.stage_type == "final_confirmation":
            result = self._process_final_confirmation(session, response)
        elif current_stage.stage_type == "execution":
             # Immediate execution for instant meetings
             # We'll generate a plan with just the meeting creation action
             # The agent.py will see "ready_for_execution" and execute it
             plan = {
                 "actions": [
                     {
                         "id": 1,
                         "type": "create_instant_meeting",
                         "description": "Create instant meeting",
                         "plugin": "browser_meeting", # Use browser plugin for instant redirect
                         "parameters": {
                             "platform": "zoom", # Default to zoom
                             "topic": "Instant Meeting"
                         }
                     }
                 ]
             }
             return {
                 "status": "ready_for_execution",
                 "plan": plan
             }
        
        # Save session after processing
        if "error" not in result:
            self.save_session(session)
            
        return result
    
    async def _process_destination_selection(self, session: ConversationSession, response: Dict[str, Any]) -> Dict[str, Any]:
        selected_destination = response.get("selection")
        session.complete_current_stage({"destination": selected_destination})
        
        # Populate next stage with destination-specific options
        next_stage = session.get_current_stage()
        if next_stage and next_stage.stage_type == "accommodation_selection":
            next_stage.data["options"] = await self._get_accommodations(selected_destination)
        
        return {
            "status": "stage_completed",
            "next_stage": next_stage.data if next_stage else None
        }
    
    async def _process_accommodation_selection(self, session: ConversationSession, response: Dict[str, Any]) -> Dict[str, Any]:
        selected_accommodation = response.get("selection")
        session.complete_current_stage({"accommodation": selected_accommodation})
        
        # Populate next stage
        next_stage = session.get_current_stage()
        if next_stage and next_stage.stage_type == "activities_selection":
            destination = session.context.get("destination")
            next_stage.data["options"] = await self._get_activities(destination)
            
        return {
            "status": "stage_completed",
            "next_stage": next_stage.data if next_stage else None
        }

    async def _process_activities_selection(self, session: ConversationSession, response: Dict[str, Any]) -> Dict[str, Any]:
        selected_activities = response.get("selections", [])
        session.complete_current_stage({"activities": selected_activities})
        
        next_stage = session.get_current_stage()
        return {
            "status": "stage_completed",
            "next_stage": next_stage.data if next_stage else None
        }

    def _process_dining_selection(self, session: ConversationSession, response: Dict[str, Any]) -> Dict[str, Any]:
        selected_dining = response.get("selections", [])
        session.complete_current_stage({"dining": selected_dining})
        
        next_stage = session.get_current_stage()
        return {
            "status": "stage_completed",
            "next_stage": next_stage.data if next_stage else None
        }

    def _process_platform_selection(self, session: ConversationSession, response: Dict[str, Any]) -> Dict[str, Any]:
        selected_platform = response.get("selection")
        session.complete_current_stage({"platform": selected_platform})
        
        next_stage = session.get_current_stage()
        return {
            "status": "stage_completed",
            "next_stage": next_stage.data if next_stage else None
        }

    def _process_participant_details(self, session: ConversationSession, response: Dict[str, Any]) -> Dict[str, Any]:
        participants = response.get("text_input")
        session.complete_current_stage({"participants": participants})
        
        next_stage = session.get_current_stage()
        return {
            "status": "stage_completed",
            "next_stage": next_stage.data if next_stage else None
        }

    def _process_final_confirmation(self, session: ConversationSession, response: Dict[str, Any]) -> Dict[str, Any]:
        # Generate execution plan
        plan = self.generate_execution_plan(session)
        return {
            "status": "ready_for_execution",
            "plan": plan
        }

    # ---------------------------------------------------------------------
    # AI Helpers
    # ---------------------------------------------------------------------
    async def _get_accommodations(self, destination: str) -> List[Dict[str, Any]]:
        from .self_healing_ai import get_ai_manager
        ai_manager = get_ai_manager()
        try:
            return await ai_manager.generate_accommodations(destination)
        except Exception:
            return [
                {"id": "resort_1", "name": f"Grand {destination} Resort", "description": "Luxury stay"},
                {"id": "hotel_1", "name": f"{destination} City Hotel", "description": "Central location"}
            ]

    async def _get_activities(self, destination: str) -> List[Dict[str, Any]]:
        from .self_healing_ai import get_ai_manager
        ai_manager = get_ai_manager()
        try:
            return await ai_manager.generate_activities(destination)
        except Exception:
            return [
                {"id": "sightseeing", "name": "City Sightseeing", "description": "Tour of main attractions"},
                {"id": "food_tour", "name": "Local Food Tour", "description": "Taste local delicacies"}
            ]

    # ---------------------------------------------------------------------
    # Plan Generation
    # ---------------------------------------------------------------------
    def generate_execution_plan(self, session: ConversationSession) -> Dict[str, Any]:
        """Generate final execution plan from session context"""
        context = session.context
        destination = context.get("destination", "")
        accommodation = context.get("accommodation", {})
        activities = context.get("activities", [])
        platform = context.get("platform")
        participants = context.get("participants")
        
        self.log_debug(f"Generating plan. Context: {context}")
        
        actions = []
        
        # Handle Meeting Flow
        if platform:
            if platform == "zoom":
                actions.append({
                    "id": 1,
                    "type": "schedule_zoom",
                    "description": f"Schedule Zoom meeting with {participants}",
                    "plugin": "zoom",
                    "parameters": {
                        "participants": participants,
                        "topic": "Meeting",
                        "duration": "30 mins"
                    }
                })
            elif platform == "google_meet":
                 actions.append({
                    "id": 1,
                    "type": "schedule_meet",
                    "description": f"Schedule Google Meet with {participants}",
                    "plugin": "calendar",
                    "parameters": {
                        "participants": participants,
                        "platform": "google_meet"
                    }
                })
            
            # Add Telegram message action
            actions.append({
                "id": 2,
                "type": "send_message",
                "description": f"Send Telegram message to {participants}",
                "plugin": "telegram",
                "parameters": {
                    "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
                    "message": f"Meeting invitation! Join link: {{meeting_link}}"
                }
            })
            
            return {
                "platform": platform,
                "participants": participants,
                "actions": actions
            }

        # Handle Birthday/Travel Flow
        if accommodation:
            acc_name = accommodation.get('name', 'resort') if isinstance(accommodation, dict) else str(accommodation)
            actions.append({
                "id": 1,
                "type": "call_resort",
                "description": f"Call {acc_name} for reservation",
                "plugin": "phone_call",
                "parameters": {
                    "contact": acc_name,
                    "purpose": "reservation"
                }
            })
            
        if activities:
            actions.append({
                "id": 2,
                "type": "book_activities",
                "description": f"Book activities: {', '.join([a.get('name', a) if isinstance(a, dict) else a for a in activities])}",
                "plugin": "booking",
                "parameters": {
                    "items": activities
                }
            })
        
        # If no actions were generated, use AI to create a plan
        if not actions:
            from .self_healing_ai import get_ai_manager
            import asyncio
            ai_manager = get_ai_manager()
            
            try:
                # Get the original user input and all collected context
                original_input = session.initial_intent.get("original_input", "")
                
                # Create a summary of the conversation
                conversation_summary = f"User request: {original_input}\n"
                conversation_summary += f"Collected information: {context}"
                
                # Ask AI to generate an execution plan
                ai_plan = asyncio.run(ai_manager.generate_dynamic_response(
                    context=conversation_summary,
                    data_type="execution_plan",
                    schema_description="""Generate an execution plan based on the user's request and collected information.
Return JSON object:
{
  "actions": [
    {
      "id": 1,
      "type": "action_type",
      "description": "Human-readable description of what this action does",
      "plugin": "plugin_name",
      "parameters": {"key": "value"}
    }
  ]
}

Common action types and plugins:
- schedule_zoom / schedule_meet: plugin "zoom" or "calendar"
- send_message: plugin "telegram" or "email"
- call_contact: plugin "phone_call"
- book_reservation: plugin "booking"
- search_information: plugin "search"

Be specific and actionable."""
                ))
                
                if isinstance(ai_plan, dict) and "actions" in ai_plan:
                    actions = ai_plan["actions"]
                    
            except Exception as e:
                print(f"[CONV_MANAGER] AI plan generation failed: {e}")
                # Create a generic action as fallback
                actions = [{
                    "id": 1,
                    "type": "execute_task",
                    "description": f"Execute: {session.initial_intent.get('original_input', 'task')}",
                    "plugin": "general",
                    "parameters": context
                }]
            
        return {
            "destination": destination,
            "actions": actions
        }

def get_conversation_manager() -> MultiStageConversationManager:
    return MultiStageConversationManager()
