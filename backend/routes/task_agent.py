"""
NEW Task-Based Agent Flow
Uses AI to match user input to tasks, then collects required info
"""
import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from ..core.ai_task_matcher import get_task_matcher
from ..core.task_registry import get_task_registry
from ..core.plugins import PluginManager
from ..core.confirmation_manager import get_confirmation_manager, PendingAction

router = APIRouter()

def _detect_communication_method(text: str) -> str:
    """Detect communication method from text (email, telegram, etc.)"""
    text_lower = text.lower()
    
    # Email patterns
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    if re.search(email_pattern, text):
        return "email"
    if any(word in text_lower for word in ["email", "mail", "e-mail", "gmail", "outlook", "yahoo"]):
        return "email"
    
    # Telegram patterns
    if "telegram" in text_lower or " tg " in text_lower:
        return "telegram"
    
    # WhatsApp patterns
    if "whatsapp" in text_lower or "wa " in text_lower:
        return "whatsapp"
    
    # SMS patterns
    if "sms" in text_lower or "text message" in text_lower:
        return "sms"
    
    # Default to telegram for backward compatibility
    return "telegram"

class AgentRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    response: str
    task_info: Optional[Dict[str, Any]] = None
    requires_input: bool = False
    requires_confirmation: bool = False
    session_id: Optional[str] = None
    pending_actions: Optional[List[Dict[str, Any]]] = None
    execution_results: Optional[List[Dict[str, Any]]] = None

# In-memory session storage (replace with Redis/DB in production)
sessions = {}

@router.post("/process_v2", response_model=AgentResponse)
async def process_task_based(request: AgentRequest):
    """
    New task-based processing:
    1. AI matches user input to a task
    2. Collect missing information
    3. Execute when we have everything
    """
    task_matcher = get_task_matcher()
    task_registry = get_task_registry()
    
    # Get or create session
    if request.session_id and request.session_id in sessions:
        session = sessions[request.session_id]
    else:
        session = {
            "session_id": f"task_{len(sessions)}",
            "task_id": None,
            "collected_info": {},
            "original_input": request.message
        }
        sessions[session["session_id"]] = session
    
    session_id = session["session_id"]
    
    # If we don't have a task yet, match it
    if not session["task_id"]:
        match_result = await task_matcher.match_task(request.message)
        
        session["task_id"] = match_result["task_id"]
        session["collected_info"].update(match_result.get("extracted_info", {}))
        
        # If it's a general query (no specific task), just respond
        if match_result["task_id"] == "general":
            return AgentResponse(
                response="I can help you with: scheduling meetings, booking restaurants, planning trips, organizing birthday parties, sending messages, or searching for information. What would you like to do?",
                task_info={"available_tasks": task_registry.get_all_tasks()},
                requires_input=False,
                session_id=session_id
            )
    
    # If this is a follow-up message, extract info from it
    if request.session_id:
        # Use AI to extract info from the user's response
        task = task_registry.get_task(session["task_id"])
        if task:
            # Ask AI to extract relevant info
            from ..core.self_healing_ai import get_ai_manager
            ai_manager = get_ai_manager()
            
            try:
                extraction_prompt = f"""User said: "{request.message}"
Task: {task.description}
Required info: {', '.join(task.required_info)}

Extract any relevant information from the user's message.
Return JSON with keys matching the required info fields.
Only include fields that are mentioned."""

                extracted = await ai_manager.generate_dynamic_response(
                    context=request.message,
                    data_type="info_extraction",
                    schema_description=extraction_prompt
                )
                
                if isinstance(extracted, dict):
                    session["collected_info"].update(extracted)
            except Exception as e:
                print(f"[TASK_AGENT] Info extraction error: {e}")
    
    # Check if we have all required info
    task = task_registry.get_task(session["task_id"])
    if not task:
        return AgentResponse(
            response="Sorry, I couldn't understand that task.",
            session_id=session_id
        )
    
    # Get next missing info
    next_question = await task_matcher.get_missing_info(
        session["task_id"],
        session["collected_info"]
    )
    
    if next_question:
        # Still need more info
        return AgentResponse(
            response=next_question,
            task_info={
                "task": task.to_dict(),
                "collected": session["collected_info"]
            },
            requires_input=True,
            session_id=session_id
        )
    
    # We have everything! Generate execution plan
    plan = await generate_execution_plan(task, session["collected_info"])
    
    # Store in confirmation manager
    confirmation_manager = get_confirmation_manager()
    pending_actions = []
    for action in plan["actions"]:
        pending_action = PendingAction(
            action_type=action["type"],
            description=action["description"],
            parameters=action["parameters"],
            plugin=action["plugin"]
        )
        pending_actions.append(pending_action)
    
    confirmation_manager.pending_actions[session_id] = pending_actions
    confirmation_manager.session_plans[session_id] = {
        "plan": plan,
        "task": task.to_dict(),
        "info": session["collected_info"]
    }
    
    # Return confirmation request
    confirmation_msg = f"Ready to {task.description}:\n"
    for action in plan["actions"]:
        confirmation_msg += f"• {action['description']}\n"
    confirmation_msg += "\nConfirm?"
    
    return AgentResponse(
        response=confirmation_msg,
        task_info={
            "task": task.to_dict(),
            "collected": session["collected_info"],
            "plan": plan
        },
        requires_confirmation=True,
        session_id=session_id,
        pending_actions=[a.to_dict() for a in pending_actions]
    )

async def generate_execution_plan(task, collected_info: Dict[str, Any]) -> Dict[str, Any]:
    """Generate execution plan based on task and collected info"""
    from ..core.intelligent_ai import get_ai_manager
    ai_manager = get_ai_manager()
    
    # Smart detection of communication method
    user_input = str(collected_info)
    comm_method = _detect_communication_method(user_input)
    
    # Determine which plugin to use for sending
    if comm_method == "email":
        send_plugin = "gmail"
        send_example = '''{{
      "type": "send_email",
      "description": "Send email to recipient",
      "plugin": "gmail",
      "parameters": {{"to": "email@example.com", "subject": "Meeting Invitation", "body": "Join here: {{meeting_link}}"}}
    }}'''
    else:
        send_plugin = "telegram"
        send_example = '''{{
      "type": "send_message",
      "description": "Send link via Telegram",
      "plugin": "telegram",
      "parameters": {{"message": "Join here: {{meeting_link}}"}}
    }}'''
    
    prompt = f"""Task: {task.description}
Available plugins: {', '.join(task.plugins)}
User provided: {collected_info}
Detected communication method: {comm_method}

Generate an execution plan with specific actions.
IMPORTANT:
- If user did NOT specify a platform (Zoom/Google Meet), use 'Jitsi' (plugin: browser_meeting) for instant working links.
- Use {send_plugin} for sending since user mentioned {comm_method}.
- Include {{meeting_link}} placeholder where the meeting link should go.

Return JSON:
{{
  "actions": [
    {{
      "type": "schedule_meeting",
      "description": "Create instant Jitsi meeting",
      "plugin": "browser_meeting",
      "parameters": {{"platform": "jitsi", "topic": "Meeting"}}
    }},
    {send_example}
  ]
}}"""

    try:
        plan = await ai_manager.generate_dynamic_response(
            context=str(collected_info),
            data_type="execution_plan",
            schema_description=prompt
        )
        
        if isinstance(plan, dict) and "actions" in plan:
            return plan
    except Exception as e:
        print(f"[TASK_AGENT] Plan generation error: {e}")
    
    # Fallback plan
    return {
        "actions": [{
            "type": "execute_task",
            "description": f"Execute: {task.description}",
            "plugin": "general",
            "parameters": collected_info
        }]
    }

@router.post("/confirm_v2")
async def confirm_task(session_id: str, approved: bool):
    """Execute confirmed task"""
    confirmation_manager = get_confirmation_manager()
    
    if session_id not in confirmation_manager.pending_actions:
        return {"status": "error", "message": "No pending actions"}
    
    if not approved:
        del confirmation_manager.pending_actions[session_id]
        del sessions[session_id]
        return {"status": "cancelled", "message": "Task cancelled"}
    
    # Execute actions
    plugin_manager = PluginManager()
    results = []
    current_state = {}  # Store state between steps
    
    for action in confirmation_manager.pending_actions[session_id]:
        plugin = plugin_manager.get_plugin(action.plugin)
        if plugin:
            step = {"action": action.action_type, "parameters": action.parameters}
            
            # Execute with current state
            result = await plugin.execute(step, current_state)
            results.append(result)
            
            # Update state with output from this step
            if result.get("output"):
                current_state.update(result["output"])
    
    # Clean up
    del confirmation_manager.pending_actions[session_id]
    if session_id in sessions:
        del sessions[session_id]
    
    return {
        "status": "completed",
        "message": "Task executed successfully!",
        "results": results
    }
